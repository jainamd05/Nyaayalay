from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nyayalay API"
    environment: str = "development"
    # One URL or a comma-separated list, e.g. "https://nyayalay.vercel.app".
    frontend_url: str = "http://localhost:5173"
    cors_origin_regex: str = r"https://.*\.vercel\.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        origins = {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",  # vite preview
            "http://127.0.0.1:4173",
        }
        for url in self.frontend_url.split(","):
            # Browsers send the Origin without a trailing slash.
            url = url.strip().rstrip("/")
            if url:
                origins.add(url)
        return sorted(origins)


settings = Settings()
