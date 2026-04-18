"""TUMonline tools — public NAT API + authenticated SPA REST API."""

import asyncio
import logging
import re

import httpx
from mcp.server.fastmcp import FastMCP

import auth
from config import NAT_API_BASE, TUM_BASE_URL, TUM_ONLINE_PATH

logger = logging.getLogger(__name__)

REST_BASE = f"{TUM_BASE_URL}{TUM_ONLINE_PATH}/ee/rest"


# Multi-language text matchers, verified against demo.campus.tum.de DSystem 2026-04.
# Course list row → "Go to course registration"
# Registration procedure page → "Enter place request" is the submit CTA
REGISTER_BUTTON_TEXTS = [
    "Go to course registration",
    "Zur Anmeldung",
    "Register for course",
]
SUBMIT_REGISTRATION_TEXTS = [
    "Enter place request",
    "Zum Platz anmelden",
    "Platz anmelden",
    "Register",
    "Anmelden",
]
EXAM_REGISTER_TEXTS = [
    "Register for exam",
    "Zur Prüfungsanmeldung",
    "Anmelden",
]


def _desktop_url(fragment: str) -> str:
    return f"{TUM_BASE_URL}{TUM_ONLINE_PATH}/ee/ui/ca2/app/desktop/#/{fragment.lstrip('/')}"


async def _click_first_matching(page, texts: list[str], timeout: int = 5_000) -> bool:
    """Try clicking the first visible element matching any of the given texts."""
    for text in texts:
        try:
            locator = page.get_by_role("button", name=re.compile(rf"^\s*{re.escape(text)}\s*$", re.I)).first
            await locator.wait_for(state="visible", timeout=timeout)
            await locator.click()
            return True
        except Exception:
            pass
        try:
            locator = page.get_by_text(text, exact=False).first
            await locator.wait_for(state="visible", timeout=timeout)
            await locator.click()
            return True
        except Exception:
            continue
    return False


def _extract_lang(lang_obj: dict | None, prefer: str = "en") -> str:
    """Extract a human-readable string from TUMonline's langdata objects."""
    if not lang_obj:
        return ""
    translations = lang_obj.get("translations", {}).get("translation", [])
    by_lang = {t["lang"]: t.get("value", "") for t in translations if t.get("value")}
    return by_lang.get(prefer) or by_lang.get("de") or by_lang.get("en") or lang_obj.get("value", "")


async def _spa_xhr(page, url: str, token: str) -> dict | list | None:
    """Make an authenticated XHR from the SPA page context (relative to SPA root)."""
    # Convert absolute REST URL to relative from the SPA desktop path
    rest_path = url.replace(REST_BASE, "../../../ee/rest")
    result = await page.evaluate(
        """async ([path, tok]) => {
            return new Promise((resolve) => {
                const xhr = new XMLHttpRequest();
                xhr.open("GET", path);
                xhr.setRequestHeader("Accept", "application/json");
                xhr.setRequestHeader("Accept-Language", "EN");
                xhr.setRequestHeader("Authorization", "Bearer " + tok);
                xhr.onload = () => resolve({ s: xhr.status, b: xhr.responseText });
                xhr.onerror = () => resolve({ s: -1, b: "" });
                xhr.send();
            });
        }""",
        [rest_path, token],
    )
    if result["s"] != 200:
        return None
    import json
    return json.loads(result["b"])


