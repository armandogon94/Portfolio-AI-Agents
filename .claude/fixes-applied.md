# Fixes Applied

## 2026-04-01: Fixed pyproject.toml invalid script entry points

**File:** `pyproject.toml`

**Problem:** `pip install -e ".[dev]"` failed with:
```
ERROR: Invalid script entry point: <ExportEntry chat = chainlit:None []>
- A callable suffix is required.
```

**Root cause:** The `[project.scripts]` section used shell command syntax instead of Python `module:callable` format:
```toml
# BROKEN
[project.scripts]
start = "uvicorn src.main:app --host 0.0.0.0 --port 8000"
dev = "uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
chat = "chainlit run src/chainlit_app.py --port 8001"
```

**Fix:** Removed the `[project.scripts]` section entirely and replaced with comments:
```toml
# Run commands directly:
#   uvicorn src.main:app --host 0.0.0.0 --port 8060 --reload
#   chainlit run src/chainlit_app.py --port 3060
```

**Status:** Fixed and verified — `pip install -e ".[dev]"` succeeds.
