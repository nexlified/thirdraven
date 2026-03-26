---
name: ThirdRaven testing conventions
description: Test file structure, fixture pattern, mock strategy, and naming conventions used across the ThirdRaven test suite
type: project
---

Testing framework: pytest (no pytest-asyncio in test files — sync TestClient only).

**Fixture pattern:**
- `app_client` fixture: creates a bare `FastAPI()`, includes the router under `/api/v1`, overrides both `get_session` (async generator yielding `AsyncMock()`) and `get_current_user` (returns `FAKE_USER`). Yields a `TestClient`. Calls `app.dependency_overrides.clear()` in teardown.
- `unauthed_client` fixture: same but omits `get_current_user` override, uses `TestClient(app, raise_server_exceptions=False)`.
- `FAKE_USER` is a `User` model instance with `datetime.utcnow()` for `created_at`.

**Mock strategy:**
- Use `unittest.mock.patch` as a context manager inside each test body (not as a decorator).
- Mock path always targets the router module: `app.api.v1.<module>.<crud_fn>`.
- Use `AsyncMock(return_value=...)` for CRUD functions.
- For `not found` cases: `return_value=None`.
- For delete `not found` cases: `return_value=None`; for success: `return_value=object()` (truthy sentinel).
- To verify query param forwarding: capture `mock_fn.call_args.kwargs` after the request.

**Factory functions:**
- `make_X(**kwargs)` pattern: build a `defaults` dict, call `defaults.update(kwargs)`, return schema instance.
- Use schema `Public` classes (Pydantic), not SQLModel table classes, for factory output.
- For schemas with `TermSlim` nested fields, create a module-level `SOME_TERM = TermSlim(...)` constant and reference it in factory defaults.

**File naming:** `tests/test_<router_module_name>.py` (mirrors `app/api/v1/<router_module_name>.py`).

**Why:** Consistent with all 10+ existing test files. The `utcnow()` deprecation warnings are present across the entire codebase and are acceptable noise.

**How to apply:** Follow this exact pattern for any new test file in this project.
