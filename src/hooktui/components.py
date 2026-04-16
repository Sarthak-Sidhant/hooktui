from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Label, Collapsible, RichLog, DataTable, Input, Switch, Button, TextArea
from textual.reactive import reactive
from hooktui.config import load_settings, save_settings, AppSettings

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
        yield ListView(
            ListItem(Label(" [b]⚙[/b] Info & Config", classes="config-nav-btn"), id="nav-config"),
            id="nav-list"
        )
        yield Label("  --- Requests ---", classes="sidebar-divider")
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

class InfoConfigView(VerticalScroll):
    """The new inline Configuration and Endpoint Info panel, replacing the modal."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = load_settings()

    def compose(self) -> ComposeResult:
        yield Label("  Configuration & Endpoints", id="config-title")
        
        # ── Section 1: Unique Endpoints ──
        with Collapsible(title="Your Unique Endpoints", collapsed=False, id="section-endpoints"):
            yield Vertical(
                Horizontal(Label(" HTTP", classes="meta-key"), Label(f"http://{self.settings.base_domain}/{self.settings.app_uuid}", classes="meta-val"), classes="meta-row"),
                Horizontal(Label(" Email", classes="meta-key"), Label(f"{self.settings.app_uuid}@{self.settings.email_domain}", classes="meta-val"), classes="meta-row"),
                Horizontal(Label(" DNS", classes="meta-key"), Label(f"{self.settings.app_uuid}.{self.settings.dns_domain}", classes="meta-val"), classes="meta-row"),
                id="meta-container",
            )
            
        # ── Section 2: Custom Domains ──
        with Collapsible(title="Custom Domains", collapsed=False, id="section-domains"):
            yield Label("Base Domain:", classes="config-label-top")
            yield Input(value=self.settings.base_domain, id="input-base-domain", classes="config-input")
            
            yield Label("Email Domain:", classes="config-label-top")
            yield Input(value=self.settings.email_domain, id="input-email-domain", classes="config-input")
            
            yield Label("DNS Domain:", classes="config-label-top")
            yield Input(value=self.settings.dns_domain, id="input-dns-domain", classes="config-input")

        # ── Section 3: HTTP Response Settings ──
        with Collapsible(title="HTTP Response Settings", collapsed=False, id="section-response"):
            yield Label("Status Code:", classes="config-label-top")
            yield Input(value=str(self.settings.response_code), type="integer", id="input-status", classes="config-input")
            
            yield Label("Content Type:", classes="config-label-top")
            yield Input(value=self.settings.response_content_type, id="input-ct", classes="config-input")
            
            yield Label("Response Body:", classes="config-label-top")
            yield TextArea(text=self.settings.response_body, language="json", id="input-body", classes="config-textarea")
            
        # ── Section 4: Module Listeners ──
        with Collapsible(title="Module Listeners (Requires Restart)", collapsed=False, id="section-modules"):
            with Horizontal(classes="config-row-toggle"):
                yield Label("DNS Sinkhole:", classes="config-label-toggle")
                yield Switch(value=self.settings.enable_dns, id="switch-dns")
                yield Label("Port:", classes="config-label-toggle")
                yield Input(value=str(self.settings.dns_port), type="integer", id="input-dns-port", classes="config-input-small")

            with Horizontal(classes="config-row-toggle"):
                yield Label("Email Inbox:", classes="config-label-toggle")
                yield Switch(value=self.settings.enable_email, id="switch-email")
                yield Label("Port:", classes="config-label-toggle")
                yield Input(value=str(self.settings.smtp_port), type="integer", id="input-smtp-port", classes="config-input-small")
        
        with Horizontal(id="config-buttons"):
            yield Button("Save Defaults", variant="success", id="btn-save")

    def on_mount(self) -> None:
        self.border_title = "Info & Config"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.save_settings_data()

    def save_settings_data(self) -> None:
        try:
            code = int(self.query_one("#input-status", Input).value)
        except ValueError:
            code = 200
            
        try:
            dns_port = int(self.query_one("#input-dns-port", Input).value)
        except ValueError:
            dns_port = 5333

        try:
            smtp_port = int(self.query_one("#input-smtp-port", Input).value)
        except ValueError:
            smtp_port = 2525
            
        new_settings = AppSettings(
            app_uuid=self.settings.app_uuid,
            base_domain=self.query_one("#input-base-domain", Input).value,
            dns_domain=self.query_one("#input-dns-domain", Input).value,
            email_domain=self.query_one("#input-email-domain", Input).value,
            response_code=code,
            response_content_type=self.query_one("#input-ct", Input).value,
            response_body=self.query_one("#input-body", TextArea).text,
            enable_dns=self.query_one("#switch-dns", Switch).value,
            dns_port=dns_port,
            enable_email=self.query_one("#switch-email", Switch).value,
            smtp_port=smtp_port,
        )
        save_settings(new_settings)
        self.settings = new_settings
        self.app.app_settings = new_settings
        self.app.notify("Settings saved! Restart to apply port/listener changes.", severity="success")
        
        # Fresh redraw of the layout text
        self.query_one("#section-endpoints", Collapsible).remove()
        self.mount(
            Collapsible(
                Vertical(
                    Horizontal(Label(" HTTP", classes="meta-key"), Label(f"http://{self.settings.base_domain}/{self.settings.app_uuid}", classes="meta-val"), classes="meta-row"),
                    Horizontal(Label(" Email", classes="meta-key"), Label(f"{self.settings.app_uuid}@{self.settings.email_domain}", classes="meta-val"), classes="meta-row"),
                    Horizontal(Label(" DNS", classes="meta-key"), Label(f"{self.settings.app_uuid}.{self.settings.dns_domain}", classes="meta-val"), classes="meta-row"),
                    id="meta-container",
                ),
                title="Your Unique Endpoints", collapsed=False, id="section-endpoints"
            ),
            after="#config-title"
        )
