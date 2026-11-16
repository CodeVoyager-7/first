from __future__ import annotations

import os

import uvicorn


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))
    reload_default = app_env not in {"production", "prod"}
    reload_enabled = _env_bool("UVICORN_RELOAD", reload_default)
    uvicorn.run("webapp.server:app", host=host, port=port, reload=reload_enabled)
