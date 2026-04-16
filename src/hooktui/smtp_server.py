import uuid
import logging
from email import message_from_bytes
from aiosmtpd.controller import Controller
from hooktui.models import WebhookRequest, WebhookReceived

class HookTUIHandler:
    def __init__(self, tui_app):
        self.tui_app = tui_app

    async def handle_DATA(self, server, session, envelope):
        try:
            msg = message_from_bytes(envelope.content)
            headers = {k: v for k, v in msg.items()}
            
            payload = msg.get_payload(decode=True)
            if payload is None:
                body = msg.as_string()
            else:
                body = payload.decode('utf-8', errors='replace')
                
            webhook_req = WebhookRequest(
                id=str(uuid.uuid4()),
                method="SMTP",
                url=f"mailto:{envelope.rcpt_tos[0]}" if envelope.rcpt_tos else "mailto:unknown",
                headers=headers,
                query_params={"mail_from": envelope.mail_from},
                body=body,
                client_ip=session.peer[0] if session.peer else None
            )
            self.tui_app.post_message(WebhookReceived(request=webhook_req))
        except Exception as e:
            logging.error(f"SMTP parse error: {e}")
            
        return '250 Message accepted for delivery'

async def start_smtp_server(tui_app, host="0.0.0.0", port=2525):
    handler = HookTUIHandler(tui_app)
    controller = Controller(handler, hostname=host, port=port)
    controller.start()
    return controller
