export type DocTool = {
  name: string;
  description: string;
};

export type DocToolGroup = {
  slug: string;
  title: string;
  summary: string;
  tools: DocTool[];
};

export type DocSection = {
  id: string;
  label: string;
  eyebrow?: string;
  title: string;
  intro: string;
  body?: string[];
  bullets?: string[];
  code?: {
    label: string;
    language: string;
    content: string;
  };
  callout?: string;
};

export const mcpSections: DocSection[] = [
  {
    id: "overview",
    label: "Overview",
    eyebrow: "Campus Co-Pilot MCP",
    title: "A TUM systems MCP for discovery and action",
    intro:
      "Campus Co-Pilot exposes TUM services as agent-callable tools over streamable HTTP. It is designed for a hackathon demo, so the focus is end-to-end flows, deterministic demo mode, and agent actions like course and sports registration rather than production-hardening.",
    bullets: [
      "Built with FastMCP in Python.",
      "Served under /mcp through a Starlette gateway.",
      "Mixes public APIs, Playwright-authenticated browser automation, and curated mocks.",
      "Currently exposes 47 tools across campus, study, transport, and career workflows.",
    ],
    code: {
      label: "MCP endpoint",
      language: "text",
      content: "https://<your-host>/mcp",
    },
  },
  {
    id: "quickstart",
    label: "Quickstart",
    title: "Run the MCP locally",
    intro:
      "The MCP lives in backend/mcp. You can run it standalone for local development, or behind the public gateway when you want the same path layout as deployment.",
    body: [
      "Set FERNET_KEY before using any authenticated tools. Without it, login can succeed transiently in-browser but session persistence will fail.",
      "TUM_ENV controls whether TUMonline flows target the demo or production environment.",
    ],
    code: {
      label: "Local setup",
      language: "bash",
      content:
        "cd backend/mcp\npython -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\ncp .env.example .env\npython server.py",
    },
    callout:
      "The MCP defaults to 0.0.0.0:8000. The public gateway can proxy /mcp to that internal service.",
  },
  {
    id: "transport",
    label: "Transport",
    title: "How the server is exposed",
    intro:
      "backend/mcp/server.py creates a FastMCP app and returns mcp.streamable_http_app(). The repo-level public gateway routes plain /mcp traffic to the MCP server and reserves special Inspector query patterns for the Inspector proxy.",
    bullets: [
      "FastMCP server name: Campus Co-Pilot",
      "Transport: streamable HTTP",
      "Default MCP host/port: 0.0.0.0:8000",
      "Public path through gateway: /mcp",
    ],
    code: {
      label: "Core registration pattern",
      language: "python",
      content:
        "mcp = FastMCP(\n    \"Campus Co-Pilot\",\n    instructions=\"TUM campus systems exposed as agent-callable tools\",\n    host=MCP_HOST,\n    port=MCP_PORT,\n)\n\nfor mod in [auth_tools, mensa, tumonline, navigatum, mvv, moodle, matrix, collab, zhs, career, linkedin, professors]:\n    mod.register(mcp)\n\napp = mcp.streamable_http_app()",
    },
  },
  {
    id: "auth",
    label: "Auth",
    title: "SSO, browser sessions, and action tools",
    intro:
      "Auth-requiring tools rely on Playwright. tum_login launches a headless Chromium session, signs into TUM SSO, and stores encrypted Playwright storageState on disk. Later tools reopen a browser context from that state using the username as the lookup key.",
    bullets: [
      "Credentials are used only during login and are not persisted.",
      "Session blobs are encrypted with Fernet and stored under SESSION_STORE_PATH.",
      "Authenticated modules include Moodle, private TUMonline endpoints, and ZHS booking.",
      "Most write actions use a staged flow: inspect first with confirm=false, then submit with confirm=true.",
    ],
    code: {
      label: "Primary auth tools",
      language: "text",
      content:
        "tum_login(username, password)\ntum_session_status(username)\ntum_logout(username)",
    },
  },
  {
    id: "demo-mode",
    label: "Demo Mode",
    title: "Curated responses for reliable demos",
    intro:
      "The MCP has a global demo-mode toggle. When enabled, tools try to resolve a canned response from backend/mcp/data/mock/<module>/<tool>.json before touching real upstream systems.",
    bullets: [
      "Enable with set_demo_mode(true).",
      "Check state with get_demo_mode().",
      "Mock files can be plain JSON or keyed by one input parameter.",
      "Useful for stable pitches when live campus systems are slow or unavailable.",
    ],
    code: {
      label: "Example keyed mock shape",
      language: "json",
      content:
        "{\n  \"__key__\": \"canteen_id\",\n  \"mensa-garching\": { \"menu\": [] },\n  \"__default__\": { \"menu\": [] }\n}",
    },
  },
  {
    id: "architecture",
    label: "Architecture",
    title: "Where the MCP sits in the full stack",
    intro:
      "The MCP is the integration and execution layer. The agent service connects to it at startup, lists available tools, and wraps them for model tool use. The frontend then streams the agent output and tool events to the UI.",
    bullets: [
      "Frontend talks to /agent, not directly to /mcp.",
      "backend/agent/tools.py fetches MCP tool metadata at startup.",
      "The chat route uses a small local toolset; the planning route gets the full MCP inventory.",
      "This keeps campus integrations isolated from prompt orchestration.",
    ],
    code: {
      label: "Request flow",
      language: "text",
      content:
        "Frontend -> /agent/*\nAgent -> list_tools() / call_tool() on MCP\nMCP -> Public APIs / Playwright browser flows / mock data",
    },
  },
  {
    id: "modules",
    label: "Modules",
    title: "Tool groups",
    intro:
      "Each module exports register(mcp) and adds one or more @mcp.tool functions. The current server mixes public retrieval tools with action-oriented tools that can actually change state in external systems.",
  },
];

