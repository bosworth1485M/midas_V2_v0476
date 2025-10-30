# Addendum – Refresh Docs Script Corrections (v0.3.18)

## Context
We switched from using `Docs/Refresh-Docs.ps1` to maintaining the **Python script** `Docs/refresh_docs.py` as the canonical way to regenerate project documentation.

## Corrections Made
- **Naming:** standardized on `refresh_docs.py` (lowercase, underscore) instead of `Refresh-Docs.ps1`.
- **Invocation:**
  - Preferred:
    ```
    python .\Docs\refresh_docs.py
    ```
  - PowerShell version still exists but considered legacy.
- **Functionality updates:**
  - Confirmed it regenerates `Docs/DEV_GUIDE.md` (and auto-injects guides like `USER_GUIDE.md` if configured).
  - Script was patched to:
    - Use repo-relative paths (no need for `--root .`).
    - Work cleanly in Python 3.13 environment.
    - Avoid stale outputs by overwriting existing guide files.

## Decisions
- **Python script is now canonical.**
- **PowerShell script kept optional** for Windows-only helpers, but not the primary method.
- All future documentation updates and tagged versions will use the **Python refresh command**.

## Next Steps
- Always run:
  ```
  python .\Docs\refresh_docs.py
  ```
  before committing + tagging a new version.
- Optional: remove `Refresh-Docs.ps1` in a later cleanup version (e.g., v0.3.20) once confident Python script covers all use cases.
