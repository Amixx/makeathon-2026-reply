"""Tiny Jinja2 wrapper for prompt + Markdown templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_PROMPTS_DIR = Path(__file__).parent / "prompts"

_env = Environment(
    loader=FileSystemLoader(_PROMPTS_DIR),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_prompt(name: str, **vars) -> str:
    return _env.get_template(name).render(**vars)