export const mcpToolGroups: DocToolGroup[] = [
  {
    slug: "auth-tools",
    title: "Auth and Demo Controls",
    summary: "Session management, demo toggling, and the entrypoint for any auth-gated workflow.",
    tools: [
      { name: "set_demo_mode", description: "Globally switch tools to curated mock responses." },
      { name: "get_demo_mode", description: "Return whether demo mode is active." },
      { name: "tum_login", description: "Authenticate against TUM SSO and persist encrypted browser state." },
      { name: "tum_session_status", description: "Validate the stored session for a user." },
      { name: "tum_logout", description: "Delete the stored session blob for a user." },
    ],
  },
  {
    slug: "mensa",
    title: "Mensa",
    summary: "Public canteen discovery and weekly menu data from the Eat API.",
    tools: [
      { name: "mensa_list_canteens", description: "List supported TUM canteens and IDs." },
      { name: "mensa_get_menu", description: "Fetch the menu for a canteen and ISO week." },
    ],
  },
  {
    slug: "tumonline",
    title: "TUMonline",
    summary: "The largest module: public NAT API reads, authenticated student views, and staged registration actions.",
    tools: [
      { name: "tumonline_search_courses", description: "Search the public TUMonline course catalog." },
      { name: "tumonline_search_rooms", description: "Search rooms by code or name." },
      { name: "tumonline_get_semester_info", description: "Return current and upcoming semester metadata." },
      { name: "tumonline_get_course", description: "Fetch full detail for a course by course ID." },
      { name: "tumonline_get_module", description: "Fetch module handbook detail by module code." },
      { name: "tumonline_search_programs", description: "Search degree programs and return study identifiers." },
      { name: "tumonline_list_program_modules", description: "List modules in a catalog tag." },
      { name: "tumonline_list_module_catalogs", description: "List available module catalogs." },
      { name: "tumonline_search_orgs", description: "Search chairs, departments, and organizations." },
      { name: "tumonline_get_course_schedule", description: "Return weekly schedule data for a course." },
      { name: "tumonline_my_courses", description: "List a logged-in student's semester courses with enriched details." },
      { name: "tumonline_get_room_schedule", description: "Return bookings for a room code." },
      { name: "tumonline_my_exams", description: "List the student's registered exams." },
      { name: "tumonline_register_course", description: "Open and optionally submit a course registration flow." },
      { name: "tumonline_register_exam", description: "Open and optionally submit an exam registration flow." },
    ],
  },
  {
    slug: "navigatum",
    title: "Navigatum",
    summary: "Public room and campus navigation lookups.",
    tools: [
      { name: "navigatum_search", description: "Search buildings, rooms, and locations." },
      { name: "navigatum_get_room", description: "Fetch detail for a Navigatum location ID." },
    ],
  },
  {
    slug: "mvv",
    title: "MVV / MVG",
    summary: "Munich transit lookup for stations and upcoming departures.",
    tools: [
      { name: "mvv_get_departures", description: "Return upcoming departures for a station." },
      { name: "mvv_search_station", description: "Resolve a station from a text query." },
    ],
  },
  {
    slug: "moodle",
    title: "Moodle",
    summary: "Authenticated scraping for enrolled courses, assignments, grades, and resource extraction.",
    tools: [
      { name: "moodle_list_courses", description: "List enrolled Moodle courses for a logged-in user." },
      { name: "moodle_list_assignments", description: "List upcoming assignment and calendar deadlines." },
      { name: "moodle_get_course_content", description: "Enumerate sections and resources inside a course." },
      { name: "moodle_fetch_resource_text", description: "Extract text from Moodle HTML or PDF resources." },
      { name: "moodle_list_grades", description: "Return overview grades across enrolled courses." },
    ],
  },
  {
    slug: "zhs",
    title: "ZHS",
    summary: "Sports catalog discovery plus a staged booking flow using Playwright and TUM SSO.",
    tools: [
      { name: "zhs_list_sports", description: "List public sports categories and URLs." },
      { name: "zhs_list_slots", description: "List bookable slots from a sport page." },
      { name: "zhs_book_slot", description: "Stage or submit a ZHS booking flow." },
    ],
  },
  {
    slug: "career",
    title: "Career",
    summary: "Career-center scraping plus rule-based coaching helpers for CVs, GitHub, and skill extraction.",
    tools: [
      { name: "career_list_jobs", description: "List job and internship postings from the TUM career portal." },
      { name: "career_list_events", description: "List upcoming career events." },
      { name: "career_audit_cv", description: "Run a rule-based CV quality audit on plain text." },
      { name: "career_github_audit", description: "Audit a public GitHub profile via the GitHub API." },
      { name: "career_skills_from_courses", description: "Extract canonical skills from course data." },
      { name: "career_get_job", description: "Fetch full content for a single job posting." },
    ],
  },
  {
    slug: "linkedin",
    title: "LinkedIn",
    summary: "Demo-only outreach helper with curated mock contacts.",
    tools: [
      { name: "linkedin_search_people", description: "Return mocked outreach contacts for a target query." },
    ],
  },
  {
    slug: "professors",
    title: "Professors",
    summary: "Mock-backed research-area and department lookup.",
    tools: [
      { name: "professors_list_fachbereiche", description: "List available TUM subject areas." },
      { name: "professors_search", description: "Search professors by name, Fachbereich, or topic." },
    ],
  },
  {
    slug: "collab",
    title: "Collab Wiki",
    summary: "Confluence-based search and page retrieval with a token supplied per call.",
    tools: [
      { name: "collab_search", description: "Search Confluence content with CQL." },
      { name: "collab_get_page", description: "Fetch rendered HTML for a page by ID." },
    ],
  },
  {
    slug: "matrix",
    title: "Matrix",
    summary: "Reserved for future chat actions. Currently explicit stubs.",
    tools: [
      { name: "matrix_send_message", description: "Stub for sending a Matrix message." },
      { name: "matrix_list_rooms", description: "Stub for listing joined Matrix rooms." },
    ],
  },
];

export const installSnippets = [
  {
    title: "Codex CLI",
    description: "Add the deployed MCP as a remote server in Codex.",
    code: "codex mcp add campus-copilot --url https://<your-host>/mcp",
  },
  {
    title: "Cursor",
    description: "Add the server to .cursor/mcp.json.",
    code:
      '{\n  "mcpServers": {\n    "campus-copilot": {\n      "url": "https://<your-host>/mcp"\n    }\n  }\n}',
  },
  {
    title: "ChatGPT Developer Mode",
    description: "Create a custom connector pointing to the MCP endpoint.",
    code:
      "Name: Campus Co-Pilot\nMCP server URL: https://<your-host>/mcp\nAuthentication: None or your chosen auth wrapper",
  },
];
