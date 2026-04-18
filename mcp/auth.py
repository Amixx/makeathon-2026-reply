"""Playwright-based TUM SSO authentication and browser context management."""

import asyncio
import logging

from playwright.async_api import Browser, BrowserContext, async_playwright

import session_store
from config import TUM_BASE_URL, TUM_ONLINE_PATH

logger = logging.getLogger(__name__)

# Global browser instance (reused across calls)
_browser: Browser | None = None
_pw_context_manager = None
_lock = asyncio.Lock()


async def _get_browser() -> Browser:
    global _browser, _pw_context_manager
    if _browser is None or not _browser.is_connected():
        async with _lock:
            if _browser is None or not _browser.is_connected():
                _pw_context_manager = async_playwright()
                pw = await _pw_context_manager.start()
                _browser = await pw.chromium.launch(headless=True)
    return _browser


async def login(username: str, password: str) -> bool:
    """Perform TUM SSO login via Playwright, persist storageState. Returns True on success."""
    logger.info("auth.login called for username=%s", username)
    browser = await _get_browser()
    context = await browser.new_context()
    page = await context.new_page()

    try:
        # Step 1: Navigate to TUMonline landing page
        await page.goto(f"{TUM_BASE_URL}{TUM_ONLINE_PATH}/", wait_until="networkidle", timeout=30_000)

        # Step 2: Click "TUM Login" to redirect to Shibboleth IdP
        await page.click("text=TUM Login", timeout=10_000)
        await page.wait_for_load_state("networkidle", timeout=30_000)

        # Step 3: Fill the Shibboleth SSO form at login.tum.de
        await page.fill("#username", username)
        await page.fill("#password", password)
        await page.click("#btnLogin")

        # Step 4: Wait for redirect back to TUMonline (authenticated state)
        await page.wait_for_url(f"{TUM_BASE_URL}/**", timeout=30_000)

        # Capture session state
        state = await context.storage_state()
        session_store.save(username, state)
        logger.info("auth.login succeeded for username=%s", username)
        return True

    except Exception:
        logger.exception("auth.login failed for username=%s", username)
        return False
    finally:
        await context.close()


async def get_context(username: str) -> BrowserContext | None:
    """Return a BrowserContext with loaded storageState, or None if no session."""
    state = session_store.load(username)
    if state is None:
        return None
    browser = await _get_browser()
    return await browser.new_context(storage_state=state)


async def is_session_valid(username: str) -> bool:
    """Lightweight check: load session and hit an authenticated page."""
    ctx = await get_context(username)
    if ctx is None:
        return False
    try:
        page = await ctx.new_page()
        resp = await page.goto(
            f"{TUM_BASE_URL}{TUM_ONLINE_PATH}/ee/ui/ca2/app/desktop/#/home",
            wait_until="networkidle",
            timeout=15_000,
        )
        # If we land on the home page (not redirected to login), session is valid
        url = page.url
        return "login" not in url.lower() and resp is not None and resp.status == 200
    except Exception:
        logger.exception("Session validity check failed for username=%s", username)
        return False
    finally:
        await ctx.close()


async def logout(username: str) -> None:
    """Delete stored session."""
    session_store.delete(username)
    logger.info("Session deleted for username=%s", username)
