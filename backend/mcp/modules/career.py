"""TUM Career Center — job postings, career events, and career-coaching helpers.

Scrapes the public community.tum.de career pages via a headless browser
(content is client-rendered, no public API), plus pure-Python coaching tools
(CV audit, GitHub profile audit, skill extraction) that the agent uses to act
as a career coach.
"""

import logging
import re

import httpx
from mcp.server.fastmcp import FastMCP

import auth
import mock

logger = logging.getLogger(__name__)

CAREER_BASE = "https://www.community.tum.de"
JOBS_BASE = "https://jobportal.community.tum.de"
JOBS_URL = f"{JOBS_BASE}/search?language=en"
EVENTS_URL = f"{CAREER_BASE}/veranstaltungen/?thema%5B%5D=bewerbung&thema%5B%5D=jobsuche&thema%5B%5D=orientation&thema%5B%5D=intcareer"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def career_list_jobs(keyword: str = "", limit: int = 20) -> dict:
        """List job/internship postings from the TUM Career Center job board.

        keyword: optional filter matched against title/company (case-insensitive).
        limit: max number of postings to return.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("career", "career_list_jobs", keyword=keyword)
            if m is not None:
                return m
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(JOBS_URL)
                resp.raise_for_status()
            html = resp.text

            # jobportal.community.tum.de renders <li class="job"> with structured info
            import re as _re
            job_blocks = _re.findall(
                r'<li\s+class="job[^"]*">\s*<a\s+href="(/show/\d+)">(.*?)</a>\s*</li>',
                html, _re.DOTALL,
            )
            jobs = []
            for href, block in job_blocks:
                title_m = _re.search(r'<strong>\s*(.*?)\s*</strong>', block, _re.DOTALL)
                company_m = _re.search(r'class="company"[^>]*>(.*?)</li>', block)
                location_m = _re.search(r'class="location"[^>]*>(.*?)</li>', block)
                type_m = _re.search(r'class="type"[^>]*>(.*?)</li>', block)
                jobs.append({
                    "title": (title_m.group(1).strip() if title_m else ""),
                    "company": (company_m.group(1).strip() if company_m else ""),
                    "location": (location_m.group(1).strip() if location_m else ""),
                    "type": (type_m.group(1).strip() if type_m else ""),
                    "url": f"{JOBS_BASE}{href}",
                })

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

    @mcp.tool()
    async def career_list_events(keyword: str = "", limit: int = 20) -> dict:
        """List upcoming TUM Career Center events (career fairs, workshops, talks).

        keyword: optional filter matched against title/description.
        limit: max number of events to return.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("career", "career_list_events", keyword=keyword)
            if m is not None:
                return m
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(EVENTS_URL)
                resp.raise_for_status()
            html = resp.text
            strip_tags = lambda s: re.sub(r"<[^>]+>", "", s).strip()
            events: list[dict] = []
            for block_m in re.finditer(
                r'class="[^"]*events-teaser__item[^"]*"[^>]*>(.*?)</(?:div|article|li|section)>',
                html, re.DOTALL,
            ):
                block = block_m.group(1)
                title_m = re.search(r'class="[^"]*events-teaser__title[^"]*"[^>]*>(.*?)</[^>]+>', block, re.DOTALL)
                if not title_m:
                    title_m = re.search(r"<h3[^>]*>(.*?)</h3>", block, re.DOTALL)
                date_m = re.search(r'class="[^"]*events-teaser__date[^"]*"[^>]*>(.*?)</[^>]+>', block, re.DOTALL)
                datetime_m = re.search(r'<time[^>]*datetime="([^"]*)"', block)
                location_m = re.search(r'class="[^"]*events-teaser__location[^"]*"[^>]*>(.*?)</[^>]+>', block, re.DOTALL)
                summary_m = re.search(r'class="[^"]*events-teaser__text[^"]*"[^>]*>(.*?)</[^>]+>', block, re.DOTALL)
                if not summary_m:
                    summary_m = re.search(r"<p[^>]*>(.*?)</p>", block, re.DOTALL)
                url_m = re.search(r'<a[^>]*href="([^"]*)"', block)
                title = strip_tags(title_m.group(1)) if title_m else ""
                if not title:
                    continue
                ev_url = url_m.group(1) if url_m else ""
                if ev_url and not ev_url.startswith("http"):
                    ev_url = f"{CAREER_BASE}{ev_url}" if ev_url.startswith("/") else f"{CAREER_BASE}/{ev_url}"
                events.append({
                    "title": title,
                    "date": strip_tags(date_m.group(1)) if date_m else "",
                    "datetime": datetime_m.group(1) if datetime_m else "",
                    "location": strip_tags(location_m.group(1)) if location_m else "",
                    "summary": (strip_tags(summary_m.group(1))[:280] if summary_m else ""),
                    "url": ev_url,
                })

            if keyword:
                kw = keyword.lower()
                events = [
                    ev for ev in events
                    if kw in ev.get("title", "").lower() or kw in ev.get("summary", "").lower()
                ]

            if not events:
                return {
                    "events": [],
                    "count": 0,
                    "source": EVENTS_URL,
                    "note": "No events found — the page may require JS rendering.",
                }
            return {"events": events[:limit], "count": len(events[:limit]), "source": EVENTS_URL}
        except Exception as e:
            logger.exception("career_list_events failed")
            return {"error": str(e), "source": EVENTS_URL}

    @mcp.tool()
    async def career_audit_cv(cv_text: str) -> dict:
        """Audit a CV for professional-hygiene red flags.

        Pass the plain-text contents of the student's CV. Returns a list of
        findings (severity + message + suggestion) plus a 0-100 score.
        Pure rule-based — no LLM, no network. Use the agent to extract text
        from a PDF first, then call this for a structured audit.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("career", "career_audit_cv")
            if m is not None:
                return m
        text = cv_text or ""
        lower = text.lower()
        findings: list[dict] = []

        # 1. Email hygiene
        emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        unprofessional_re = re.compile(
            r"\b(gamer|xx|x_|cool|sexy|pimp|babe|kitty|princess|hottie|"
            r"lover|killer|ninja|noob|king|queen|lord|god|420|69|666|1337)\b",
            re.I,
        )
        for em in emails:
            local = em.split("@", 1)[0]
            if unprofessional_re.search(local) or re.search(r"\d{4,}", local):
                findings.append({
                    "severity": "high",
                    "category": "email",
                    "message": f"Email '{em}' looks unprofessional.",
                    "suggestion": "Use a firstname.lastname@... address for applications.",
                })
        if not emails:
            findings.append({
                "severity": "high",
                "category": "contact",
                "message": "No email address found.",
                "suggestion": "Add a contact email near the top of your CV.",
            })

        # 2. Section coverage
        required_sections = {
            "education": ["education", "studium", "ausbildung", "academic"],
            "experience": ["experience", "berufserfahrung", "work", "employment", "praktikum", "internship"],
            "skills": ["skills", "kenntnisse", "technologies", "tech stack"],
        }
        for name, needles in required_sections.items():
            if not any(n in lower for n in needles):
                findings.append({
                    "severity": "medium",
                    "category": "structure",
                    "message": f"No '{name}' section detected.",
                    "suggestion": f"Add a clearly labelled '{name.title()}' section.",
                })

        # 3. Weak / passive language
        weak_phrases = [
            "responsible for", "duties included", "helped with",
            "worked on", "participated in", "involved in",
        ]
        weak_hits = [p for p in weak_phrases if p in lower]
        if weak_hits:
            findings.append({
                "severity": "low",
                "category": "language",
                "message": f"Weak phrasing: {', '.join(weak_hits)}.",
                "suggestion": "Replace with action verbs (built, shipped, led, designed, measured).",
            })

        # 4. Quantification
        if not re.search(r"\b\d+\s*(%|percent|users|customers|x|k|m)\b", lower):
            findings.append({
                "severity": "low",
                "category": "impact",
                "message": "No quantified impact (%/users/x improvement) detected.",
                "suggestion": "Add at least one metric per role (e.g. 'reduced latency by 40%').",
            })

        # 5. Length
        words = len(text.split())
        if words < 150:
            findings.append({
                "severity": "high",
                "category": "length",
                "message": f"CV is very short ({words} words).",
                "suggestion": "A student CV should usually be 300–600 words, one page.",
            })
        elif words > 900:
            findings.append({
                "severity": "medium",
                "category": "length",
                "message": f"CV is long ({words} words).",
                "suggestion": "Trim to one page — drop pre-university roles unless directly relevant.",
            })

        # 6. Online presence
        has_linkedin = "linkedin.com/" in lower
        has_github = "github.com/" in lower
        if not has_linkedin:
            findings.append({
                "severity": "medium",
                "category": "presence",
                "message": "No LinkedIn URL found.",
                "suggestion": "Add your LinkedIn profile URL to the header.",
            })
        if not has_github and any(k in lower for k in ["python", "java", "react", "swe", "developer", "engineer"]):
            findings.append({
                "severity": "low",
                "category": "presence",
                "message": "Tech CV without a GitHub link.",
                "suggestion": "Add github.com/<you> so recruiters can see your code.",
            })

        # Score: start at 100, deduct by severity.
        weight = {"high": 20, "medium": 10, "low": 4}
        score = max(0, 100 - sum(weight[f["severity"]] for f in findings))

        return {
            "score": score,
            "findings": findings,
            "stats": {
                "word_count": words,
                "emails": emails,
                "has_linkedin": has_linkedin,
                "has_github": has_github,
            },
        }

    @mcp.tool()
    async def career_github_audit(username: str) -> dict:
        """Audit a GitHub profile via the public API.

        Returns repo count, top languages by repo, follower count, recent
        push activity. Uses the unauthenticated GitHub API (60 req/h/IP).
        Useful as the technical-presence half of a CV audit.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("career", "career_github_audit", username=username)
            if m is not None:
                return m
        async with httpx.AsyncClient(timeout=15, headers={"Accept": "application/vnd.github+json"}) as client:
            user_resp = await client.get(f"https://api.github.com/users/{username}")
            if user_resp.status_code == 404:
                return {"error": f"GitHub user '{username}' not found"}
            if user_resp.status_code != 200:
                return {"error": f"GitHub API returned {user_resp.status_code}", "detail": user_resp.text[:300]}
            user = user_resp.json()

            repos_resp = await client.get(
                f"https://api.github.com/users/{username}/repos",
                params={"per_page": 100, "sort": "pushed", "type": "owner"},
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

        lang_counts: dict[str, int] = {}
        stars = 0
        recent = []
        for r in repos:
            if r.get("fork"):
                continue
            lang = r.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            stars += r.get("stargazers_count", 0)
            recent.append({
                "name": r.get("name"),
                "language": lang,
                "stars": r.get("stargazers_count", 0),
                "pushed_at": r.get("pushed_at"),
                "description": r.get("description") or "",
                "url": r.get("html_url"),
            })

        top_languages = sorted(lang_counts.items(), key=lambda kv: -kv[1])[:5]
        recent.sort(key=lambda x: x["pushed_at"] or "", reverse=True)

        return {
            "username": user.get("login"),
            "name": user.get("name"),
            "bio": user.get("bio"),
            "public_repos": user.get("public_repos"),
            "followers": user.get("followers"),
            "created_at": user.get("created_at"),
            "total_stars": stars,
            "top_languages": [{"language": l, "repos": c} for l, c in top_languages],
            "recent_repos": recent[:10],
            "profile_url": user.get("html_url"),
        }

    # Curated keyword → canonical-skill map. Order matters: longer phrases first.
    _SKILL_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\bmachine learning|ml\b|statistical learning", re.I), "Machine Learning"),
        (re.compile(r"\bdeep learning|neural network", re.I), "Deep Learning"),
        (re.compile(r"\bnatural language processing|\bnlp\b", re.I), "NLP"),
        (re.compile(r"\bcomputer vision|image processing", re.I), "Computer Vision"),
        (re.compile(r"\breinforcement learning\b", re.I), "Reinforcement Learning"),
        (re.compile(r"\b(data structures|algorithms)\b", re.I), "Algorithms & Data Structures"),
        (re.compile(r"\bdatabases?\b|sql|relational", re.I), "Databases"),
        (re.compile(r"\bdistributed systems\b|microservices", re.I), "Distributed Systems"),
        (re.compile(r"\boperating systems?\b", re.I), "Operating Systems"),
        (re.compile(r"\bcomputer networks?\b|networking", re.I), "Networking"),
        (re.compile(r"\bsoftware engineering\b|software design", re.I), "Software Engineering"),
        (re.compile(r"\bcompiler|programming languages?\b", re.I), "Compilers / PL"),
        (re.compile(r"\bsecurity\b|cryptograph", re.I), "Security & Cryptography"),
        (re.compile(r"\bcloud\b|aws|azure|gcp|kubernetes", re.I), "Cloud & DevOps"),
        (re.compile(r"\bweb (development|engineering)|frontend|backend", re.I), "Web Development"),
        (re.compile(r"\bmobile\b|android|ios", re.I), "Mobile Development"),
        (re.compile(r"\bembedded\b|iot|microcontroller", re.I), "Embedded Systems"),
        (re.compile(r"\brobotic", re.I), "Robotics"),
        (re.compile(r"\bcontrol (theory|systems)\b", re.I), "Control Systems"),
        (re.compile(r"\bsignal processing\b", re.I), "Signal Processing"),
        (re.compile(r"\bstatistic|probability\b", re.I), "Statistics & Probability"),
        (re.compile(r"\blinear algebra|numerical", re.I), "Numerical Methods"),
        (re.compile(r"\boptimization\b", re.I), "Optimization"),
        (re.compile(r"\beconomic|finance|accounting", re.I), "Economics & Finance"),
        (re.compile(r"\bmanagement\b|leadership|entrepreneurship", re.I), "Management"),
    ]

    @mcp.tool()
    async def career_skills_from_courses(courses: list[dict]) -> dict:
        """Extract canonical skills from a list of courses.

        Each course should be a dict with at least a 'title'; optionally
        'content', 'objective', or 'description'. Returns a deduplicated
        list of skills with the courses that map to each.

        Pair with tumonline_my_courses to build the student's skill profile,
        then match against a job posting in the agent layer.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("career", "career_skills_from_courses")
            if m is not None:
                return m
        skill_to_courses: dict[str, list[str]] = {}
        for c in courses or []:
            text = " ".join(str(c.get(k, "") or "") for k in ("title", "content", "objective", "description", "name"))
            if not text.strip():
                continue
            label = c.get("title") or c.get("name") or "(untitled)"
            for pattern, skill in _SKILL_PATTERNS:
                if pattern.search(text):
                    skill_to_courses.setdefault(skill, []).append(label)

        skills = [
            {"skill": s, "course_count": len(set(cs)), "courses": sorted(set(cs))}
            for s, cs in sorted(skill_to_courses.items(), key=lambda kv: -len(set(kv[1])))
        ]
        return {"skills": skills, "count": len(skills)}

    @mcp.tool()
    async def career_get_job(url: str) -> dict:
        """Fetch the full details of a single job posting by URL."""
        if mock.is_demo_mode():
            m = mock.get_mock("career", "career_get_job", url=url)
            if m is not None:
                return m
        if not (url.startswith(CAREER_BASE) or url.startswith(JOBS_BASE)):
            return {"error": f"URL must be on {CAREER_BASE} or {JOBS_BASE}"}
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
