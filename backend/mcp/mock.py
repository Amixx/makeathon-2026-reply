"""Demo-mode mock data layer.

Toggle with the `set_demo_mode` MCP tool. When enabled, tools call
`get_mock(module, tool_name, **kwargs)` which returns curated JSON
from data/mock/{module}/{tool_name}.json.

Mock files can optionally be keyed by a parameter value. For example,
data/mock/mensa/mensa_get_menu.json can be either:
  - A plain dict/list → returned as-is
  - A dict with a "__key__" field → we look up kwargs[__key__] in the dict
"""

import asyncio
import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

MOCK_DIR = Path(__file__).parent / "data" / "mock"

# ── Global toggle ────────────────────────────────────────────────────────────
_demo_mode: bool = False


def is_demo_mode() -> bool:
    return _demo_mode


def set_demo_mode(enabled: bool) -> None:
    global _demo_mode
    _demo_mode = enabled
    logger.info("Demo mode %s", "ENABLED" if enabled else "DISABLED")


# ── Mock data loader ─────────────────────────────────────────────────────────
async def get_mock(module: str, tool_name: str, **kwargs) -> dict | list | None:
    """Load mock response from data/mock/{module}/{tool_name}.json.

    Returns None if no mock file exists (tool should fall through to real impl).
    Adds a random 0.5–1.5s delay to simulate real API latency.
    """
    path = MOCK_DIR / module / f"{tool_name}.json"
    if not path.exists():
        logger.warning("No mock file at %s — falling through to real implementation", path)
        return None

    await asyncio.sleep(random.uniform(0.5, 1.5))

    data = json.loads(path.read_text())

    # Support keyed lookups: {"__key__": "canteen_id", "mensa-garching": {...}, ...}
    if isinstance(data, dict) and "__key__" in data:
        key_param = data["__key__"]
        key_value = str(kwargs.get(key_param, ""))
        if key_value in data:
            return data[key_value]
        if "__default__" in data:
            return data["__default__"]
        logger.warning("Mock key '%s=%s' not found in %s", key_param, key_value, path)
        return None

    return data
