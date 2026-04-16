import asyncio
import uvicorn
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, ListView, Label, ContentSwitcher
from textual.containers import Horizontal

from hooktui.server import create_app
from hooktui.models import ServerConfig, WebhookReceived, WebhookRequest
from hooktui.components import Sidebar, RequestDetails, RequestListItem, InfoConfigView
from hooktui.themes import HOOKTUI_THEMES
from hooktui import db
from hooktui.config import load_settings
from hooktui.dns_server import start_dns_server
from hooktui.smtp_server import start_smtp_server
from typing import Any


class HookTUIApp(App):
    """webhook.site in your terminal."""

    TITLE = "HookTUI"
    SUB_TITLE = "Webhook Inspector"
    CSS_PATH = "theme.css"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j,down", "cursor_down", "↓", show=False),
        Binding("k,up", "cursor_up", "↑", show=False),
        Binding("g", "scroll_top", "Top", show=False),
        Binding("shift+g", "scroll_bottom", "Bottom", show=False),
        Binding("c", "clear_requests", "Clear"),
        Binding("d", "delete_selected", "Delete"),
        Binding("y", "copy_body", "Copy Body"),
        Binding("shift+y", "copy_url", "Copy URL"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("question_mark", "show_help", "Help"),
    ]

    def __init__(self, host: str = "127.0.0.1", port: int = 8080, **kwargs):
        super().__init__(**kwargs)
        self.server_config = ServerConfig(host=host, port=port)
        self._server_task: asyncio.Task | None = None
        self._requests: list[WebhookRequest] = []
        self._theme_names = list(HOOKTUI_THEMES.keys())
        self._theme_index = 0
        self.app_settings = load_settings()
        self._dns_transport: Any = None
        self._smtp_controller: Any = None

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label("[b]⚡ HookTUI[/b]", id="app-title"),
            Label("[dim]webhook.site for your terminal[/dim]", id="app-subtitle"),
            id="app-header",
        )
        yield Label(
            f"  ● http://{self.server_config.host}:{self.server_config.port}/",
            id="listen-bar",
        )
        yield Horizontal(
            Sidebar(id="sidebar"),
            ContentSwitcher(
                RequestDetails(id="request-details"),
                InfoConfigView(id="info-config"),
                id="main-panel",
                initial="request-details",
            ),
            id="app-body",
        )
        yield Footer()

    async def on_mount(self) -> None:
        db.init_db()
        self._requests = db.get_all_requests()

        lv = self.query_one("#request-list", ListView)
        for req in self._requests:
            lv.append(RequestListItem(req))
        self.query_one("#sidebar", Sidebar).update_count(len(self._requests))
        if self._requests:
            try:
                self.query_one("#empty-label").display = False
            except Exception:
                pass

        for theme in HOOKTUI_THEMES.values():
            self.register_theme(theme)
        self.theme = "galaxy"

        if self.app_settings.enable_dns:
            try:
                self._dns_transport = await start_dns_server(self, port=self.app_settings.dns_port)
                self.notify(f"DNS Sinkhole listening on :{self.app_settings.dns_port}", severity="information")
            except Exception as e:
                self.notify(f"DNS Server failed: {e}", severity="error")
                
        if self.app_settings.enable_email:
            try:
                self._smtp_controller = await start_smtp_server(self, port=self.app_settings.smtp_port)
                self.notify(f"SMTP Inbox listening on :{self.app_settings.smtp_port}", severity="information")
            except Exception as e:
                self.notify(f"SMTP Server failed: {e}", severity="error")

        fastapi_app = create_app(self)
        config = uvicorn.Config(
            app=fastapi_app,
            host=self.server_config.host,
            port=self.server_config.port,
            log_level="error",
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())

    async def on_unmount(self) -> None:
        if getattr(self, "_dns_transport", None):
            self._dns_transport.close()
        if getattr(self, "_smtp_controller", None):
            self._smtp_controller.stop()

    # ── Webhook events ──

    def on_webhook_received(self, event: WebhookReceived) -> None:
        db.save_request(event.request)
        self._requests.append(event.request)
        lv = self.query_one("#request-list", ListView)
        item = RequestListItem(event.request)
        lv.append(item)
        lv.index = len(lv) - 1
        self._update_details(item)
        self.query_one("#sidebar", Sidebar).update_count(len(self._requests))
        try:
            self.query_one("#empty-label").display = False
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "nav-list":
            # Pressed the "Info & Config" button
            self.query_one("#main-panel", ContentSwitcher).current = "info-config"
            # Deselect the main request list if any was active
            self.query_one("#request-list", ListView).index = None
        elif event.list_view.id == "request-list":
            self._update_details(event.item)
            self.query_one("#main-panel", ContentSwitcher).current = "request-details"
            self.query_one("#nav-list", ListView).index = None

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "nav-list" and event.item:
            self.query_one("#main-panel", ContentSwitcher).current = "info-config"
        elif event.list_view.id == "request-list" and event.item:
            self._update_details(event.item)
            self.query_one("#main-panel", ContentSwitcher).current = "request-details"

    def _update_details(self, item: RequestListItem) -> None:
        self.query_one("#request-details", RequestDetails).current_request = item.request

    # ── Navigation ──

    def action_cursor_down(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if lv.index is not None and lv.index < len(lv) - 1:
            lv.index += 1

    def action_cursor_up(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if lv.index is not None and lv.index > 0:
            lv.index -= 1

    def action_scroll_top(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if len(lv):
            lv.index = 0

    def action_scroll_bottom(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if len(lv):
            lv.index = len(lv) - 1

    # ── Data actions ──

    def action_clear_requests(self) -> None:
        db.clear_requests()
        self._requests.clear()
        lv = self.query_one("#request-list", ListView)
        lv.clear()
        self.query_one("#sidebar", Sidebar).update_count(0)
        try:
            self.query_one("#empty-label").display = True
            self.query_one("#placeholder").display = True
        except Exception:
            pass
        self.notify("Cleared", severity="information")

    def action_delete_selected(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self._requests):
            req_id = self._requests[lv.index].id
            db.delete_request(req_id)
            self._requests.pop(lv.index)
            lv.pop(lv.index)
            self.query_one("#sidebar", Sidebar).update_count(len(self._requests))
            if len(lv) > 0:
                lv.index = min(lv.index, len(lv) - 1)
            else:
                try:
                    self.query_one("#empty-label").display = True
                except Exception:
                    pass

    def action_copy_body(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self._requests):
            self.copy_to_clipboard(self._requests[lv.index].body or "")
            self.notify("Body copied", severity="information")

    def action_copy_url(self) -> None:
        lv = self.query_one("#request-list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self._requests):
            self.copy_to_clipboard(self._requests[lv.index].url)
            self.notify("URL copied", severity="information")

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._theme_names)
        name = self._theme_names[self._theme_index]
        self.theme = name
        self.notify(f"Theme: {name}", severity="information")

    def action_show_help(self) -> None:
        self.notify(
            "[b]j/↓[/b] Down  [b]k/↑[/b] Up  [b]g[/b] Top  [b]G[/b] Bottom\n"
            "[b]d[/b] Delete  [b]c[/b] Clear  [b]y[/b] Copy body  [b]Y[/b] Copy URL\n"
            "[b]t[/b] Theme  [b]q[/b] Quit  [b]?[/b] Help",
            severity="information",
            timeout=10,
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HookTUI — webhook.site in your terminal")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    args = parser.parse_args()
    HookTUIApp(host=args.host, port=args.port).run()


if __name__ == "__main__":
    main()
