# Mock Data for Demo Mode

Place JSON files here to provide curated responses when demo mode is active.

## Structure

```
data/mock/
├── {module}/
│   └── {tool_name}.json
```

Example: `data/mock/mensa/mensa_get_menu.json`

## Format

**Simple** — return the same response regardless of params:
```json
{"days": [{"date": "2026-04-20", "dishes": [...]}]}
```

**Keyed** — return different responses based on a parameter:
```json
{
  "__key__": "canteen_id",
  "__default__": {"days": []},
  "mensa-garching": {"days": [...]},
  "mensa-arcisstr": {"days": [...]}
}
```

## Activating

Call the `set_demo_mode(enabled=true)` MCP tool. Call with `false` to go back to real APIs.
