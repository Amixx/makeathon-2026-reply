"""Playwright-based TUM SSO authentication and browser context management."""

import asyncio
import logging

from playwright.async_api import Browser, BrowserContext, async_playwright

import session_store
from config import TUM_BASE_URL

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


async def login(user_id: str, username: str, password: str) -> bool:
    """Perform TUM SSO login via Playwright, persist storageState. Returns True on success."""
    logger.info("auth.login called for user_id=%s", user_id)
    browser = await _get_browser()
    context = await browser.new_context()
    page = await context.new_page()

    try:
        # Navigate to TUMonline which redirects to Shibboleth SSO
        await page.goto(f"{TUM_BASE_URL}/tumonline/ee/ui/ca2/app/desktop/#/login", wait_until="networkidle", timeout=30_000)

        # Fill SSO form
        await page.fill('input[name="username"], input#username', username)
        await page.fill('input[name="password"], input#password', password)
        await page.click('button[type="submit"], input[type="submit"]')

        # Wait for redirect back to TUMonline (authenticated state)
        await page.wait_for_url(f"{TUM_BASE_URL}/**", timeout=30_000)

        # Capture session state
        state = await context.storage_state()
        session_store.save(user_id, state)
        logger.info("auth.login succeeded for user_id=%s", user_id)
        return True

    except Exception:
        logger.exception("auth.login failed for user_id=%s", user_id)
        return False
    finally:
        await context.close()


async def get_context(user_id: str) -> BrowserContext | None:
    """Return a BrowserContext with loaded storageState, or None if no session."""
    state = session_store.load(user_id)
    if state is None:
        return None
    browser = await _get_browser()
    return await browser.new_context(storage_state=state)


async def is_session_valid(user_id: str) -> bool:
    """Lightweight check: load session and hit an authenticated page."""
    ctx = await get_context(user_id)
    if ctx is None:
        return False
    try:
        page = await ctx.new_page()
        resp = await page.goto(
            f"{TUM_BASE_URL}/tumonline/ee/ui/ca2/app/desktop/#/login",
            wait_until="networkidle",
            timeout=15_000,
        )
        # If we're redirected past the login page, session is valid
        url = page.url
        return "login" not in url.lower() or resp is not None and resp.status == 200
    except Exception:
        logger.exception("Session validity check failed for user_id=%s", user_id)
        return False
    finally:
        await ctx.close()


async def logout(user_id: str) -> None:
    """Delete stored session."""
    session_store.delete(user_id)
    logger.info("Session deleted for user_id=%s", user_id)
