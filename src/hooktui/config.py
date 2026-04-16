import json
from pathlib import Path
from pydantic import BaseModel, Field
import uuid
from hooktui.db import get_db_path

def get_settings_path() -> Path:
    config_dir = Path.home() / ".config" / "hooktui"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"

def generate_uuid() -> str:
    return str(uuid.uuid4())

class AppSettings(BaseModel):
    # UUID & Domain Config
    app_uuid: str = Field(default_factory=generate_uuid)
    base_domain: str = "localhost:8080"
    dns_domain: str = "dns.localhost"
    email_domain: str = "email.localhost"
    
    # HTTP Endpoint Config
    http_listen_path: str = "/"
    response_code: int = 200
    response_content_type: str = "application/json"
    response_body: str = '{"status": "ok", "message": "Webhook received by HookTUI."}'
    
    # Feature toggles
    enable_dns: bool = False
    dns_port: int = 5333
    enable_email: bool = False
    smtp_port: int = 2525

def load_settings() -> AppSettings:
    p = get_settings_path()
    if p.exists():
        try:
            return AppSettings.model_validate_json(p.read_text("utf-8"))
        except Exception:
            pass
    return AppSettings()

def save_settings(settings: AppSettings) -> None:
    p = get_settings_path()
    p.write_text(settings.model_dump_json(indent=4), "utf-8")
