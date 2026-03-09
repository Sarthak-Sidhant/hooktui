from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from textual.message import Message

class WebhookRequest(BaseModel):
    id: str
    method: str
    url: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    client_ip: Optional[str] = None

class WebhookReceived(Message):
    """Event fired when the server receives a new webhook."""
    def __init__(self, request: WebhookRequest) -> None:
        self.request = request
        super().__init__()

class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080
