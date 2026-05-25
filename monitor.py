#!/usr/bin/env python3
# ============================================================
#   W E B M O N I T O R  —  by Claude  |  v2.0 ELITE
#   Auto Refresh & URL Monitor  |  24/7 Termux Edition
# ============================================================

import sys
import os
import time
import socket
import ssl
import json
import signal
import threading
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Dependency check & auto-install ──────────────────────────
REQUIRED = ["requests", "bs4", "rich"]

def auto_install():
    import subprocess
    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        pip_names = {"bs4": "beautifulsoup4"}
        install_names = [pip_names.get(p, p) for p in missing]
        print(f"\033[93m[AUTO-INSTALL] Installing: {', '.join(install_names)}\033[0m")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + install_names
        )
        print("\033[92m[AUTO-INSTALL] Done! Restarting...\033[0m\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

auto_install()

# ── Imports (after install) ───────────────────────────────────
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.style import Style
from rich.rule import Rule
from rich.align import Align

console = Console()

# ── Color Palette ─────────────────────────────────────────────
C = {
    "cyan":    "bold cyan",
    "green":   "bold green",
    "red":     "bold red",
    "yellow":  "bold yellow",
    "magenta": "bold magenta",
    "white":   "bold white",
    "dim":     "dim white",
    "blue":    "bold blue",
    "orange":  "bold dark_orange",
}

# ── Global State ──────────────────────────────────────────────
stop_event   = threading.Event()
log_lock     = threading.Lock()
stats        = {}          # url -> dict
log_file     = None
LOG_PATH     = f"webmonitor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# ── Signal handler ────────────────────────────────────────────
def handle_exit(sig, frame):
    stop_event.set()

signal.signal(signal.SIGINT,  handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# ─────────────────────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────────────────────
BANNER = r"""
 ██╗    ██╗███████╗██████╗ ███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗ 
 ██║    ██║██╔════╝██╔══██╗████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗
 ██║ █╗ ██║█████╗  ██████╔╝██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝
 ██║███╗██║██╔══╝  ██╔══██╗██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗
 ╚███╔███╔╝███████╗██████╔╝██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║
  ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
"""

def show_banner():
    console.print()
    console.print(Text(BANNER, style="bold cyan"), justify="center")
    console.print(
        Align.center(
            Text("◆  24/7 Website Monitor & Auto-Refresh  ◆  Termux Edition  ◆", style="bold magenta")
        )
    )
    console.print(
        Align.center(
            Text("Press  Ctrl+C  to stop gracefully", style="dim white")
        )
    )
    console.print()

# ─────────────────────────────────────────────────────────────
#  LOG
# ─────────────────────────────────────────────────────────────
def log(msg: str):
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with log_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)

# ─────────────────────────────────────────────────────────────
#  SSL INFO
# ─────────────────────────────────────────────────────────────
def get_ssl_info(hostname: str) -> dict:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.create_connection((hostname, 443), timeout=5),
                             server_hostname=hostname) as s:
            cert = s.getpeercert()
            not_after  = cert.get("notAfter",  "N/A")
            not_before = cert.get("notBefore", "N/A")
            issuer     = dict(x[0] for x in cert.get("issuer", []))
            subject    = dict(x[0] for x in cert.get("subject", []))
            try:
                exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                days_left = (exp - datetime.utcnow()).days
            except Exception:
                days_left = -1
            return {
                "valid":      True,
                "issuer":     issuer.get("organizationName", issuer.get("commonName", "N/A")),
                "subject":    subject.get("commonName", "N/A"),
                "not_before": not_before,
                "not_after":  not_after,
                "days_left":  days_left,
            }
    except Exception as e:
        return {"valid": False, "error": str(e)}

