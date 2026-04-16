# HookTUI ⚡

**webhook.site in your terminal.**

HookTUI is a sleek, modern Terminal User Interface (TUI) for inspecting webhooks, DNS queries, and SMTP traffic. Built with [Textual](https://textual.textualize.io/), it provides a real-time stream of incoming requests with detailed inspection of headers, query parameters, and bodies.

![HookTUI Screenshot](https://raw.githubusercontent.com/Sarthak-Sidhant/hooktui/main/screenshot.png) *(Note: Replace with actual screenshot link after push)*

## Features

- 🚀 **HTTP Webhook Inspector**: Capture and inspect GET, POST, PUT, DELETE, and more.
- 📬 **Embedded SMTP Server**: Test email sending by pointing your SMTP client to HookTUI.
- 🌍 **Embedded DNS Server**: A DNS sinkhole to inspect DNS lookups in real-time.
- 🎨 **Beautiful Themes**: Multiple built-in themes (Galaxy, Nebula, Aurora, Monokai).
- 💾 **Persistent History**: All requests are saved to a local SQLite database and persist across sessions.
- 📋 **Clipboard Support**: Easily copy request bodies or full URLs.
- ⌨️ **Vim-like Keybindings**: Navigate quickly with `j`/`k` and other familiar shortcuts.

## Installation

You can install HookTUI via pip:

```bash
pip install hooktui
```

Or using [uv](https://github.com/astral-sh/uv):

```bash
uv tool install hooktui
```

## Quick Start

Simply run `hooktui` to start the server and the TUI:

```bash
hooktui
```

By default, the HTTP server listens on `http://127.0.0.1:8080`.

### CLI Options

```bash
hooktui --host 0.0.0.0 --port 9000
```

## Keybindings

| Key | Action |
|-----|--------|
| `q` | Quit HookTUI |
| `j` / `↓` | Select Next Request |
| `k` / `↑` | Select Previous Request |
| `c` | Clear all requests |
| `d` | Delete selected request |
| `y` | Copy request body |
| `Y` | Copy request URL |
| `t` | Cycle themes |
| `?` | Show help |

## Configuration

Settings are stored in `~/.config/hooktui/settings.json`. You can enable/disable DNS and SMTP servers and change their ports through this file or the in-app config view (coming soon).

---

Built with ❤️ by [Sarthak Sidhant](https://github.com/Sarthak-Sidhant)
