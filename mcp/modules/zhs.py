"""ZHS sports booking tools — public catalog + auth-gated booking.

ZHS publishes its course catalog at https://www.zhs-muenchen.de/sportarten.
Each sport links to a buchungssystem.zhs-muenchen.de page with bookable slots.
Booking requires TUM SSO (Shibboleth) and runs through a Playwright flow.
"""

import logging
import re

import httpx
from mcp.server.fastmcp import FastMCP

import auth
from config import TUM_ENV

logger = logging.getLogger(__name__)

ZHS_BASE = "https://www.zhs-muenchen.de"
ZHS_BOOKING_BASE = "https://buchung.zhs-muenchen.de"

BOOK_BUTTON_TEXTS = ["Buchen", "buchen", "Book", "book", "Zum Warenkorb", "In den Warenkorb"]
CHECKOUT_BUTTON_TEXTS = ["Weiter zur Buchung", "Weiter", "Checkout", "Buchung abschließen", "Jetzt buchen"]
CONFIRM_BUTTON_TEXTS = ["Verbindlich buchen", "Bestätigen", "Confirm", "Zahlungspflichtig buchen"]


async def _click_first_matching(page, texts: list[str], timeout: int = 5_000) -> bool:
    for text in texts:
        try:
            loc = page.get_by_role("button", name=re.compile(rf"^\s*{re.escape(text)}\s*$", re.I)).first
            await loc.wait_for(state="visible", timeout=timeout)
            await loc.click()
            return True
        except Exception:
            pass
        try:
            loc = page.get_by_text(text, exact=False).first
            await loc.wait_for(state="visible", timeout=timeout)
            await loc.click()
            return True
        except Exception:
            continue
    return False


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def zhs_list_sports(category: str = "") -> dict:
        """List ZHS sport categories from the public catalog.

        category: optional substring filter on sport name.
        """
        url = f"{ZHS_BASE}/sportarten/"
        logger.info("Fetching ZHS sports catalog")
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            # Sports are rendered as <a href="...sportarten/{slug}..."> items
            html = resp.text
            matches = re.findall(
                r'<a[^>]+href="([^"]*sportarten/[^"\s]+)"[^>]*>([^<]{2,80})</a>',
                html,
                flags=re.I,
            )
            sports = []
            seen = set()
            for href, label in matches:
                label = label.strip()
                if not label or href in seen:
                    continue
                seen.add(href)
                sports.append({
                    "name": label,
                    "url": href if href.startswith("http") else f"{ZHS_BASE}{href}",
                })
            if category:
                cat = category.lower()
                sports = [s for s in sports if cat in s["name"].lower()]
            return {"sports": sports, "count": len(sports), "source": url}
        except Exception as e:
            logger.exception("zhs_list_sports failed")
            return {"error": str(e), "source": url}

    @mcp.tool()
    async def zhs_list_slots(sport_url: str) -> dict:
        """List bookable slots for a ZHS sport by its catalog URL.

        sport_url: a URL from zhs_list_sports, typically under zhs-muenchen.de.
        """
        ctx = await auth.get_anonymous_context()
        try:
            page = await ctx.new_page()
            await page.goto(sport_url, wait_until="networkidle", timeout=30_000)
            # Most ZHS pages embed a table of offerings (Kurs, Zeit, Ort, Leitung, Preis, Buchung)
            slots = await page.eval_on_selector_all(
                "table tr, .kurs, .angebot, [class*='kurs']",
                """rows => rows.map(r => {
                    const cells = r.querySelectorAll('td');
                    const link = r.querySelector('a[href*=\"buchung.zhs\"], a.bs_btn, a[href*=\"Buchung\"]');
                    return {
                        course: (cells[0]?.textContent || r.querySelector('.kursname, .name')?.textContent || '').trim(),
                        day_time: (cells[1]?.textContent || r.querySelector('.zeit, .time')?.textContent || '').trim(),
                        location: (cells[2]?.textContent || r.querySelector('.ort, .location')?.textContent || '').trim(),
                        instructor: (cells[3]?.textContent || '').trim(),
                        price: (cells[4]?.textContent || r.querySelector('.preis, .price')?.textContent || '').trim(),
                        booking_url: link?.href || '',
                    };
                }).filter(x => x.course && x.booking_url)"""
            )
            return {"slots": slots, "count": len(slots), "source": sport_url}
        except Exception as e:
            logger.exception("zhs_list_slots failed")
            return {"error": str(e), "source": sport_url}
        finally:
            await ctx.close()

    @mcp.tool()
    async def zhs_book_slot(
        username: str,
        booking_url: str,
        confirm: bool = False,
    ) -> dict:
        """Book a ZHS sports slot. Requires prior tum_login.

        booking_url: a booking URL from zhs_list_slots (usually buchung.zhs-muenchen.de).
        confirm: must be True to actually submit. Without it, the flow stops at
                 the final confirmation screen and reports what was found.
        """
        if TUM_ENV == "prod" and confirm:
            logger.warning("ZHS booking in prod with confirm=True for user=%s", username)

        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(booking_url, wait_until="networkidle", timeout=30_000)

            # Step 1 — add to cart / start booking
            if not await _click_first_matching(page, BOOK_BUTTON_TEXTS, timeout=8_000):
                return {
                    "error": "Could not find a 'Buchen' / Book button on the slot page.",
                    "url": page.url,
                }
            await page.wait_for_load_state("networkidle", timeout=15_000)

            # Step 2 — proceed to checkout (may go through SSO if not already authed)
            await _click_first_matching(page, CHECKOUT_BUTTON_TEXTS, timeout=8_000)
            await page.wait_for_load_state("networkidle", timeout=20_000)

            # If redirected into Shibboleth, the storageState cookies should carry us through.
            # Give the redirect a moment to settle.
            if "login.tum.de" in page.url or "idp" in page.url.lower():
                await page.wait_for_load_state("networkidle", timeout=20_000)

            summary_excerpt = (await page.inner_text("body"))[:800]

            if not confirm:
                return {
                    "status": "staged",
                    "message": "Reached booking confirmation page. Re-run with confirm=True to finalize.",
                    "url": page.url,
                    "page_excerpt": summary_excerpt,
                }

            if not await _click_first_matching(page, CONFIRM_BUTTON_TEXTS, timeout=8_000):
                return {
                    "error": "Could not find a final-confirmation button.",
                    "url": page.url,
                    "page_excerpt": summary_excerpt,
                }
            await page.wait_for_load_state("networkidle", timeout=20_000)

            return {
                "status": "submitted",
                "url": page.url,
                "page_excerpt": (await page.inner_text("body"))[:800],
            }
        except Exception as e:
            logger.exception("zhs_book_slot failed")
            return {"error": str(e), "url": booking_url}
        finally:
            await ctx.close()
