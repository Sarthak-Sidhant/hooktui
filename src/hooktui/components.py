from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Label, Collapsible, RichLog, DataTable
from textual.reactive import reactive

from hooktui.models import WebhookRequest
import json
from urllib.parse import urlparse, parse_qs


class RequestListItem(ListItem):
    """Sidebar entry — matches webhook.site: METHOD #shortID IP / date."""

    def __init__(self, request: WebhookRequest, **kwargs):
        super().__init__(**kwargs)
        self.request = request

    def compose(self) -> ComposeResult:
        method = self.request.method
        short_id = f"#{self.request.id[:5]}"
        ip = self.request.client_ip or "127.0.0.1"
        ts = self.request.timestamp.strftime("%m/%d/%Y %H:%M:%S")
        yield Vertical(
            Horizontal(
                Label(f" {method} ", classes=f"method-badge method-{method}"),
                Label(f" {short_id} {ip}", classes="req-id-ip"),
            ),
            Label(f" {ts}", classes="req-date"),
            classes="req-item-inner",
        )


class Sidebar(Vertical):
    """Left sidebar — request list with counter."""

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label(" INBOX", id="inbox-label"),
            Label("(0)", id="inbox-count"),
            id="inbox-header",
        )
        yield ListView(id="request-list")
        yield Label("  Waiting for webhooks…", id="empty-label")

    def update_count(self, count: int) -> None:
        self.query_one("#inbox-count", Label).update(f"({count})")

    def on_mount(self) -> None:
        self.border_title = "Collection"


class RequestDetails(VerticalScroll):
    """Main panel — webhook.site style single scrollable view with sections."""

    current_request: reactive[WebhookRequest | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Label("  Select a request to view details", id="placeholder")

        # ── Section 1: Request Details ──
        with Collapsible(title="Request Details", collapsed=False, id="section-details"):
            # URL row
            yield Horizontal(
                Label("", id="detail-method-badge"),
                Label("", id="detail-url"),
                id="url-row",
            )
            yield Vertical(
                Horizontal(Label(" Host", classes="meta-key"), Label("", id="meta-host", classes="meta-val"), classes="meta-row"),
                Horizontal(Label(" Date", classes="meta-key"), Label("", id="meta-date", classes="meta-val"), classes="meta-row"),
                Horizontal(Label(" Size", classes="meta-key"), Label("", id="meta-size", classes="meta-val"), classes="meta-row"),
                Horizontal(Label(" ID", classes="meta-key"), Label("", id="meta-id", classes="meta-val"), classes="meta-row"),
                id="meta-container",
            )

        # ── Section 2: Headers ──
        with Collapsible(title="Headers", collapsed=False, id="section-headers"):
            yield DataTable(id="headers-table")

        # ── Section 3: Query Strings ──
        with Collapsible(title="Query Strings", collapsed=False, id="section-query"):
            yield DataTable(id="query-table")

        # ── Section 3: Request Content ──
        with Collapsible(title="Request Content", collapsed=False, id="section-content"):
            yield Horizontal(
                Label(" Raw Content", classes="content-label"),
                Label("  Copy", id="copy-btn", classes="copy-btn"),
                id="content-header",
            )
            yield RichLog(id="body-content", highlight=True, markup=True)

    def on_mount(self) -> None:
        self.border_title = "Request"
        
        ht = self.query_one("#headers-table", DataTable)
        ht.add_columns("Name", "Value")
        ht.cursor_type = "row"
        ht.show_header = True

        qt = self.query_table = self.query_one("#query-table", DataTable)
        qt.add_columns("Name", "Value")
        qt.cursor_type = "row"
        qt.show_header = True

    def watch_current_request(self, request: WebhookRequest | None) -> None:
        if request is None:
            return

        # Hide placeholder
        try:
            self.query_one("#placeholder").display = False
        except Exception:
            pass

        # Show sections
        for sid in ("#section-details", "#section-headers", "#section-query", "#section-content"):
            try:
                self.query_one(sid).display = True
            except Exception:
                pass

        # ── URL row ──
        method_label = self.query_one("#detail-method-badge", Label)
        method_label.update(f" {request.method} ")
        method_label.set_classes(f"method-badge method-{request.method}")

        self.query_one("#detail-url", Label).update(f"  {request.url}")

        # ── Left column: metadata ──
        parsed = urlparse(request.url)
        self.query_one("#meta-host", Label).update(f"  {parsed.hostname or 'localhost'}")
        ts = request.timestamp.strftime("%m/%d/%Y %H:%M:%S")
        self.query_one("#meta-date", Label).update(f"  {ts}")

        body_size = len(request.body.encode("utf-8")) if request.body else 0
        self.query_one("#meta-size", Label).update(f"  {body_size} bytes")
        self.query_one("#meta-id", Label).update(f"  {request.id[:36]}")

        # ── Headers ──
        ht = self.query_one("#headers-table", DataTable)
        ht.clear()
        if request.headers:
            for k, v in request.headers.items():
                ht.add_row(k, v)

        # ── Query strings ──
        qt = self.query_one("#query-table", DataTable)
        qt.clear()
        if request.query_params:
            for k, v in request.query_params.items():
                qt.add_row(k, v)
        else:
            qt.add_row("None", "")

        # ── Body content ──
        body_log = self.query_one("#body-content", RichLog)
        body_log.clear()
        if request.body:
            try:
                parsed_json = json.loads(request.body)
                body_log.write(json.dumps(parsed_json, indent=2))
            except (json.JSONDecodeError, ValueError):
                body_log.write(request.body)
        else:
            body_log.write("(empty body)")