# ─────────────────────────────────────────────────────────────
#  IP RESOLVE
# ─────────────────────────────────────────────────────────────
def resolve_ip(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return "N/A"

# ─────────────────────────────────────────────────────────────
#  SINGLE CHECK
# ─────────────────────────────────────────────────────────────
def check_url(url: str, timeout: int = 10) -> dict:
    parsed   = urllib.parse.urlparse(url)
    hostname = parsed.netloc or parsed.path
    result   = {
        "url":          url,
        "status_code":  None,
        "status_text":  "N/A",
        "page_title":   "N/A",
        "meta_desc":    "N/A",
        "server":       "N/A",
        "response_ms":  None,
        "checked_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip":           resolve_ip(hostname),
        "ssl":          {},
        "headers":      {},
        "error":        None,
        "is_up":        False,
    }
    try:
        t0 = time.perf_counter()
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "WebMonitor/2.0 (Termux; Python)"},
            allow_redirects=True,
            verify=True,
        )
        elapsed = (time.perf_counter() - t0) * 1000

        result["status_code"] = resp.status_code
        result["status_text"] = resp.reason or "OK"
        result["response_ms"] = round(elapsed, 2)
        result["headers"]     = dict(resp.headers)
        result["server"]      = resp.headers.get("Server", "N/A")
        result["is_up"]       = resp.status_code < 400

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            title_tag = soup.find("title")
            result["page_title"] = title_tag.get_text(strip=True)[:100] if title_tag else "N/A"
            meta = soup.find("meta", attrs={"name": lambda n: n and n.lower() == "description"})
            if meta:
                result["meta_desc"] = (meta.get("content") or "N/A")[:150]
        except Exception:
            pass

        if parsed.scheme == "https":
            result["ssl"] = get_ssl_info(hostname)

    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection Error: {e}"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL Error: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result

# ─────────────────────────────────────────────────────────────
#  RENDER — single result panel
# ─────────────────────────────────────────────────────────────
STATUS_COLOR = {
    range(100, 200): "bold cyan",
    range(200, 300): "bold green",
    range(300, 400): "bold yellow",
    range(400, 500): "bold red",
    range(500, 600): "bold magenta",
}

def status_style(code):
    if code is None:
        return "bold red"
    for rng, style in STATUS_COLOR.items():
        if code in rng:
            return style
    return "bold white"

def speed_bar(ms) -> str:
    if ms is None:
        return "[red]●●●●●[/red] N/A"
    bars = min(int(ms / 200), 5)
    colors = ["green", "green", "yellow", "yellow", "red"]
    filled = "".join(f"[{colors[i]}]█[/{colors[i]}]" for i in range(bars))
    empty  = "[dim]░[/dim]" * (5 - bars)
    return f"{filled}{empty} {ms}ms"

def ssl_badge(ssl_info: dict) -> str:
    if not ssl_info:
        return "[dim]N/A[/dim]"
    if ssl_info.get("valid"):
        days = ssl_info.get("days_left", -1)
        color = "green" if days > 30 else ("yellow" if days > 7 else "red")
        return f"[{color}]✔ Valid[/{color}] — [{color}]{days}d left[/{color}] — {ssl_info.get('issuer', 'N/A')}"
    return f"[red]✘ Invalid — {ssl_info.get('error', 'Unknown')}[/red]"

def make_result_panel(r: dict, idx: int, total: int, check_num: int) -> Panel:
    code  = r["status_code"]
    style = status_style(code)
    is_up = r["is_up"]

    # ── Status line ──
    if r["error"]:
        status_line = f"[bold red]✘ DOWN  —  {r['error']}[/bold red]"
    else:
        emoji = "✔" if is_up else "✘"
        color = "green" if is_up else "red"
        status_line = f"[{color}]{emoji} {code} {r['status_text']}[/{color}]"

    # ── Grid ──
    t = Table(box=None, padding=(0, 1), expand=True, show_header=False)
    t.add_column("Key",   style="dim cyan",  width=20, no_wrap=True)
    t.add_column("Value", style="bold white", ratio=1)

    rows = [
        ("🌐  URL",            r["url"]),
        ("📊  Status",         status_line),
        ("⚡  Response Time",   speed_bar(r["response_ms"])),
        ("🕐  Last Check",     r["checked_at"]),
        ("🔢  Check #",        f"[cyan]{check_num}[/cyan]"),
        ("📡  IP Address",     r["ip"] or "N/A"),
        ("📄  Page Title",     r["page_title"]),
        ("📝  Meta Desc",      r["meta_desc"]),
        ("🖥️  Server",         r["server"]),
        ("🔒  SSL",            ssl_badge(r["ssl"])),
    ]

    for key, val in rows:
        t.add_row(key, val if isinstance(val, str) else str(val))

    # ── Headers sub-table ──
    if r["headers"]:
        t.add_row("", "")
        t.add_row("[bold cyan]── HTTP Headers ──[/bold cyan]", "")
        for k, v in list(r["headers"].items())[:12]:
            t.add_row(f"  [dim]{k}[/dim]", f"[white]{v[:80]}[/white]")

    # ── Panel border color ──
    border_style = "green" if is_up else "red"
    title_str    = f"[bold]{idx+1}/{total}[/bold]  [cyan]{r['url']}[/cyan]"
    return Panel(t, title=title_str, border_style=border_style, padding=(1, 2))

