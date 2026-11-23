import json
import os
import time
from pathlib import Path
from PIL import ImageGrab
from pywinauto import Desktop


def check_native_picker(out):
    desktop = Desktop(backend="uia")
    title = "下载 Oruk Fourier 2B 英语模型"
    folder = Path(os.environ["LUMEN_MODELS_DIR"]) / "oruk-fourier-2b-sherpa-int8"
    candidates = [Path(os.environ[k]) / "LumenAsr" / "config.toml" for k in ("LOCALAPPDATA", "APPDATA")]
    clicked = False
    log = out / "windows-accessibility.txt"
    deadline = time.monotonic() + 90
    try:
        while time.monotonic() < deadline and not clicked:
            windows = desktop.windows()
            with log.open("a", encoding="utf-8") as fp:
                print([(w.handle, w.window_text()) for w in windows], file=fp)
            for window in windows:
                if "lumen" not in window.window_text().lower():
                    continue
                controls = window.descendants(control_type="Button")
                with log.open("a", encoding="utf-8") as fp:
                    print([w.window_text() for w in controls][:100], file=fp)
                visible = {b.window_text(): b for b in controls if b.is_visible() and b.is_enabled()}
                for name in (title, "关闭设置", "设置"):
                    if name in visible:
                        visible[name].invoke()
                        clicked = name == title
                        break
                if clicked:
                    break
            time.sleep(1)
        if not clicked:
            raise RuntimeError("No Fourier install action was available in the installed app's accessibility tree")
        deadline = time.monotonic() + 480
        while time.monotonic() < deadline:
            files = [f for f in folder.rglob("*") if f.is_file()]
            size = sum(f.stat().st_size for f in files)
            saved = any(f.exists() and folder.name in f.read_text(encoding="utf-8") and "local_qwen" in f.read_text(encoding="utf-8") for f in candidates)
            if saved and size == 2409908809 and len(files) == 10:
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"Install incomplete: {len(files)} files, {size} bytes; saved config: {saved}")
        result = {"desktop": os.environ["DESKTOP_REV"], "platform": "Windows x64", "install": "NSIS current user", "interaction": "production Windows accessibility button", "selected": folder.name, "files": len(files), "bytes": size, "saved_engine": "local_qwen", "installer_sha256": Path("package/SHA256SUMS").read_text().split()[0]}
        print(json.dumps(result))
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    finally:
        ImageGrab.grab(all_screens=True).save(out / "native-window.png")
