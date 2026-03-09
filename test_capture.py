"""
Headless test: start HookTUI, send webhooks, capture SVG screenshot.
"""
import asyncio, os

os.environ["TEXTUAL_HEADLESS"] = "1"

from hooktui.app import HookTUIApp

ARTIFACT_DIR = "/home/sidhant/.gemini/antigravity/brain/7e51e8f4-11f2-4dda-b281-36a4fd5b0911"


async def run_test():
    app = HookTUIApp(host="127.0.0.1", port=9123)

    async with app.run_test(size=(160, 42)) as pilot:
        await asyncio.sleep(2.0)

        import httpx

        async with httpx.AsyncClient(timeout=5) as client:
            await client.get("http://127.0.0.1:9123/api/healthcheck?source=tui&v=2")
            await asyncio.sleep(0.2)

            await client.post(
                "http://127.0.0.1:9123/stripe/webhook",
                json={
                    "type": "payment_intent.succeeded",
                    "data": {"object": {"id": "pi_3abc", "amount": 4200, "currency": "usd"}},
                },
            )
            await asyncio.sleep(0.2)

            await client.put(
                "http://127.0.0.1:9123/users/42",
                headers={"Authorization": "Bearer tok_live_xyz", "Content-Type": "application/x-www-form-urlencoded"},
                content="name=Sidhant&role=admin",
            )
            await asyncio.sleep(0.2)

            await client.delete("http://127.0.0.1:9123/cache/stale-key")
            await asyncio.sleep(0.2)

            await client.patch(
                "http://127.0.0.1:9123/settings/theme",
                json={"theme": "galaxy", "dark_mode": True},
            )
            await asyncio.sleep(0.5)

        svg = app.export_screenshot(title="HookTUI")
        path = os.path.join(ARTIFACT_DIR, "hooktui_screenshot.svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"Screenshot saved → {path}")


if __name__ == "__main__":
    asyncio.run(run_test())
