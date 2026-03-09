"""HookTUI – a webhook.site TUI built with Textual."""

from textual.theme import Theme as TextualTheme

HOOKTUI_THEMES: dict[str, TextualTheme] = {
    "galaxy": TextualTheme(
        name="galaxy",
        primary="#00E5FF",
        secondary="#a684e8",
        warning="#FFD700",
        error="#FF4500",
        success="#00FA9A",
        accent="#B53471",
        background="#0A0A0F",
        surface="#13131A",
        panel="#1A1A24",
        dark=True,
        variables={
            "input-cursor-background": "#00E5FF",
            "footer-background": "transparent",
        },
    ),
    "nebula": TextualTheme(
        name="nebula",
        primary="#4A9CFF",
        secondary="#66D9EF",
        warning="#FFB454",
        error="#FF5555",
        success="#50FA7B",
        accent="#FF79C6",
        surface="#193549",
        panel="#1F4662",
        background="#0D2137",
        dark=True,
        variables={
            "input-selection-background": "#4A9CFF 35%",
        },
    ),
    "aurora": TextualTheme(
        name="aurora",
        primary="#45FFB3",
        secondary="#A1FCDF",
        accent="#DF7BFF",
        warning="#FFE156",
        error="#FF6B6B",
        success="#64FFDA",
        background="#0A1A2F",
        surface="#142942",
        panel="#1E3655",
        dark=True,
        variables={
            "input-cursor-background": "#45FFB3",
            "input-selection-background": "#45FFB3 35%",
            "footer-background": "transparent",
            "button-color-foreground": "#0A1A2F",
        },
    ),
    "monokai": TextualTheme(
        name="monokai",
        primary="#F92672",
        secondary="#66D9EF",
        warning="#E6DB74",
        error="#F92672",
        success="#A6E22E",
        accent="#AE81FF",
        background="#272822",
        surface="#3E3D32",
        panel="#49483E",
        dark=True,
        variables={
            "footer-background": "transparent",
        },
    ),
}
