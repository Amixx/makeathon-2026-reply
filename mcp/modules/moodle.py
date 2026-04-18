"""Moodle tools — browser-automated access (requires TUM SSO auth)."""

import logging

from mcp.server.fastmcp import FastMCP

import auth

logger = logging.getLogger(__name__)

MOODLE_BASE = "https://www.moodle.tum.de"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def moodle_list_courses(username: str) -> dict:
        """List the user's enrolled Moodle courses. Requires prior tum_login."""
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(f"{MOODLE_BASE}/my/", wait_until="networkidle", timeout=30_000)
            courses = await page.eval_on_selector_all(
                ".course-listitem, .coursebox, [data-region='course-content'] .card, .dashboard-card",
                """els => els.map(e => ({
                    name: (e.querySelector('.coursename, .course-title, h3, .multiline')?.textContent || '').trim(),
                    url: e.querySelector('a')?.href || '',
                })).filter(x => x.name)"""
            )
            return {"courses": courses, "count": len(courses)}
        except Exception as e:
            logger.exception("Moodle list_courses failed")
            return {"error": str(e)}
        finally:
            await ctx.close()

    @mcp.tool()
    async def moodle_list_assignments(username: str, days_ahead: int = 30) -> dict:
        """List upcoming Moodle deadlines (assignments, quizzes, etc).

        days_ahead: window in days to look ahead. Requires prior tum_login.
        """
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(
                f"{MOODLE_BASE}/calendar/view.php?view=upcoming",
                wait_until="networkidle",
                timeout=30_000,
            )
            events = await page.eval_on_selector_all(
                ".event, [data-region='event-list-content-event'], .calendarwrapper .event",
                """els => els.map(e => ({
                    title: (e.querySelector('.name, h3, .event-name, [data-region=\"event-list-content-event-action\"]')?.textContent || '').trim(),
                    course: (e.querySelector('.course, .event-course, [data-region=\"event-course\"]')?.textContent || '').trim(),
                    date: (e.querySelector('.date, time, .event-time, [data-region=\"event-list-content-date\"]')?.textContent || '').trim(),
                    datetime: e.querySelector('time')?.getAttribute('datetime') || '',
                    url: e.querySelector('a')?.href || '',
                    type: (e.querySelector('.event_icon, img')?.getAttribute('title') || e.getAttribute('data-event-component') || '').trim(),
                })).filter(x => x.title)"""
            )
            return {
                "assignments": events,
                "count": len(events),
                "window_days": days_ahead,
                "source": f"{MOODLE_BASE}/calendar/view.php?view=upcoming",
            }
        except Exception as e:
            logger.exception("Moodle list_assignments failed")
            return {"error": str(e)}
        finally:
            await ctx.close()

    @mcp.tool()
    async def moodle_list_grades(username: str) -> dict:
        """List grades across all enrolled Moodle courses. Requires prior tum_login."""
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(
                f"{MOODLE_BASE}/grade/report/overview/index.php",
                wait_until="networkidle",
                timeout=30_000,
            )
            rows = await page.eval_on_selector_all(
                "table.overview tr, table.grade-report-overview tr",
                """rs => rs.map(r => ({
                    course: (r.querySelector('td.course, td:nth-child(1) a')?.textContent || '').trim(),
                    grade: (r.querySelector('td.grade, td:nth-child(2)')?.textContent || '').trim(),
                })).filter(x => x.course && x.grade)"""
            )
            return {"grades": rows, "count": len(rows)}
        except Exception as e:
            logger.exception("Moodle list_grades failed")
            return {"error": str(e)}
        finally:
            await ctx.close()
