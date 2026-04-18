"""Playwright-based TUM SSO authentication and browser context management."""

import asyncio
import logging

from playwright.async_api import Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError, async_playwright

import session_store
from config import FERNET_KEY, SESSION_STORE_PATH, TUM_BASE_URL, TUM_ONLINE_PATH

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


def _login_button_selector() -> str:
    return "text=TUM Login"


async def login(username: str, password: str) -> tuple[bool, str]:
    """Perform TUM SSO login via Playwright and persist storageState."""
    logger.info("auth.login called for username=%s", username)
    if not FERNET_KEY:
        logger.error("auth.login aborted: FERNET_KEY is not set")
        return False, "Server misconfiguration: FERNET_KEY is not set on the deployed app."

    browser = await _get_browser()
    context = await browser.new_context()
    page = await context.new_page()

    try:
        # Step 1: Navigate to TUMonline landing page
        landing_url = f"{TUM_BASE_URL}{TUM_ONLINE_PATH}/"
        logger.info("auth.login step=goto_landing url=%s", landing_url)
        await page.goto(landing_url, wait_until="domcontentloaded", timeout=30_000)

        # Step 2: Click "TUM Login" to redirect to Shibboleth IdP
        logger.info("auth.login step=click_tum_login current_url=%s", page.url)
        await page.locator(_login_button_selector()).first.click(timeout=10_000)
        await page.wait_for_selector("#username", timeout=30_000)

        # Step 3: Fill the Shibboleth SSO form at login.tum.de
        logger.info("auth.login step=submit_credentials current_url=%s", page.url)
        await page.fill("#username", username)
        await page.fill("#password", password)
        await page.click("#btnLogin")

        # Step 4: Wait for redirect back to TUMonline (authenticated state)
        logger.info("auth.login step=wait_for_redirect current_url=%s", page.url)
        await page.wait_for_url(lambda url: url.startswith(TUM_BASE_URL), timeout=45_000)
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)

        # Capture session state
        logger.info(
            "auth.login step=save_session current_url=%s session_store_path=%s",
            page.url,
            SESSION_STORE_PATH,
        )
        state = await context.storage_state()
        session_store.save(username, state)
        logger.info("auth.login succeeded for username=%s", username)
        return True, "Logged in successfully. Session saved."

    except PlaywrightTimeoutError:
        logger.exception("auth.login timed out for username=%s at url=%s", username, page.url)
        return False, f"Login timed out while waiting for TUM to respond. Last URL: {page.url}"
    except Exception as exc:
        logger.exception("auth.login failed for username=%s at url=%s", username, page.url)
        return False, f"Login failed on the server at {page.url}: {type(exc).__name__}"
    finally:
        await context.close()


async def get_context(username: str) -> BrowserContext | None:
    """Return a BrowserContext with loaded storageState, or None if no session."""
    state = session_store.load(username)
    if state is None:
        return None
    browser = await _get_browser()
    return await browser.new_context(storage_state=state)


async def get_anonymous_context() -> BrowserContext:
    """Return a fresh BrowserContext with no auth — for scraping public pages."""
    browser = await _get_browser()
    return await browser.new_context()


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


async def get_access_token(username: str) -> str | None:
    """Load session, navigate to SPA, and return the REST API access token from localStorage."""
    ctx = await get_context(username)
    if ctx is None:
        return None
    try:
        page = await ctx.new_page()
        await page.goto(
            f"{TUM_BASE_URL}{TUM_ONLINE_PATH}/ee/ui/ca2/app/desktop/#/home",
            wait_until="networkidle",
            timeout=30_000,
        )
        await page.wait_for_timeout(3000)
        ls_key = f"{TUM_ONLINE_PATH.lstrip('/')}_co.login.accessToken"
        token = await page.evaluate(
            f'() => localStorage.getItem("{ls_key}")'
        )
        return token
    except Exception:
        logger.exception("Failed to get access token for username=%s", username)
        return None
    finally:
        await ctx.close()


async def logout(username: str) -> None:
    """Delete stored session."""
    session_store.delete(username)
    logger.info("Session deleted for username=%s", username)
