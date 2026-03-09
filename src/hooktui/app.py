import asyncio
import uvicorn
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, ListView, Label
from textual.containers import Horizontal

from hooktui.server import create_app
from hooktui.models import ServerConfig, WebhookReceived, WebhookRequest
from hooktui.components import Sidebar, RequestDetails, RequestListItem
from hooktui.themes import HOOKTUI_THEMES


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
            RequestDetails(id="main-panel"),
            id="app-body",
        )
        yield Footer()

    async def on_mount(self) -> None:
        for theme in HOOKTUI_THEMES.values():
            self.register_theme(theme)
        self.theme = "galaxy"

        fastapi_app = create_app(self)
        config = uvicorn.Config(
            app=fastapi_app,
            host=self.server_config.host,
            port=self.server_config.port,
            log_level="error",
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())

    # ── Webhook events ──

    def on_webhook_received(self, event: WebhookReceived) -> None:
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
        self._update_details(event.item)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item:
            self._update_details(event.item)

    def _update_details(self, item: RequestListItem) -> None:
        self.query_one("#main-panel", RequestDetails).current_request = item.request

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