def register(mcp: FastMCP) -> None:
    # ── Public API tools ─────────────────────────────────────────────────────
    @mcp.tool()
    async def tumonline_search_courses(query: str, limit: int = 10) -> dict:
        """Search TUMonline course catalog. Returns matching courses."""
        url = f"{NAT_API_BASE}/course"
        params = {"q": query, "count": limit}
        logger.info("Searching courses: %s", params)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_search_rooms(query: str, limit: int = 10) -> dict:
        """Search for rooms in TUMonline."""
        url = f"{NAT_API_BASE}/rom/list"
        params = {"q": query, "count": limit}
        logger.info("Searching rooms: %s", params)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_get_semester_info() -> dict:
        """Get current semester info including exam periods and registration dates."""
        url = f"{NAT_API_BASE}/semesters/extended"
        logger.info("Fetching semester info")
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            all_semesters = resp.json()
            # Only return current + future semesters
            relevant = [s for s in all_semesters if s.get("is_current") or s.get("semester_period_start", "") >= "2026"]
            return {"semesters": relevant[-4:]}

    @mcp.tool()
    async def tumonline_get_course(course_id: int) -> dict:
        """Get full details for a single course by its TUMonline course_id.
        Returns description, schedule, instructors, exam info, registration links."""
        url = f"{NAT_API_BASE}/course/{course_id}"
        logger.info("Fetching course detail: %s", course_id)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return {"error": f"Course {course_id} not found"}
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_get_module(module_code: str) -> dict:
        """Get module handbook entry by module code (e.g. 'IN0011').
        Returns ECTS credits, description, prerequisites, responsible professor."""
        url = f"{NAT_API_BASE}/mhb/module/{module_code}"
        logger.info("Fetching module: %s", module_code)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return {"error": f"Module '{module_code}' not found"}
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_search_programs(query: str, limit: int = 10) -> dict:
        """Search degree programs (e.g. 'Informatics', 'Mechanical Engineering').
        Returns study_id which can be used to find program-specific module catalogs."""
        url = f"{NAT_API_BASE}/programs/search"
        params = {"q": query, "count": limit}
        logger.info("Searching programs: %s", params)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_list_program_modules(catalog_tag: str, limit: int = 50) -> dict:
        """List modules in a degree program catalog.
        Use tumonline_list_module_catalogs to discover catalog_tags first.
        Example: '163016030_electives_mla' for M.Sc. Informatics ML electives."""
        url = f"{NAT_API_BASE}/mhb/module"
        params = {"catalog_tag": catalog_tag, "count": limit}
        logger.info("Listing program modules: %s", params)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_list_module_catalogs(query: str = "") -> dict:
        """List available module handbook catalogs (degree program course groups).
        Filter by query (e.g. 'Informatics', 'Maschinenwesen').
        Returns catalog_tag values for use with tumonline_list_program_modules."""
        url = f"{NAT_API_BASE}/mhb/catalog"
        logger.info("Listing module catalogs, query=%s", query)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            catalogs = resp.json()
            if query:
                q = query.lower()
                catalogs = [c for c in catalogs if q in (c.get("catalog_title_en") or "").lower()
                            or q in (c.get("catalog_title") or "").lower()]
            return {"catalogs": catalogs}

    # ── Authenticated REST API tools ────────────────────────────────────────
    @mcp.tool()
    async def tumonline_my_courses(username: str, semester_id: int = 206) -> dict:
        """List the user's registered courses for a semester with full details.

        Returns course title, type, SWS, instructors, and registration info.
        Requires prior tum_login. semester_id defaults to current (206 = Summer 2026).
        """
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            # Navigate to SPA to get auth context + access token
            await page.goto(
                _desktop_url("slc.tm.cp/student/courses"),
                wait_until="networkidle",
                timeout=30_000,
            )
            await page.wait_for_timeout(3000)

            ls_key = f"{TUM_ONLINE_PATH.lstrip('/')}_co.login.accessToken"
            token = await page.evaluate(f'() => localStorage.getItem("{ls_key}")')
            if not token:
                return {"error": "Could not obtain access token. Session may have expired."}

            # 1. Fetch myCourses list (returns course IDs + links)
            my_url = f"{REST_BASE}/slc.tm.cp/student/myCourses?$filter=termId-eq={semester_id}&$orderBy=title=ascnf&$skip=0&$top=200"
            my_data = await _spa_xhr(page, my_url, token)
            if my_data is None:
                return {"error": "Failed to fetch myCourses. Session may have expired."}

            total = my_data.get("totalCount", 0)
            detail_links = [
                l for l in my_data.get("links", [])
                if l.get("rel") == "detail" and l.get("name") == "CpCourseDto"
            ]

            # 2. Fetch each course detail in parallel
            async def fetch_detail(course_key: str) -> dict | None:
                url = f"{REST_BASE}/slc.tm.cp/student/courses/{course_key}"
                return await _spa_xhr(page, url, token)

            details = await asyncio.gather(
                *(fetch_detail(l["key"]) for l in detail_links)
            )

            # 3. Parse into clean output
            courses = []
            for raw in details:
                if raw is None:
                    continue
                resources = raw.get("resource", [])
                if not resources:
                    continue
                dto = resources[0].get("content", {}).get("cpCourseDetailDto", {})
                course = dto.get("cpCourseDto", {})
                desc = dto.get("cpCourseDescriptionDto", {})

                title = _extract_lang(course.get("courseTitle"))
                course_type = course.get("courseTypeDto", {}).get("key", "")
                course_type_name = _extract_lang(course.get("courseTypeDto", {}).get("courseTypeName"))
                course_number = course.get("courseNumber", {}).get("courseNumber", "")

                # Instructors from lectureships
                instructors = []
                for lec in course.get("lectureships", []):
                    ident = lec.get("identityLibDto", {})
                    fname = ident.get("firstName", "")
                    lname = ident.get("lastName", "")
                    role = lec.get("teachingFunction", {}).get("name", "")
                    if fname or lname:
                        instructors.append({"name": f"{fname} {lname}".strip(), "role": role})

                # Language
                langs = []
                for ld in course.get("courseLanguageDtos", []):
                    lang_name = _extract_lang(ld.get("languageDto", {}).get("name"))
                    if lang_name:
                        langs.append(lang_name)

                # Description fields
                content = _extract_lang(desc.get("courseContent"))
                objective = _extract_lang(desc.get("courseObjective"))
                exam_method = _extract_lang(course.get("examinationMethodName"))

                # Organisation
                org = _extract_lang(course.get("organisationResponsibleDto", {}).get("name"))

                entry = {
                    "id": course.get("id"),
                    "course_number": course_number,
                    "title": title,
                    "type": course_type,
                    "type_name": course_type_name,
                    "language": ", ".join(langs) if langs else None,
                    "organisation": org or None,
                    "instructors": instructors,
                    "exam_method": exam_method or None,
                }
                if content:
                    entry["content"] = content
                if objective:
                    entry["objective"] = objective

                courses.append(entry)

            return {"total": total, "semester_id": semester_id, "courses": courses}
        except Exception as e:
            logger.exception("tumonline_my_courses failed")
            return {"error": str(e)}
        finally:
            await ctx.close()

    @mcp.tool()
    async def tumonline_register_course(
        username: str,
        course_id: str,
        group_id: str | None = None,
        confirm: bool = False,
    ) -> dict:
        """Register for a TUMonline course.

        course_id: internal numeric TUMonline course id (e.g. 950877768),
                   as returned by tumonline_my_courses or tumonline_search_courses.
        group_id: optional group/parallel selection (label substring).
        confirm: must be True to actually submit. Without it, navigates to the
                 registration procedure page and reports what it sees.
        """
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            # Deterministic SPA URL for a course's registration-procedure picker.
            # Verified: /ee/rest/pages/slc.tm.cp/course-registration/{id} redirects here.
            await page.goto(
                _desktop_url(
                    f"slc.tm.cp/student/courses/{course_id}/registrationProcedures?$ctx=design=ca"
                ),
                wait_until="networkidle",
                timeout=30_000,
            )
            await page.wait_for_timeout(2_000)
            page_title = await page.title()
            body_now = await page.inner_text("body")
            if "Page not found" in page_title or "Page not found" in body_now[:400]:
                return {
                    "error": "Course not open for registration (no registration procedures page).",
                    "course_id": course_id,
                    "page_title": page_title,
                    "url": page.url,
                }

            # On the procedure page, grab a useful summary of what's visible
            summary = await page.evaluate("""() => ({
                url: location.href,
                heading: document.querySelector('h1,h2')?.innerText?.trim() || '',
                body: document.body.innerText.slice(0, 1500),
            })""")

            # Optional group selector — click a label containing group_id if provided
            if group_id:
                try:
                    await page.get_by_text(group_id, exact=False).first.click(timeout=5_000)
                    await page.wait_for_timeout(500)
                except Exception:
                    logger.warning("Could not select group %s", group_id)

            if not confirm:
                return {
                    "status": "staged",
                    "message": "Registration procedure opened. Re-run with confirm=True to submit.",
                    "course_id": course_id,
                    "url": summary["url"],
                    "heading": summary["heading"],
                    "page_excerpt": summary["body"][:800],
                }

            if not await _click_first_matching(page, SUBMIT_REGISTRATION_TEXTS, timeout=8_000):
                return {
                    "error": "Could not find the 'Enter place request' submit button — a curriculum context may be required first.",
                    "course_id": course_id,
                    "url": page.url,
                    "page_excerpt": summary["body"][:800],
                }
            await page.wait_for_load_state("networkidle", timeout=15_000)

            return {
                "status": "submitted",
                "course_id": course_id,
                "url": page.url,
                "page_excerpt": (await page.inner_text("body"))[:800],
            }
        except Exception as e:
            logger.exception("tumonline_register_course failed")
            return {"error": str(e), "course_id": course_id}
        finally:
            await ctx.close()

    @mcp.tool()
    async def tumonline_register_exam(
        username: str,
        exam_id: str,
        confirm: bool = False,
    ) -> dict:
        """Register for a TUMonline exam.

        exam_id: exam/registration record id.
        confirm: must be True to submit. Otherwise only navigates + reports.
        """
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto(
                _desktop_url(f"slc.tm.cp/student/exams/{exam_id}"),
                wait_until="networkidle",
                timeout=30_000,
            )
            page_title = await page.title()

            opened = await _click_first_matching(page, EXAM_REGISTER_TEXTS, timeout=8_000)
            if not opened:
                return {
                    "error": "Could not find an exam-registration button.",
                    "exam_id": exam_id,
                    "page_title": page_title,
                    "url": page.url,
                }
            await page.wait_for_load_state("networkidle", timeout=15_000)

            if not confirm:
                return {
                    "status": "staged",
                    "message": "Exam registration page opened. Re-run with confirm=True to submit.",
                    "exam_id": exam_id,
                    "url": page.url,
                }

            confirmed = await _click_first_matching(page, SUBMIT_REGISTRATION_TEXTS, timeout=8_000)
            if not confirmed:
                return {
                    "error": "Could not find a confirmation button.",
                    "exam_id": exam_id,
                    "url": page.url,
                }
            await page.wait_for_load_state("networkidle", timeout=15_000)

            body_text = (await page.inner_text("body"))[:500]
            return {
                "status": "submitted",
                "exam_id": exam_id,
                "url": page.url,
                "page_excerpt": body_text,
            }
        except Exception as e:
            logger.exception("tumonline_register_exam failed")
            return {"error": str(e), "exam_id": exam_id}
        finally:
            await ctx.close()
