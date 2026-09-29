#!/usr/bin/env python3
"""
Generate a simple HTML test report from:
- status (pass/fail)
- logfile path
- test name
-example run :- python urvf_reporter.py PASS /tmp/test_logs/ethernet_connectivity_test_1773603611.log ethernet_connectivity_test
"""

import argparse
import html
from datetime import datetime
from pathlib import Path
import re
from uuid import uuid4
import json


VALID_STATUSES = {"pass", "fail"}


def generate_html_report(
    status: str, logfile_path: str, test_name: str, output_path: str | None = None
) -> Path:
    status_normalized = status.strip().lower()
    if status_normalized not in VALID_STATUSES:
        raise ValueError("status must be 'pass' or 'fail'")

    log_path = Path(logfile_path)
    if not log_path.exists() or not log_path.is_file():
        raise FileNotFoundError(f"Log file not found: {logfile_path}")

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    color = "#2e7d32" if status_normalized == "pass" else "#c62828"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    marker = "<!-- REPORT_ROWS -->"
    out_path = Path(output_path) if output_path else Path("test_report.html")

    test_key = test_name.strip()
    escaped_test_key = html.escape(test_key, quote=True)

    def parse_history(raw: str) -> list[dict[str, str]]:
        raw = raw.strip()
        if not raw:
            return []

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                normalized: list[dict[str, str]] = []
                for item in parsed:
                    if isinstance(item, dict):
                        normalized.append(
                            {
                                "generated": str(item.get("generated", "")),
                                "status": str(item.get("status", "")).lower(),
                                "log_text": str(item.get("log_text", "")),
                            }
                        )
                return normalized
        except Exception:
            pass

        result: list[dict[str, str]] = []
        for part in raw.split("||"):
            part = part.strip()
            if not part:
                continue
            m = re.match(
                r"(?P<generated>.+?)\s*-\s*(?P<status>PASS|FAIL)\s*\((?P<log_name>.+)\)\s*$",
                part,
                re.I,
            )
            if m:
                result.append(
                    {
                        "generated": m.group("generated"),
                        "status": m.group("status").lower(),
                        "log_text": f"[old log ref] {m.group('log_name')}",
                    }
                )
        return result

    def serialize_history(items: list[dict[str, str]]) -> str:
        return json.dumps(items, ensure_ascii=False, separators=(",", ":"))

    def build_log_pop(history_items: list[dict[str, str]]) -> str:
        current_line = f"<pre>{html.escape(log_text)}</pre>"

        last_pass_log = ""
        if status_normalized == "pass":
            last_pass_log = log_text
        else:
            for item in history_items:
                if item.get("status", "").lower() == "pass":
                    last_pass_log = item.get("log_text", "")
                    break

        last_pass_line = (
            f"<pre>{html.escape(last_pass_log)}</pre>" if last_pass_log else "-"
        )

        return f"""
            <details class="log-pop">
              <summary>Log Pop</summary>
              <div><strong>Current:</strong>{current_line}</div>
              <div><strong>Last Passed:</strong> {last_pass_line}</div>
            </details>
        """

    def build_row(history_items: list[dict[str, str]]) -> str:
        history_attr = html.escape(serialize_history(history_items), quote=True)
        current_log_attr = html.escape(log_text, quote=True)

        history_summary = [
            f'{html.escape(x.get("generated", ""))} - {html.escape(x.get("status", "").upper())}'
            for x in history_items
        ]
        history_html = "<br>".join(history_summary) if history_summary else "-"
        log_pop_html = build_log_pop(history_items)
        row_id = f"row-{uuid4().hex}"

        return f"""
        <tr id="{row_id}" data-test="{escaped_test_key}" data-history="{history_attr}" data-current-log="{current_log_attr}">
          <td>{html.escape(test_name)}</td>
          <td class="status" style="font-weight:bold;color:{color};text-transform:uppercase;">{html.escape(status_normalized)}</td>
          <td class="generated">{generated_at}</td>
          <td class="log">
            <details>
              <summary>View Log</summary>
              <pre>{html.escape(log_text)}</pre>
            </details>
          </td>
          <td class="history">{history_html}{log_pop_html}</td>
        </tr>
"""

    def ensure_pie_chart_section(doc: str) -> str:
        chart_block = """
    <div class="chart-wrap">
      <h2>Status Pie Chart</h2>
      <div class="chart-row">
        <canvas id="statusPieChart" width="220" height="220" aria-label="Pass/Fail pie chart"></canvas>
        <div id="statusLegend" class="legend"></div>
      </div>
    </div>
"""
        chart_script = """
<script>
(function () {
  function drawStatusPieChart() {
    const rows = document.querySelectorAll("tbody tr td.status");
    let passCount = 0;
    let failCount = 0;

    rows.forEach((cell) => {
      const val = (cell.textContent || "").trim().toLowerCase();
      if (val === "pass") passCount += 1;
      else if (val === "fail") failCount += 1;
    });

    const total = passCount + failCount;
    const canvas = document.getElementById("statusPieChart");
    const legend = document.getElementById("statusLegend");
    if (!canvas || !legend) return;

    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) / 2 - 10;

    ctx.clearRect(0, 0, w, h);

    if (total === 0) {
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = "#ddd";
      ctx.fill();
      legend.innerHTML = "<div>No data</div>";
      return;
    }

    const passAngle = (passCount / total) * Math.PI * 2;
    const failAngle = (failCount / total) * Math.PI * 2;

    let start = -Math.PI / 2;

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + passAngle);
    ctx.closePath();
    ctx.fillStyle = "#2e7d32";
    ctx.fill();

    start += passAngle;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + failAngle);
    ctx.closePath();
    ctx.fillStyle = "#c62828";
    ctx.fill();

    legend.innerHTML = `
      <div><span class="dot pass"></span>PASS: ${passCount}</div>
      <div><span class="dot fail"></span>FAIL: ${failCount}</div>
      <div><strong>Total: ${total}</strong></div>
    `;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", drawStatusPieChart);
  } else {
    drawStatusPieChart();
  }
})();
</script>
"""
        if 'id="statusPieChart"' not in doc:
            doc = doc.replace(
                "<h1>Test Report</h1>", "<h1>Test Report</h1>" + chart_block, 1
            )
        if "drawStatusPieChart" not in doc:
            doc = doc.replace("</body>", chart_script + "\n</body>", 1)
        return doc

    if out_path.exists():
        current_html = out_path.read_text(encoding="utf-8", errors="replace")
        if marker not in current_html:
            raise ValueError(f"Cannot update rows: marker missing in {out_path}")

        row_pattern = re.compile(
            rf'<tr\s+[^>]*data-test="{re.escape(escaped_test_key)}"[^>]*data-history="(?P<hist>[^"]*)"[^>]*>.*?</tr>',
            re.S,
        )
        existing = row_pattern.search(current_html)

        if existing:
            existing_row = existing.group(0)
            existing_history_raw = html.unescape(existing.group("hist"))
            history_items = parse_history(existing_history_raw)

            prev_status = re.search(
                r'<td class="status"[^>]*>([^<]+)</td>', existing_row
            )
            prev_generated = re.search(
                r'<td class="generated">([^<]+)</td>', existing_row
            )
            prev_current_log = re.search(r'data-current-log="([^"]*)"', existing_row)

            if prev_status and prev_generated:
                prev_record = {
                    "generated": prev_generated.group(1),
                    "status": prev_status.group(1).strip().lower(),
                    "log_text": (
                        html.unescape(prev_current_log.group(1))
                        if prev_current_log
                        else ""
                    ),
                }

                if not history_items or history_items[0] != prev_record:
                    history_items.insert(0, prev_record)

            history_items = history_items[:20]
            new_row = build_row(history_items)
            updated_html = row_pattern.sub(new_row, current_html, count=1)
        else:
            new_row = build_row([])
            updated_html = current_html.replace(marker, f"{new_row}\n{marker}", 1)
    else:
        new_row = build_row([])
        updated_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Test Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f7f7; }}
    .card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    .chart-wrap {{ margin-top: 10px; margin-bottom: 14px; padding: 12px; border: 1px solid #eee; border-radius: 8px; background: #fcfcfc; }}
    .chart-row {{ display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }}
    .legend {{ font-size: 14px; line-height: 1.8; }}
    .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }}
    .dot.pass {{ background: #2e7d32; }}
    .dot.fail {{ background: #c62828; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; }}
    th {{ background: #f0f0f0; text-align: left; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #fafafa; padding: 8px; border: 1px solid #eee; border-radius: 4px; }}
    .log-pop {{ margin-top: 8px; }}
    .log-pop summary {{ cursor: pointer; color: #1565c0; }}
    .log-pop div {{ margin-top: 4px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Test Report</h1>
    <div class="chart-wrap">
      <h2>Status Pie Chart</h2>
      <div class="chart-row">
        <canvas id="statusPieChart" width="220" height="220" aria-label="Pass/Fail pie chart"></canvas>
        <div id="statusLegend" class="legend"></div>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Test Name</th>
          <th>Status</th>
          <th>Generated At</th>
          <th>Log Output</th>
          <th>History</th>
        </tr>
      </thead>
      <tbody>
        {new_row}
        {marker}
      </tbody>
    </table>
  </div>
<script>
(function () {{
  function drawStatusPieChart() {{
    const rows = document.querySelectorAll("tbody tr td.status");
    let passCount = 0;
    let failCount = 0;

    rows.forEach((cell) => {{
      const val = (cell.textContent || "").trim().toLowerCase();
      if (val === "pass") passCount += 1;
      else if (val === "fail") failCount += 1;
    }});

    const total = passCount + failCount;
    const canvas = document.getElementById("statusPieChart");
    const legend = document.getElementById("statusLegend");
    if (!canvas || !legend) return;

    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) / 2 - 10;

    ctx.clearRect(0, 0, w, h);

    if (total === 0) {{
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = "#ddd";
      ctx.fill();
      legend.innerHTML = "<div>No data</div>";
      return;
    }}

    const passAngle = (passCount / total) * Math.PI * 2;
    const failAngle = (failCount / total) * Math.PI * 2;

    let start = -Math.PI / 2;

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + passAngle);
    ctx.closePath();
    ctx.fillStyle = "#2e7d32";
    ctx.fill();

    start += passAngle;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + failAngle);
    ctx.closePath();
    ctx.fillStyle = "#c62828";
    ctx.fill();

    legend.innerHTML = `
      <div><span class="dot pass"></span>PASS: ${{passCount}}</div>
      <div><span class="dot fail"></span>FAIL: ${{failCount}}</div>
      <div><strong>Total: ${{total}}</strong></div>
    `;
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", drawStatusPieChart);
  }} else {{
    drawStatusPieChart();
  }}
}})();
</script>
</body>
</html>
"""

    updated_html = re.sub(
        rf"\s*{re.escape(marker)}\s*", f"\n        {marker}\n", updated_html, count=1
    )
    updated_html = ensure_pie_chart_section(updated_html)
    out_path.write_text(updated_html, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate HTML report from test status, log file, and test name."
    )
    parser.add_argument("status", help="Test status: pass or fail")
    parser.add_argument("logfile", help="Path to log file")
    parser.add_argument("test_name", help="Test name")
    parser.add_argument("-o", "--output", help="Output HTML file path (optional)")
    args = parser.parse_args()

    report_path = generate_html_report(
        args.status, args.logfile, args.test_name, args.output
    )
    print(f"Report generated: {report_path.resolve()}")


if __name__ == "__main__":
    main()
