from pydantic import BaseModel, Field
import os

class Settings(BaseModel):
    env: str = Field(default=os.getenv("ENV", "dev"))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "DEBUG"))
    # Updated service name to reflect the new project identity.
    service_name: str = "Terry Delmonaco Presents: AI"
    service_version: str = "1.0.0"
    otlp_endpoint: str = os.getenv("OTLP_ENDPOINT", "").strip()
    enable_traces: bool = Field(default=os.getenv("ENABLE_TRACES", "false").lower() == "true")

    # API key used to authenticate requests. If not set, authentication is disabled.
    api_key: str | None = Field(default=os.getenv("API_KEY"))

    # Optional path to a serialized model (e.g. joblib or pickle). If provided, the application
    # will attempt to load a trained model from this path instead of using built‑in coefficients.
    model_path: str | None = Field(default=os.getenv("MODEL_PATH"))

settings = Settings()
