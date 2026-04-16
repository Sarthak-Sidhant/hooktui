import uuid
from typing import Any
from fastapi import FastAPI, Request, Response
from textual.app import App as TextualApp
from hooktui.models import WebhookRequest

def create_app(tui_app: TextualApp) -> FastAPI:
    app = FastAPI(title="HookTUI Server", version="0.1.0")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"])
    async def catch_all(request: Request, path: str) -> Any:
        try:
            body = (await request.body()).decode("utf-8")
        except Exception:
            body = "<binary or non-utf8 data>"

        webhook_req = WebhookRequest(
            id=str(uuid.uuid4()),
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            body=body,
            client_ip=request.client.host if request.client else None
        )
        
        from hooktui.models import WebhookReceived
        tui_app.post_message(WebhookReceived(request=webhook_req))

        settings = getattr(tui_app, "app_settings", None)
        if settings:
            return Response(
                content=settings.response_body,
                status_code=settings.response_code,
                media_type=settings.response_content_type,
            )
        return {"status": "ok", "message": "Webhook received by HookTUI."}

    return app
