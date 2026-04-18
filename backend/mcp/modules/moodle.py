"""Moodle tools — browser-automated access (requires TUM SSO auth)."""

import logging

from mcp.server.fastmcp import FastMCP

import auth
import mock

logger = logging.getLogger(__name__)

MOODLE_BASE = "https://www.moodle.tum.de"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def moodle_list_courses(username: str) -> dict:
        """List the user's enrolled Moodle courses. Requires prior tum_login."""
        if mock.is_demo_mode():
            m = mock.get_mock("moodle", "moodle_list_courses", username=username)
            if m is not None:
                return m
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
        if mock.is_demo_mode():
            m = mock.get_mock("moodle", "moodle_list_assignments", username=username)
            if m is not None:
                return m
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
    async def moodle_get_course_content(username: str, course_url: str) -> dict:
        """List sections, resources (PDFs/slides) and activities inside a Moodle course.

        course_url: full URL of a Moodle course (as returned by moodle_list_courses).
        Returns one entry per section with the resource title, type, and direct URL.
        Pair with moodle_fetch_resource_text to summarize lecture slides.
        Requires prior tum_login.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("moodle", "moodle_get_course_content", course_url=course_url)
            if m is not None:
                return m
        if not course_url.startswith(MOODLE_BASE):
            return {"error": f"course_url must start with {MOODLE_BASE}"}
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(course_url, wait_until="networkidle", timeout=30_000)
            sections = await page.eval_on_selector_all(
                "li.section, .course-section, .topics > li",
                """secs => secs.map(s => ({
                    name: (s.querySelector('.sectionname, h3, .section-title')?.textContent || '').trim(),
                    items: Array.from(s.querySelectorAll('li.activity, .activity, .activityinstance')).map(a => ({
                        title: (a.querySelector('.instancename, .activity-name, a')?.textContent || '').trim(),
                        type: (a.className.match(/modtype_(\\w+)/)?.[1])
                              || a.querySelector('img.activityicon, .activityicon')?.getAttribute('alt')
                              || '',
                        url: a.querySelector('a')?.href || '',
                    })).filter(it => it.title),
                })).filter(s => s.items.length || s.name)"""
            )
            title = await page.title()
            return {
                "course_title": title,
                "course_url": course_url,
                "sections": sections,
                "section_count": len(sections),
            }
        except Exception as e:
            logger.exception("Moodle get_course_content failed")
            return {"error": str(e), "course_url": course_url}
        finally:
            await ctx.close()

    @mcp.tool()
    async def moodle_fetch_resource_text(username: str, resource_url: str, max_chars: int = 8000) -> dict:
        """Download a Moodle resource (PDF/page/file) and return its text content.

        resource_url: a URL from moodle_get_course_content sections[].items[].url
        For PDFs (mod/resource), follows the redirect to the file and extracts text.
        For mod/page, scrapes the rendered HTML body. Other types: best-effort.
        Requires prior tum_login.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("moodle", "moodle_fetch_resource_text", resource_url=resource_url)
            if m is not None:
                return m
        if not resource_url.startswith(MOODLE_BASE):
            return {"error": f"resource_url must start with {MOODLE_BASE}"}
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            response = await page.goto(resource_url, wait_until="networkidle", timeout=45_000)
            content_type = (response.headers.get("content-type") if response else "") or ""

            if "pdf" in content_type.lower() or resource_url.lower().endswith(".pdf"):
                # Pull the bytes via the authenticated browser context, parse with pypdf if available
                pdf_bytes = await response.body() if response else b""
                if not pdf_bytes:
                    return {"error": "PDF body was empty.", "resource_url": resource_url}
                try:
                    from pypdf import PdfReader  # noqa: WPS433
                    import io
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    text = "\n".join((p.extract_text() or "") for p in reader.pages)
                except Exception as parse_err:
                    return {
                        "error": f"PDF parsing failed: {parse_err}. Install pypdf for text extraction.",
                        "resource_url": resource_url,
                        "byte_length": len(pdf_bytes),
                    }
                return {
                    "kind": "pdf",
                    "resource_url": resource_url,
                    "text": text[:max_chars],
                    "truncated": len(text) > max_chars,
                    "char_count": len(text),
                }

            # HTML page (mod/page, mod/url landing, etc.)
            body = await page.inner_text("#region-main, main, body")
            return {
                "kind": "html",
                "resource_url": resource_url,
                "text": body[:max_chars],
                "truncated": len(body) > max_chars,
                "char_count": len(body),
            }
        except Exception as e:
            logger.exception("Moodle fetch_resource_text failed")
            return {"error": str(e), "resource_url": resource_url}
        finally:
            await ctx.close()

    @mcp.tool()
    async def moodle_list_grades(username: str) -> dict:
        """List grades across all enrolled Moodle courses. Requires prior tum_login."""
        if mock.is_demo_mode():
            m = mock.get_mock("moodle", "moodle_list_grades", username=username)
            if m is not None:
                return m
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
