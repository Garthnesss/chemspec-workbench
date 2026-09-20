#!/usr/bin/env python3
"""Capture ChemSpec NiceGUI UI screenshot (public ethanol IR).

Requires: ``pip install -e ".[ui]"``, selenium, and google-chrome/chromium.
Honesty: screenshot is the analysis UI only — not compound identification.

NiceGUI needs a real ``.py`` launcher file (``python -c`` breaks script mode).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "screenshots" / "chemspec-ethanol-ir.png"


def _wait_http(url: str, timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.5)
    raise RuntimeError(f"UI not ready at {url}: {last_err}")


def capture(*, port: int, out: Path, button_label: str) -> Path:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    url = f"http://127.0.0.1:{port}"
    _wait_http(url)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--force-device-scale-factor=1")

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 40)
        # Prefer exact button text match among button-like elements
        btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//button[contains(normalize-space(.), '{button_label}')]"
                    f" | //*[self::div or self::span]"
                    f"[contains(@class,'q-btn')]"
                    f"[contains(normalize-space(.), '{button_label}')]",
                )
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", btn
        )
        time.sleep(0.3)
        btn.click()
        # Wait for Plotly canvas / svg after fixture load
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".js-plotly-plot .plotly, .js-plotly-plot svg")
            )
        )
        time.sleep(2.0)
        # Scroll to top so header + plot + status are in frame
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        # Prefer a plot-centered crop via full page height resize
        total_h = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
        )
        total_w = driver.execute_script(
            "return Math.max(document.body.scrollWidth, 1400);"
        )
        driver.set_window_size(min(int(total_w), 1600), min(int(total_h), 2200))
        time.sleep(0.8)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.4)
        out.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(out))
    finally:
        driver.quit()
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--button",
        default="Load public: Ethanol IR",
        help="UI button label to click before capture",
    )
    parser.add_argument(
        "--external-server",
        action="store_true",
        help="Do not spawn ui_app (already running on --port)",
    )
    args = parser.parse_args(argv)

    proc: subprocess.Popen | None = None
    launcher: Path | None = None
    try:
        if not args.external_server:
            # Keep under /tmp root — not /tmp/pr39-sandbox
            launcher = Path(tempfile.gettempdir()) / f"chemspec_ui_capture_{args.port}.py"
            launcher.write_text(
                "from chemspec.ui_app import create_app\n"
                "from nicegui import ui\n"
                "create_app()\n"
                "ui.run(title='ChemSpec Workbench', reload=False, show=False, "
                f"port={args.port}, host='127.0.0.1')\n",
                encoding="utf-8",
            )
            proc = subprocess.Popen(
                [sys.executable, str(launcher)],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        path = capture(port=args.port, out=args.out, button_label=args.button)
        print(f"wrote {path} ({path.stat().st_size} bytes)")
        return 0
    except Exception as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        if proc is not None and proc.stdout is not None:
            try:
                chunk = proc.stdout.read(4000)
                if chunk:
                    print(chunk.decode("utf-8", errors="replace"), file=sys.stderr)
            except Exception:
                pass
        return 1
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        if launcher is not None and launcher.is_file():
            try:
                launcher.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
