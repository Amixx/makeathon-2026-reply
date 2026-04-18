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
import mock
from config import TUM_ENV

logger = logging.getLogger(__name__)

ZHS_BASE = "https://www.zhs-muenchen.de"
ZHS_KURSE_BASE = "https://kurse.zhs-muenchen.de"
ZHS_BOOKING_BASE = "https://buchung.zhs-muenchen.de"

BOOK_BUTTON_TEXTS = ["Buchen", "buchen", "Book", "book", "Zum Warenkorb", "In den Warenkorb"]
CHECKOUT_BUTTON_TEXTS = ["Weiter zur Buchung", "Weiter", "Checkout", "Buchung abschließen", "Jetzt buchen"]
CONFIRM_BUTTON_TEXTS = ["Verbindlich buchen", "Bestätigen", "Confirm", "Zahlungspflichtig buchen"]



def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def zhs_list_sports(category: str = "") -> dict:
        """List ZHS sport categories from the public catalog.

        category: optional substring filter on sport name.
        """
        if mock.is_demo_mode():
            m = await mock.get_mock("zhs", "zhs_list_sports", category=category)
            if m is not None:
                return m
        url = f"{ZHS_KURSE_BASE}/de/muenchen"
        logger.info("Fetching ZHS sports catalog from %s", url)
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            html = resp.text
            seen: set[str] = set()
            sports: list[dict] = []
            for m_link in re.finditer(r'<a\s[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
                href, inner = m_link.group(1), m_link.group(2)
                name = re.sub(r"<[^>]+>", "", inner).strip().split("\n")[0].strip()
                if not name or len(name) < 2 or len(name) > 80 or name in seen:
                    continue
                if not href:
                    continue
                if not href.startswith("http"):
                    href = f"{ZHS_KURSE_BASE}{href}" if href.startswith("/") else f"{ZHS_KURSE_BASE}/{href}"
                seen.add(name)
                sports.append({"name": name, "url": href})
            if category:
                cat = category.lower()
                sports = [s for s in sports if cat in s["name"].lower()]
            if not sports:
                return {
                    "sports": [],
                    "count": 0,
                    "source": url,
                    "note": "No sports found — the page may require JS rendering. Try zhs_list_slots with a known sport URL instead.",
                }
            return {"sports": sports, "count": len(sports), "source": url}
        except Exception as e:
            logger.exception("zhs_list_sports failed")
            return {"error": str(e), "source": url}

    @mcp.tool()
    async def zhs_list_slots(sport_url: str) -> dict:
        """List bookable slots for a ZHS sport by its catalog URL.

        sport_url: a URL from zhs_list_sports, typically under zhs-muenchen.de.
        """
        if mock.is_demo_mode():
            m = await mock.get_mock("zhs", "zhs_list_slots", sport_url=sport_url)
            if m is not None:
                return m
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(sport_url)
                resp.raise_for_status()
            html = resp.text
            slots: list[dict] = []
            for row_m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL):
                row_html = row_m.group(1)
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
                link_m = re.search(r'<a[^>]*href="([^"]*buchung\.zhs[^"]*|[^"]*Buchung[^"]*)"', row_html, re.I)
                if len(cells) < 3 or not link_m:
                    continue
                strip_tags = lambda s: re.sub(r"<[^>]+>", "", s).strip()
                booking_url = link_m.group(1)
                if not booking_url.startswith("http"):
                    booking_url = f"{ZHS_BOOKING_BASE}{booking_url}" if booking_url.startswith("/") else f"{ZHS_BOOKING_BASE}/{booking_url}"
                slots.append({
                    "course": strip_tags(cells[0]),
                    "day_time": strip_tags(cells[1]) if len(cells) > 1 else "",
                    "location": strip_tags(cells[2]) if len(cells) > 2 else "",
                    "instructor": strip_tags(cells[3]) if len(cells) > 3 else "",
                    "price": strip_tags(cells[4]) if len(cells) > 4 else "",
                    "booking_url": booking_url,
                })
            if not slots:
                return {
                    "slots": [],
                    "count": 0,
                    "source": sport_url,
                    "note": "No slots found — the page may require JS rendering or have a different layout.",
                }
            return {"slots": slots, "count": len(slots), "source": sport_url}
        except Exception as e:
            logger.exception("zhs_list_slots failed")
            return {"error": str(e), "source": sport_url}

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
        if mock.is_demo_mode():
            m = await mock.get_mock("zhs", "zhs_book_slot", confirm=confirm)
            if m is not None:
                return m
        if TUM_ENV == "prod" and confirm:
            logger.warning("ZHS booking in prod with confirm=True for user=%s", username)

        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(booking_url, wait_until="networkidle", timeout=30_000)

            # Step 1 — add to cart / start booking
            if not await auth.click_first_matching(page, BOOK_BUTTON_TEXTS, timeout=8_000):
                return {
                    "error": "Could not find a 'Buchen' / Book button on the slot page.",
                    "url": page.url,
                }
            await page.wait_for_load_state("networkidle", timeout=15_000)

            # Step 2 — proceed to checkout (may go through SSO if not already authed)
            await auth.click_first_matching(page, CHECKOUT_BUTTON_TEXTS, timeout=8_000)
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

            if not await auth.click_first_matching(page, CONFIRM_BUTTON_TEXTS, timeout=8_000):
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
