import json
import os
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path("evidence")
base = "http://127.0.0.1:19382"
for _ in range(20):
    try:
        with urllib.request.urlopen(base + "/json/version", timeout=1) as r:
            if r.status == 200:
                break
    except OSError:
        pass
    time.sleep(1)
else:
    from native_picker import check_native_picker
    check_native_picker(out)
    raise SystemExit(0)

with sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp(base)
    deadline = time.monotonic() + 75
    page = None
    while time.monotonic() < deadline and page is None:
        for context in browser.contexts:
            for tab in context.pages:
                if "tauri.localhost" in tab.url and "capsule" not in tab.url and tab.locator("#root").count():
                    page = tab
                    break
        if page is None:
            time.sleep(0.5)
    if page is None:
        raise RuntimeError(f"No Lumen application WebView in {[p.url for c in browser.contexts for p in c.pages]}")
    try:
        close = page.get_by_role("button", name="关闭设置", exact=True)
        settings = page.get_by_role("button", name="设置", exact=True)
        pick = page.get_by_role("button", name="下载 Oruk Fourier 2B 英语模型", exact=True)
        for _ in range(45):
            if pick.is_visible():
                break
            if close.is_visible():
                close.click()
            elif settings.is_visible() and not page.locator("nav.settings-tabs").is_visible():
                settings.click()
            page.wait_for_timeout(500)
        pick.click(timeout=15000)
        folder = Path(os.environ["LUMEN_MODELS_DIR"]) / "oruk-fourier-2b-sherpa-int8"
        candidates = [Path(os.environ[k]) / "LumenAsr" / "config.toml" for k in ("LOCALAPPDATA", "APPDATA")]
        deadline = time.monotonic() + 480
        while time.monotonic() < deadline:
            files = [f for f in folder.rglob("*") if f.is_file()]
            size = sum(f.stat().st_size for f in files)
            saved = next((f for f in candidates if f.exists() and folder.name in f.read_text(encoding="utf-8") and "local_qwen" in f.read_text(encoding="utf-8")), None)
            if saved and size == 2409908809 and len(files) == 10:
                break
            page.wait_for_timeout(1000)
        else:
            raise RuntimeError(f"Install incomplete: {len(files)} files, {size} bytes; saved config: {saved}")
        result = {"desktop": os.environ["DESKTOP_REV"], "platform": "Windows x64", "install": "NSIS current user", "interaction": "production WebView button click", "selected": folder.name, "files": len(files), "bytes": size, "saved_engine": "local_qwen", "installer_sha256": Path("package/SHA256SUMS").read_text().split()[0]}
        print(json.dumps(result))
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    finally:
        (out / "window.txt").write_text(page.locator("body").inner_text(), encoding="utf-8")
        page.screenshot(path=str(out / "window.png"), timeout=5000)
