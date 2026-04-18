"""TUM Career Center — job postings and career events.

Scrapes the public community.tum.de career pages via a headless browser,
since the content is rendered client-side and there is no public API.
"""

import logging

from mcp.server.fastmcp import FastMCP

import auth

logger = logging.getLogger(__name__)

CAREER_BASE = "https://www.community.tum.de"
JOBS_URL = f"{CAREER_BASE}/en/career/job-board/"
EVENTS_URL = f"{CAREER_BASE}/en/career/career-events/"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def career_list_jobs(keyword: str = "", limit: int = 20) -> dict:
        """List job/internship postings from the TUM Career Center job board.

        keyword: optional filter matched against title/company (case-insensitive).
        limit: max number of postings to return.
        """
        ctx = await auth.get_anonymous_context()
        try:
            page = await ctx.new_page()
            await page.goto(JOBS_URL, wait_until="networkidle", timeout=30_000)

            # Generic extraction — cover likely card/list renderings
            jobs = await page.eval_on_selector_all(
                "article, .job, .job-posting, .card, li.posting, [class*='job']",
                """els => els.map(e => ({
                    title: (e.querySelector('h1,h2,h3,h4,.title,[class*=\"title\"]')?.textContent || '').trim(),
                    company: (e.querySelector('.company,[class*=\"company\"],[class*=\"employer\"]')?.textContent || '').trim(),
                    location: (e.querySelector('.location,[class*=\"location\"]')?.textContent || '').trim(),
                    type: (e.querySelector('.type,.employment-type,[class*=\"type\"]')?.textContent || '').trim(),
                    url: e.querySelector('a')?.href || '',
                })).filter(x => x.title)"""
            )

            if keyword:
                kw = keyword.lower()
                jobs = [
                    j for j in jobs
                    if kw in j.get("title", "").lower() or kw in j.get("company", "").lower()
                ]

            return {"jobs": jobs[:limit], "count": len(jobs[:limit]), "source": JOBS_URL}
        except Exception as e:
            logger.exception("career_list_jobs failed")
            return {"error": str(e), "source": JOBS_URL}
        finally:
            await ctx.close()

    @mcp.tool()
    async def career_list_events(keyword: str = "", limit: int = 20) -> dict:
        """List upcoming TUM Career Center events (career fairs, workshops, talks).

        keyword: optional filter matched against title/description.
        limit: max number of events to return.
        """
        ctx = await auth.get_anonymous_context()
        try:
            page = await ctx.new_page()
            await page.goto(EVENTS_URL, wait_until="networkidle", timeout=30_000)

            events = await page.eval_on_selector_all(
                "article, .event, .card, li.event, [class*='event']",
                """els => els.map(e => ({
                    title: (e.querySelector('h1,h2,h3,h4,.title,[class*=\"title\"]')?.textContent || '').trim(),
                    date: (e.querySelector('time,.date,[class*=\"date\"]')?.textContent || '').trim(),
                    datetime: e.querySelector('time')?.getAttribute('datetime') || '',
                    location: (e.querySelector('.location,[class*=\"location\"],[class*=\"venue\"]')?.textContent || '').trim(),
                    summary: (e.querySelector('p,.summary,.description,[class*=\"description\"]')?.textContent || '').trim().slice(0, 280),
                    url: e.querySelector('a')?.href || '',
                })).filter(x => x.title)"""
            )

            if keyword:
                kw = keyword.lower()
                events = [
                    ev for ev in events
                    if kw in ev.get("title", "").lower() or kw in ev.get("summary", "").lower()
                ]

            return {"events": events[:limit], "count": len(events[:limit]), "source": EVENTS_URL}
        except Exception as e:
            logger.exception("career_list_events failed")
            return {"error": str(e), "source": EVENTS_URL}
        finally:
            await ctx.close()

    @mcp.tool()
    async def career_get_job(url: str) -> dict:
        """Fetch the full details of a single job posting by URL."""
        if not url.startswith(CAREER_BASE):
            return {"error": f"URL must be on {CAREER_BASE}"}
        ctx = await auth.get_anonymous_context()
        try:
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            title = await page.title()
            body = await page.inner_text("main, article, body")
            return {"title": title, "url": url, "content": body[:4_000]}
        except Exception as e:
            logger.exception("career_get_job failed")
            return {"error": str(e), "url": url}
        finally:
            await ctx.close()
