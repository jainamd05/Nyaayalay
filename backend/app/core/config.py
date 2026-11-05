from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

LOCAL_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


def _normalise_origin(origin: str) -> str:
    # Browsers send the Origin header without a trailing slash or path, so a
    # FRONTEND_URL copied from the address bar ("https://x.vercel.app/") would
    # otherwise never match and every CORS preflight would fail.
    return origin.strip().rstrip("/")


class Settings(BaseSettings):
    app_name: str = "Nyayalay API"
    environment: str = "development"

    # One or more comma-separated frontend origins, e.g.
    # "https://nyaayalay.vercel.app,https://www.example.com"
    frontend_url: str = "http://localhost:5173"

    # Optional regex for extra allowed origins, e.g. Vercel preview deploys:
    # "https://nyaayalay-.*\.vercel\.app"
    frontend_url_regex: str = ""

    warmup_on_startup: bool = True

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        configured = [
            _normalise_origin(origin)
            for origin in self.frontend_url.split(",")
            if origin.strip()
        ]
        return list(dict.fromkeys(LOCAL_DEV_ORIGINS + configured))


settings = Settings()