# ─────────────────────────────────────────────────────────────
#  NOTIFICATION (terminal bell + log)
# ─────────────────────────────────────────────────────────────
def notify_down(url: str, error: str):
    console.print(
        Panel(
            f"[bold red]⚠  WEBSITE DOWN  ⚠[/bold red]\n"
            f"[yellow]{url}[/yellow]\n"
            f"[red]{error}[/red]",
            border_style="red",
            title="[bold red]ALERT[/bold red]",
        )
    )
    sys.stdout.write("\a")  # terminal bell
    sys.stdout.flush()
    log(f"[ALERT] DOWN: {url} — {error}")

# ─────────────────────────────────────────────────────────────
#  WORKER — monitors one URL in a loop
# ─────────────────────────────────────────────────────────────
def monitor_worker(url: str, interval: float, url_idx: int, total: int):
    check_num    = 0
    was_down     = False
    stats[url]   = {"checks": 0, "ok": 0, "errors": 0}

    while not stop_event.is_set():
        check_num += 1
        stats[url]["checks"] += 1

        # Loading spinner while checking
        with console.status(
            f"[cyan]Checking[/cyan] [yellow]{url}[/yellow]  "
            f"[dim](#{check_num})[/dim]",
            spinner="dots12",
        ):
            result = check_url(url)

        # Stats
        if result["is_up"]:
            stats[url]["ok"] += 1
            if was_down:
                console.print(f"[bold green]✔ RECOVERED:[/bold green] {url}")
                log(f"[RECOVERED] {url}")
                was_down = False
        else:
            stats[url]["errors"] += 1
            if not was_down:
                notify_down(url, result["error"] or f"HTTP {result['status_code']}")
                was_down = True

        # Log to file
        log(
            f"[CHECK] {url} | "
            f"status={result['status_code']} | "
            f"ms={result['response_ms']} | "
            f"title={result['page_title']} | "
            f"error={result['error']}"
        )

        # Render panel
        panel = make_result_panel(result, url_idx, total, check_num)
        console.print(panel)

        # Summary bar
        ok     = stats[url]["ok"]
        errors = stats[url]["errors"]
        total_ = stats[url]["checks"]
        uptime = (ok / total_) * 100 if total_ else 0
        console.print(
            f"  [dim]Uptime:[/dim] [{'green' if uptime > 90 else 'yellow' if uptime > 70 else 'red'}]"
            f"{uptime:.1f}%[/] "
            f"[dim]|[/dim] [green]OK {ok}[/green] "
            f"[dim]|[/dim] [red]ERR {errors}[/red] "
            f"[dim]|[/dim] Next check in [cyan]{interval}s[/cyan]"
        )
        console.print()

        # Wait interval (interruptible)
        for _ in range(int(interval * 10)):
            if stop_event.is_set():
                break
            time.sleep(0.1)

# ─────────────────────────────────────────────────────────────
#  INTERACTIVE SETUP
# ─────────────────────────────────────────────────────────────
def prompt(msg: str, default: str = "") -> str:
    default_hint = f" [dim](default: {default})[/dim]" if default else ""
    console.print(f"  [cyan]›[/cyan] {msg}{default_hint} ", end="")
    try:
        val = input().strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default

