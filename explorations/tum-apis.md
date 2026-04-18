# TUM API Exploration Notes

## NAT API (`https://api.srv.nat.tum.de/api/v1`)

Full OpenAPI spec at `/api/v1/openapi.json`. Massive API with ~300 endpoints.

### Public (no auth needed) — confirmed working

| Endpoint | What it returns | Notes |
|---|---|---|
| `GET /semesters` | All semesters since 1998 | Has `is_current` flag |
| `GET /semesters/extended` | Semesters + exam periods, registration dates | **Best for "when are exams?"** |
| `GET /course` | Course search, paginated | `?q=Machine+Learning` works. Returns `course_id`, name, hours/week |
| `GET /course/{course_id}` | Single course detail | Includes activity type (lecture/exercise), instructor list |
| `GET /course/{course_id}/schedule` | Course schedule/timetable | |
| `GET /programs/search` | Degree program search | `?q=informatics` → all informatics programs |
| `GET /programs/combined` | Combined study programs | |
| `GET /rom/campus` | All TUM campuses + buildings | Includes lat/lng, addresses |
| `GET /rom/building/{code}` | Building details | |
| `GET /rom/{room_code}` | Room details | |
| `GET /rom/{room_code}/schedule` | Room schedule/booking | |
| `GET /orgs` | Organization/chair search | `?q=informatik` → all CS chairs |
| `GET /orgs/tree/{org_id}` | Org hierarchy | |
| `GET /mhb/module/{code}` | Module handbook entry | `IN0011` → "Intro to Theory of Computation", credits, responsible prof |
| `GET /mhb/module/{code}/schedule` | Module schedule | |

### Auth required (Bearer token or API key)

| Endpoint | What it does |
|---|---|
| `GET /persons/vcard/me` | Current user's info |
| `GET /user/search` | Search users |
| `GET /students/search` | Search students |
| `GET /students/{username}` | Student details |
| `GET /exam/achievement/{course_id}` | Exam results for a course |

### Key findings

1. **Course search is on `/course` not `/course-catalog/search`** — our current `tumonline_search_courses` tool uses wrong path and returns 404!
2. **Module handbook (`/mhb/module/{code}`)** is public and very useful — gives ECTS, description, prerequisites, responsible prof
3. **Room schedule (`/rom/{room_code}/schedule`)** is public — could show free rooms
4. **Exam periods in `/semesters/extended`** — much richer than bare `/semesters`
5. **Program/SPO structure (`/spo/structure/{id}`)** exists — could map degree requirements

### Fix needed in tumonline.py

```python
# BROKEN (404):
url = f"{NAT_API_BASE}/course-catalog/search"

# CORRECT:
url = f"{NAT_API_BASE}/course"
params = {"q": query, "limit": limit}
```

Same for rooms — should be `/rom/list` or `/rom/{room_code}`, not `/rooms`.

---

## Navigatum API (`https://nav.tum.de/api`)

Public, no auth. Working.

| Endpoint | What it returns |
|---|---|
| `GET /search?q=MW&limit_all=10` | Search buildings, rooms | Returns faceted results (rooms, sites_buildings) |
| `GET /locations/{id}` | Room/building details | |

Good for "where is X on campus?" questions. Complements NAT's `/rom/` endpoints.

---

## Eat API (`https://tum-dev.github.io/eat-api/en`)

Static JSON, no auth. Working.

| Pattern | Example |
|---|---|
| `/{canteen}/{year}/{week}.json` | `/mensa-garching/2026/16.json` |

Returns dishes with prices (student/staff/guest), allergen labels, dish type.

---

## MVG (`mvg` Python package)

No auth. Working. Uses `MvgApi.station()` and `MvgApi.departures()`.

---

## Strategy: API-first, Playwright only when forced

- **Use NAT API** for courses, modules, semesters, rooms, buildings, orgs — it's fast and structured
- **Use Playwright** only for actions that have no API: course registration, exam registration, Moodle scraping
- **Module handbook (`/mhb/module/`)** is a goldmine for the career coach use case — module descriptions, ECTS, prerequisites
- **Exam periods** from `/semesters/extended` are perfect for "when should I study?" advice

---

## TUMonline authenticated SPA REST (`{TUM_BASE}/{DSYSTEM|tumonline}/ee/rest`)

Verified against `demo.campus.tum.de/DSYSTEM` on 2026-04. The Angular SPA
fetches data via REST with a Bearer token stashed in `localStorage`.

### Getting a token

After a Playwright login, the SPA writes an access token to:

```js
localStorage.getItem("DSYSTEM_co.login.accessToken")   // demo
localStorage.getItem("tumonline_co.login.accessToken") // prod
```

Once we have it, any `/ee/rest/*` path is callable via
`Authorization: Bearer <token>` + `Accept: application/json`. We make the XHR
from inside the page context (see `_spa_xhr` in `modules/tumonline.py`) — this
avoids CORS and reuses the SPA's cookies.

### Useful REST endpoints

| Endpoint | What it returns |
|---|---|
| `GET /ee/rest/slc.tm.cp/student/myCourses?$filter=termId-eq={semId}&$top=200` | Registered courses for a term. Response has `links[]` with `rel="detail"` pointing at each course |
| `GET /ee/rest/slc.tm.cp/student/courses/{course_id}` | Full course detail (`cpCourseDetailDto`) — title, type, SWS, lectureships with roles, exam method, languages, description |
| `GET /ee/rest/pages/slc.tm.cp/course-registration/{course_id}` | Returns `{"location": "<SPA URL>"}` — the SPA URL of the registration-procedure page for that course |

### Deterministic registration URL

For any course open for registration:

```text
{TUM_BASE}/{TUM_ONLINE_PATH}/ee/ui/ca2/app/desktop/#/slc.tm.cp/student/courses/{course_id}/registrationProcedures?$ctx=design=ca
```

On load, the SPA either lands on a procedure-picker page or auto-redirects to
the single procedure (`.../registrationProcedures/{procedure_id}?courseId=...`).
The procedure page shows: registration period, ranking options, participant cap,
groups, and any curriculum-context errors — all scrapeable from `body.innerText`
for a staged preview.

### SPA DOM component names (useful for Playwright)

Courses list (`#/slc.tm.cp/student/courses?...`) renders each row as:

- `ca-list-entry` — the container
  - `slc-course-number` — course number (e.g. `0000001204`)
  - `slc-course-title` — course title
  - `tm-regprocedure-button` — registration link/status (holds an `<a>` with href pointing at `/ee/rest/pages/slc.tm.cp/course-registration/{course_id}`)
  - `tm-status-course-registration` — status text
  - `tm-status-course-eval` — evaluation status

### Verified UI button texts (EN + DE)

| Action | English | German |
|---|---|---|
| Row → open registration | `Go to course registration` | `Zur Anmeldung` |
| Submit registration | `Enter place request` | `Zum Platz anmelden` |
| View existing reg (already registered) | `View course registration detail` | — |
