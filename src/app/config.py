"""Configuration management using Pydantic settings."""
import os

os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from pydantic_settings import BaseSettings, SettingsConfigDict

try:  # pragma: no cover - defensive import to silence telemetry warnings
    from crewai.telemetry.telemetry import Telemetry  # type: ignore

    Telemetry.set_tracer = lambda self: None  # noqa: E731
except Exception:
    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Required API keys
    rapidapi_key: str = ""
    openai_api_key: str = ""
    
    # Optional API keys for future extensions
    news_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    
    # LoopNet API configuration
    loopnet_base_url: str = "https://loopnet-api.p.rapidapi.com"
    loopnet_host: str = "loopnet-api.p.rapidapi.com"
    
    # Retry configuration
    max_retries: int = 3
    retry_wait_min: int = 1
    retry_wait_max: int = 10
    
    # Agent weights for final scoring
    weight_investment: float = 0.30
    weight_location: float = 0.25
    weight_news: float = 0.10
    weight_vc_risk: float = 0.20
    weight_construction: float = 0.15
    
    # Output configuration
    output_dir: str = "./out"
    
    def get_weights(self) -> dict[str, float]:
        """Return agent weights as a dictionary."""
        return {
            "investment": self.weight_investment,
            "location": self.weight_location,
            "news": self.weight_news,
            "vc_risk": self.weight_vc_risk,
            "construction": self.weight_construction,
        }


# Global settings instance
settings = Settings()