def get_interval() -> float:
    console.print("\n  [bold cyan]Pilih interval refresh:[/bold cyan]")
    options = [
        ("1", "1 detik   [dim](aggressive)[/dim]"),
        ("2", "5 detik   [dim](normal)[/dim]"),
        ("3", "10 detik  [dim](moderate)[/dim]"),
        ("4", "30 detik  [dim](light)[/dim]"),
        ("5", "Custom    [dim](masukkan sendiri)[/dim]"),
    ]
    for key, label in options:
        console.print(f"    [{key}] {label}")
    console.print()

    choice = prompt("Pilihan interval [1-5]", "2")
    mapping = {"1": 1.0, "2": 5.0, "3": 10.0, "4": 30.0}
    if choice in mapping:
        return mapping[choice]
    try:
        val = float(prompt("Masukkan interval (detik)", "5"))
        return max(0.5, val)
    except ValueError:
        return 5.0

def get_urls() -> list:
    console.print("\n  [bold cyan]Masukkan URL website (kosongkan untuk selesai):[/bold cyan]")
    console.print("  [dim]Format: https://example.com[/dim]\n")
    urls = []
    i = 1
    while True:
        url = prompt(f"URL #{i}", "")
        if not url:
            break
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        urls.append(url)
        i += 1
    return urls

# ─────────────────────────────────────────────────────────────
#  FINAL SUMMARY
# ─────────────────────────────────────────────────────────────
def show_summary(urls: list):
    console.print()
    console.print(Rule("[bold cyan]SESSION SUMMARY[/bold cyan]"))
    t = Table(box=box.ROUNDED, border_style="cyan", expand=True)
    t.add_column("URL",    style="bold white")
    t.add_column("Checks", justify="right", style="cyan")
    t.add_column("OK",     justify="right", style="green")
    t.add_column("Errors", justify="right", style="red")
    t.add_column("Uptime", justify="right")

    for url in urls:
        s = stats.get(url, {})
        c = s.get("checks", 0)
        o = s.get("ok",     0)
        e = s.get("errors", 0)
        up = (o / c * 100) if c else 0.0
        color = "green" if up > 90 else ("yellow" if up > 70 else "red")
        t.add_row(url, str(c), str(o), str(e), f"[{color}]{up:.1f}%[/{color}]")

    console.print(t)
    console.print(f"\n  [dim]Log saved to:[/dim] [cyan]{LOG_PATH}[/cyan]\n")

# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────
def main():
    console.clear()
    show_banner()

    # ── Setup ──
    urls = get_urls()
    if not urls:
        console.print("[red]Tidak ada URL yang dimasukkan. Keluar.[/red]")
        sys.exit(0)

    interval = get_interval()

    console.print()
    console.print(
        Panel(
            "\n".join([
                f"[cyan]URLs     :[/cyan] {len(urls)} website",
                f"[cyan]Interval :[/cyan] {interval} detik",
                f"[cyan]Log File :[/cyan] {LOG_PATH}",
                f"[cyan]Mode     :[/cyan] Infinite loop  (Ctrl+C untuk berhenti)",
            ]),
            title="[bold magenta]⚙  KONFIGURASI[/bold magenta]",
            border_style="magenta",
        )
    )
    console.print()

    log(f"Session started | URLs: {urls} | interval: {interval}s")

    # ── Countdown ──
    for i in range(3, 0, -1):
        console.print(f"  Memulai dalam [bold cyan]{i}[/bold cyan]...", end="\r")
        time.sleep(1)
    console.print(" " * 40)

    # ── Multi-URL concurrent ──
    if len(urls) == 1:
        monitor_worker(urls[0], interval, 0, 1)
    else:
        # Round-robin sequential across URLs (one thread per URL staggered)
        threads = []
        for i, url in enumerate(urls):
            t = threading.Thread(
                target=monitor_worker,
                args=(url, interval * len(urls), i, len(urls)),
                daemon=True,
            )
            threads.append(t)

        # Stagger starts
        for i, t in enumerate(threads):
            time.sleep(interval / len(urls) if len(urls) > 1 else 0)
            t.start()

        # Wait until stop
        while not stop_event.is_set():
            time.sleep(0.5)

        for t in threads:
            t.join(timeout=5)

    show_summary(urls)
    log("Session ended by user.")

if __name__ == "__main__":
    main()
