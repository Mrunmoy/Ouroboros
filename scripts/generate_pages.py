#!/usr/bin/env python3
"""Generate GitHub Pages content from CI artifacts.

Expected directory layout (from downloaded artifacts):
  bench-results/results.json
  bench-results/size_report.txt
  bench-results/sizeof_report.txt
  coverage-results/coverage_html/   (lcov HTML)
  coverage-results/coverage_pct.txt (single line: "85.3")
  arm-size-results/arm_cortex_m4.txt
  arm-size-results/arm_cortex_a53.txt
  arm-size-results/arm_cortex_r5.txt

Output: public/  directory ready for GitHub Pages deployment.
"""

import json
import os
import re
import shutil
import sys
from html import escape as esc

ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", ".")
OUT_DIR = os.environ.get("OUT_DIR", "public")


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def parse_size_report(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if ln.lower().startswith("text") and "bss" in ln.lower():
            if i + 1 < len(lines):
                parts = re.split(r"\s+", lines[i + 1])
                if len(parts) >= 3:
                    return {"text": parts[0], "data": parts[1], "bss": parts[2]}
    return {"text": "?", "data": "?", "bss": "?"}


def parse_arm_size(text):
    """Parse `size` output for an ARM object file."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    results = []
    header_idx = None
    for i, ln in enumerate(lines):
        if ln.lower().startswith("text") and "bss" in ln.lower():
            header_idx = i
            continue
        if header_idx is not None and i > header_idx:
            parts = re.split(r"\s+", ln)
            if len(parts) >= 4:
                results.append({
                    "text": parts[0],
                    "data": parts[1],
                    "bss": parts[2],
                    "file": parts[-1] if len(parts) >= 6 else "",
                })
    return results


def fmt_mps(x):
    return f"{x / 1e6:.2f} M/s"


def fmt_gibs(x):
    return f"{x / (1024 ** 3):.2f} GiB/s"


def badge_color(pct):
    if pct >= 90:
        return "brightgreen"
    if pct >= 75:
        return "green"
    if pct >= 60:
        return "yellowgreen"
    if pct >= 40:
        return "yellow"
    return "red"


def main():
    os.makedirs(os.path.join(OUT_DIR, "bench"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "badges"), exist_ok=True)

    # ── Bench artifacts ──────────────────────────────────────────────
    results_path = os.path.join(ARTIFACT_DIR, "bench-results", "results.json")
    size_path = os.path.join(ARTIFACT_DIR, "bench-results", "size_report.txt")
    sizeof_path = os.path.join(ARTIFACT_DIR, "bench-results", "sizeof_report.txt")

    results_txt = read_text(results_path)
    size_txt = read_text(size_path)
    sizeof_txt = read_text(sizeof_path)

    results = json.loads(results_txt) if results_txt else {"benchmarks": [], "context": {}}
    size = parse_size_report(size_txt)

    # Copy raw bench files
    for name in ["results.json", "size_report.txt", "sizeof_report.txt"]:
        src = os.path.join(ARTIFACT_DIR, "bench-results", name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(OUT_DIR, "bench", name))

    # ── Coverage artifacts ───────────────────────────────────────────
    cov_html_src = os.path.join(ARTIFACT_DIR, "coverage-results", "coverage_html")
    cov_pct_path = os.path.join(ARTIFACT_DIR, "coverage-results", "coverage_pct.txt")

    coverage_pct = 0.0
    pct_txt = read_text(cov_pct_path).strip()
    if pct_txt:
        try:
            coverage_pct = float(pct_txt)
        except ValueError:
            pass

    if os.path.isdir(cov_html_src):
        shutil.copytree(cov_html_src, os.path.join(OUT_DIR, "coverage"), dirs_exist_ok=True)

    # Coverage badge JSON (shields.io endpoint)
    badge_json = {
        "schemaVersion": 1,
        "label": "coverage",
        "message": f"{coverage_pct:.1f}%",
        "color": badge_color(coverage_pct),
    }
    with open(os.path.join(OUT_DIR, "badges", "coverage.json"), "w") as f:
        json.dump(badge_json, f)

    # ── ARM size artifacts ───────────────────────────────────────────
    arm_targets = [
        ("Cortex-M4", "arm_cortex_m4.txt"),
        ("Cortex-A53", "arm_cortex_a53.txt"),
        ("Cortex-R5", "arm_cortex_r5.txt"),
    ]
    arm_data = {}
    for label, filename in arm_targets:
        path = os.path.join(ARTIFACT_DIR, "arm-size-results", filename)
        txt = read_text(path)
        if txt:
            arm_data[label] = parse_arm_size(txt)

    # ── Bench rows ───────────────────────────────────────────────────
    benches = results.get("benchmarks", [])
    ctx = results.get("context", {})

    rows = []
    best_items = None
    best_bytes = None

    for b in benches:
        name = b.get("name", "")
        time_unit = b.get("time_unit", "")
        real_time = b.get("real_time", None)
        items = b.get("items_per_second", None)
        bytes_ps = b.get("bytes_per_second", None)

        time_str = ""
        if real_time is not None and time_unit == "ns":
            time_str = f"{real_time:.2f} ns"
        elif real_time is not None:
            time_str = f"{real_time:.2f} {time_unit}"

        items_str = fmt_mps(items) if items else ""
        bytes_str = fmt_gibs(bytes_ps) if bytes_ps else ""

        if items and (best_items is None or items > best_items):
            best_items = items
        if bytes_ps and (best_bytes is None or bytes_ps > best_bytes):
            best_bytes = bytes_ps

        rows.append((esc(name), esc(time_str), esc(items_str), esc(bytes_str)))

    best_items_str = fmt_mps(best_items) if best_items else "n/a"
    best_bytes_str = fmt_gibs(best_bytes) if best_bytes else "n/a"

    host = esc(str(ctx.get("host_name", "unknown")))
    date = esc(str(ctx.get("date", "unknown")))
    num_cpus = esc(str(ctx.get("num_cpus", "unknown")))
    mhz = esc(str(ctx.get("mhz_per_cpu", "unknown")))
    scaling = ctx.get("cpu_scaling_enabled", None)
    scaling_str = "enabled" if scaling else "disabled"

    # ── ARM size HTML ────────────────────────────────────────────────
    arm_html = ""
    if arm_data:
        arm_html += '<h2>ARM Code Size</h2>\n'
        for target_label, entries in arm_data.items():
            arm_html += f'<h3 style="color:var(--accent2);margin:16px 0 6px 0;font-size:15px;">{esc(target_label)}</h3>\n'
            arm_html += '<table><thead><tr><th>text</th><th>data</th><th>bss</th><th>file</th></tr></thead><tbody>\n'
            for e in entries:
                arm_html += f'<tr><td>{esc(e["text"])}</td><td>{esc(e["data"])}</td><td>{esc(e["bss"])}</td><td>{esc(e["file"])}</td></tr>\n'
            arm_html += '</tbody></table>\n'

    # ── Bench rows HTML ──────────────────────────────────────────────
    bench_rows_html = ""
    for (name, time_str, items_str, bytes_str) in rows:
        bench_rows_html += f"<tr><td>{name}</td><td>{time_str}</td><td>{items_str}</td><td>{bytes_str}</td></tr>\n"

    # ── Coverage link ────────────────────────────────────────────────
    cov_link_html = ""
    if coverage_pct > 0:
        cov_link_html = f'<li><a href="coverage/index.html">Coverage report ({coverage_pct:.1f}%)</a></li>'

    # ── Generate HTML ────────────────────────────────────────────────
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ouroboros Dashboard</title>
  <style>
    :root {{
      --bg: #05070d;
      --panel: rgba(12, 18, 35, 0.72);
      --panel2: rgba(8, 12, 24, 0.72);
      --text: #e6f1ff;
      --muted: rgba(230, 241, 255, 0.65);
      --line: rgba(0, 255, 209, 0.18);
      --line2: rgba(102, 204, 255, 0.16);
      --accent: #00ffd1;
      --accent2: #66ccff;
      --shadow: 0 10px 30px rgba(0,0,0,0.55);
      --radius: 14px;
    }}

    html, body {{ height: 100%; }}

    body {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(1200px 600px at 20% 0%, rgba(0,255,209,0.12), transparent 55%),
        radial-gradient(900px 500px at 90% 10%, rgba(102,204,255,0.10), transparent 55%),
        radial-gradient(800px 500px at 50% 100%, rgba(255,59,129,0.06), transparent 60%),
        linear-gradient(180deg, #03040a, #070a14 35%, #040611);
      padding: 26px;
    }}

    .grid {{
      position: fixed; inset: 0; pointer-events: none;
      background-image:
        linear-gradient(to right, rgba(0,255,209,0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0,255,209,0.04) 1px, transparent 1px);
      background-size: 44px 44px;
      mask-image: radial-gradient(circle at 50% 20%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.75) 40%, rgba(0,0,0,0) 85%);
    }}

    .wrap {{ max-width: 1180px; margin: 0 auto; }}

    h1 {{ margin: 0 0 10px 0; font-size: 34px; letter-spacing: 0.4px; text-transform: uppercase; }}
    h2 {{ margin: 26px 0 10px 0; font-size: 18px; letter-spacing: 0.6px; text-transform: uppercase; color: rgba(230,241,255,0.9); }}
    h3 {{ margin: 16px 0 6px 0; font-size: 15px; }}

    .muted {{ color: var(--muted); line-height: 1.45; }}
    .divider {{ height: 1px; background: linear-gradient(90deg, transparent, var(--line), transparent); margin: 18px 0 6px 0; }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px; margin: 18px 0 22px 0;
    }}

    .card {{
      background: linear-gradient(180deg, rgba(12,18,35,0.84), rgba(8,12,24,0.72));
      border: 1px solid var(--line); border-radius: var(--radius);
      box-shadow: var(--shadow); padding: 14px 16px;
      position: relative; overflow: hidden;
    }}

    .card::before {{
      content: ""; position: absolute; inset: 0;
      background:
        radial-gradient(400px 120px at 10% 10%, rgba(0,255,209,0.12), transparent 60%),
        radial-gradient(380px 110px at 90% 20%, rgba(102,204,255,0.10), transparent 60%);
      opacity: 0.9; pointer-events: none;
    }}

    .card .label {{ position: relative; color: var(--muted); font-size: 12px; letter-spacing: 0.6px; text-transform: uppercase; }}
    .card .value {{ position: relative; font-size: 26px; margin-top: 8px; color: var(--accent); text-shadow: 0 0 12px rgba(0,255,209,0.18); }}

    table {{
      width: 100%; border-collapse: collapse; margin: 10px 0 18px 0;
      background: rgba(8,12,24,0.55); border: 1px solid var(--line2);
      border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow);
    }}

    th, td {{ padding: 10px 12px; border-bottom: 1px solid rgba(102,204,255,0.10); font-size: 13px; vertical-align: top; }}
    th {{ text-align: left; color: rgba(230,241,255,0.85); background: rgba(12,18,35,0.65); letter-spacing: 0.6px; text-transform: uppercase; }}
    tr:hover td {{ background: rgba(0,255,209,0.04); }}
    td {{ color: rgba(230,241,255,0.88); }}

    a {{ color: var(--accent2); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    pre {{
      background: rgba(8,12,24,0.65); border: 1px solid var(--line2);
      border-radius: var(--radius); padding: 12px 14px; overflow-x: auto;
      box-shadow: var(--shadow); color: rgba(230,241,255,0.88);
    }}

    .raw ul {{ margin: 8px 0 0 18px; }}
  </style>
</head>
<body>
  <div class="grid"></div>
  <div class="wrap">
    <h1>ouroboros Dashboard</h1>
    <div class="muted">
      Host: <b>{host}</b> &bull; CPUs: <b>{num_cpus}</b> @ <b>{mhz} MHz</b> &bull; CPU scaling: <b>{scaling_str}</b><br/>
      Generated: <b>{date}</b>
    </div>

    <div class="divider"></div>

    <div class="cards">
      <div class="card">
        <div class="label">Best items/sec</div>
        <div class="value">{best_items_str}</div>
      </div>
      <div class="card">
        <div class="label">Best GiB/sec</div>
        <div class="value">{best_bytes_str}</div>
      </div>
      <div class="card">
        <div class="label">Code size (text)</div>
        <div class="value">{size["text"]} bytes</div>
      </div>
      <div class="card">
        <div class="label">RAM (data+bss)</div>
        <div class="value">{size["data"]} + {size["bss"]} bytes</div>
      </div>
      <div class="card">
        <div class="label">Test coverage</div>
        <div class="value">{coverage_pct:.1f}%</div>
      </div>
    </div>

    <h2>Benchmark summary</h2>
    <table>
      <thead>
        <tr><th>Benchmark</th><th>Time</th><th>Items/sec</th><th>GiB/sec</th></tr>
      </thead>
      <tbody>
{bench_rows_html}
      </tbody>
    </table>

    <h2>Native Code/RAM Footprint</h2>
    <table>
      <thead>
        <tr><th>text</th><th>data</th><th>bss</th></tr>
      </thead>
      <tbody>
        <tr><td>{size["text"]}</td><td>{size["data"]}</td><td>{size["bss"]}</td></tr>
      </tbody>
    </table>

{arm_html}

    <h2>sizeof report</h2>
    <pre>{esc(sizeof_txt)}</pre>

    <h2>Resources</h2>
    <ul class="raw">
      <li><a href="bench/results.json">results.json</a></li>
      <li><a href="bench/size_report.txt">size_report.txt</a></li>
      <li><a href="bench/sizeof_report.txt">sizeof_report.txt</a></li>
      {cov_link_html}
    </ul>
  </div>
</body>
</html>
"""

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {os.path.join(OUT_DIR, 'index.html')}")


if __name__ == "__main__":
    main()
