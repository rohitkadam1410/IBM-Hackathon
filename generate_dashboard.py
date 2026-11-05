import json
import os
import math

RESULTS_FILE = "benchmark_suite_results.json"
DASHBOARD_FILE = "benchmark_dashboard.html"

def generate_html_dashboard():
    if not os.path.exists(RESULTS_FILE):
        print(f"Error: {RESULTS_FILE} does not exist.")
        return

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = list(data.keys())
    if not models:
        print("No models found in results file.")
        return

    # Extract task metadata
    tasks_map = {}
    for m in models:
        for tid, tinfo in data[m].items():
            if tid not in tasks_map:
                tasks_map[tid] = {
                    "name": tinfo.get("task_name", tid),
                    "category": tinfo.get("category", "General"),
                    "prompt": tinfo.get("prompt", "")
                }

    task_ids = list(tasks_map.keys())
    categories = list(dict.fromkeys([t["category"] for t in tasks_map.values()]))

    # Calculate overall model metrics
    model_stats = {}
    for m in models:
        speeds, latencies, stabilities, tokens = [], [], [], []
        cat_speeds = {c: [] for c in categories}

        for tid in task_ids:
            task_data = data[m].get(tid, {})
            stats = task_data.get("stats", {})
            if "mean_tokens_per_sec" in stats:
                spd = stats["mean_tokens_per_sec"]
                lat = stats["mean_latency_sec"]
                stab = stats.get("stability_score", 100)
                tok = stats.get("mean_eval_tokens", 0)

                speeds.append(spd)
                latencies.append(lat)
                stabilities.append(stab)
                tokens.append(tok)

                cat = tasks_map[tid]["category"]
                cat_speeds[cat].append(spd)

        model_stats[m] = {
            "avg_speed": round(sum(speeds)/len(speeds), 2) if speeds else 0,
            "avg_latency": round(sum(latencies)/len(latencies), 2) if latencies else 0,
            "avg_stability": round(sum(stabilities)/len(stabilities), 1) if stabilities else 0,
            "avg_tokens": round(sum(tokens)/len(tokens), 0) if tokens else 0,
            "cat_speeds": {c: round(sum(cat_speeds[c])/len(cat_speeds[c]), 2) if cat_speeds[c] else 0 for c in categories}
        }

    # Best performers
    fastest_model = max(models, key=lambda m: model_stats[m]["avg_speed"])
    lowest_lat_model = min(models, key=lambda m: model_stats[m]["avg_latency"] if model_stats[m]["avg_latency"] > 0 else 999)
    most_stable_model = max(models, key=lambda m: model_stats[m]["avg_stability"])

    # Prepare Chart Data
    chart_task_names = [tasks_map[tid]["name"] for tid in task_ids]

    speed_datasets = []
    latency_datasets = []
    stability_datasets = []
    colors = [
        {"border": "#3b82f6", "bg": "rgba(59, 130, 246, 0.7)"},   # Blue
        {"border": "#10b981", "bg": "rgba(16, 185, 129, 0.7)"},   # Green
        {"border": "#f59e0b", "bg": "rgba(245, 158, 11, 0.7)"},   # Amber
        {"border": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.7)"}    # Purple
    ]

    for idx, m in enumerate(models):
        c = colors[idx % len(colors)]
        t_speeds = [data[m].get(tid, {}).get("stats", {}).get("mean_tokens_per_sec", 0) for tid in task_ids]
        t_lats = [data[m].get(tid, {}).get("stats", {}).get("mean_latency_sec", 0) for tid in task_ids]
        t_stabs = [data[m].get(tid, {}).get("stats", {}).get("stability_score", 0) for tid in task_ids]

        speed_datasets.append({
            "label": m,
            "data": t_speeds,
            "backgroundColor": c["bg"],
            "borderColor": c["border"],
            "borderWidth": 1.5,
            "borderRadius": 4
        })

        latency_datasets.append({
            "label": m,
            "data": t_lats,
            "backgroundColor": c["bg"],
            "borderColor": c["border"],
            "borderWidth": 1.5,
            "borderRadius": 4
        })

        stability_datasets.append({
            "label": m,
            "data": t_stabs,
            "backgroundColor": c["bg"],
            "borderColor": c["border"],
            "borderWidth": 1.5,
            "borderRadius": 4
        })

    # Radar datasets
    radar_datasets = []
    for idx, m in enumerate(models):
        c = colors[idx % len(colors)]
        c_vals = [model_stats[m]["cat_speeds"].get(cat, 0) for cat in categories]
        radar_datasets.append({
            "label": m,
            "data": c_vals,
            "backgroundColor": c["bg"].replace("0.7", "0.2"),
            "borderColor": c["border"],
            "borderWidth": 2,
            "pointBackgroundColor": c["border"],
            "pointRadius": 4
        })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Local LLM Benchmark & Repeatability Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --primary: #3b82f6;
      --success: #10b981;
      --warning: #f59e0b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background: var(--bg); color: var(--text-main); padding: 24px; line-height: 1.5; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    
    header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }}
    h1 {{ font-size: 26px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }}
    .badge {{ background: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}

    /* Cards Grid */
    .grid-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
    .card-title {{ font-size: 13px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; }}
    .card-value {{ font-size: 28px; font-weight: 800; color: #fff; margin-bottom: 4px; }}
    .card-sub {{ font-size: 13px; color: var(--accent); }}

    /* Charts Grid */
    .grid-charts {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .chart-box {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; position: relative; }}
    .chart-box h2 {{ font-size: 17px; font-weight: 600; margin-bottom: 14px; color: #fff; }}
    .full-width {{ grid-column: 1 / -1; }}

    /* Table */
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; }}
    th {{ background: #0f172a; padding: 12px; color: var(--text-muted); border-bottom: 1px solid var(--border); font-weight: 600; }}
    td {{ padding: 12px; border-bottom: 1px solid var(--border); }}
    tr:hover td {{ background: rgba(255,255,255,0.02); }}

    /* Task Explorer */
    .task-selector {{ width: 100%; padding: 10px 14px; background: #0f172a; color: #fff; border: 1px solid var(--border); border-radius: 8px; font-size: 15px; margin-bottom: 16px; }}
    .model-outputs-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 16px; margin-top: 14px; }}
    .output-card {{ background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 16px; }}
    .output-card h3 {{ font-size: 15px; color: var(--accent); margin-bottom: 8px; border-bottom: 1px solid #1e293b; padding-bottom: 6px; }}
    pre {{ background: #020617; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: #e2e8f0; max-height: 280px; }}
    details {{ margin-bottom: 10px; font-size: 13px; color: var(--text-muted); }}
    summary {{ cursor: pointer; color: var(--accent); font-weight: 500; }}
  </style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>⚡ Local AI Agent Benchmark & Repeatability Dashboard</h1>
      <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Tested on Apple Silicon Local Ollama Server across {len(task_ids)} agent tasks</p>
    </div>
    <span class="badge">VRAM-Safe Mode</span>
  </header>

  <!-- Scorecards -->
  <div class="grid-cards">
    <div class="card">
      <div class="card-title">🚀 Fastest Throughput</div>
      <div class="card-value">{model_stats[fastest_model]['avg_speed']} <span style="font-size: 16px; font-weight: normal;">tok/s</span></div>
      <div class="card-sub">{fastest_model}</div>
    </div>
    <div class="card">
      <div class="card-title">⏱️ Lowest Latency</div>
      <div class="card-value">{model_stats[lowest_lat_model]['avg_latency']} <span style="font-size: 16px; font-weight: normal;">s</span></div>
      <div class="card-sub">{lowest_lat_model}</div>
    </div>
    <div class="card">
      <div class="card-title">🎯 Highest Repeatability / Stability</div>
      <div class="card-value">{model_stats[most_stable_model]['avg_stability']}%</div>
      <div class="card-sub">{most_stable_model} (Lowest Variance)</div>
    </div>
    <div class="card">
      <div class="card-title">📦 Models Compared</div>
      <div class="card-value">{len(models)}</div>
      <div class="card-sub">{", ".join(models)}</div>
    </div>
  </div>

  <!-- Primary Charts -->
  <div class="grid-charts">
    <div class="chart-box">
      <h2>Throughput by Task (Tokens / Second) — Higher is Better</h2>
      <canvas id="speedChart" height="130"></canvas>
    </div>
    <div class="chart-box">
      <h2>Category Strengths (Radar)</h2>
      <canvas id="radarChart" height="180"></canvas>
    </div>
  </div>

  <div class="grid-charts">
    <div class="chart-box">
      <h2>End-to-End Latency by Task (Seconds) — Lower is Better</h2>
      <canvas id="latencyChart" height="130"></canvas>
    </div>
    <div class="chart-box">
      <h2>Repeatability Stability Score (%)</h2>
      <canvas id="stabilityChart" height="180"></canvas>
    </div>
  </div>

  <!-- Interactive Task Output Inspector -->
  <div class="chart-box full-width" style="margin-bottom: 24px;">
    <h2>🔍 Interactive Task Output & Reasoning Inspector</h2>
    <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 12px;">Select a benchmark task to inspect each model's actual response, reasoning trace, and consistency.</p>
    
    <select id="taskSelect" class="task-selector" onchange="updateTaskView()">
      {"".join([f'<option value="{tid}">{tasks_map[tid]["category"]}: {tasks_map[tid]["name"]}</option>' for tid in task_ids])}
    </select>

    <div id="promptBox" style="background: #020617; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 16px; font-size: 13px;">
      <strong style="color: var(--accent);">Prompt:</strong> <span id="promptText"></span>
    </div>

    <div id="modelOutputsContainer" class="model-outputs-grid"></div>
  </div>

  <!-- Summary Table -->
  <div class="chart-box full-width">
    <h2>Detailed Performance Metrics Table</h2>
    <div style="overflow-x: auto;">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Avg Speed</th>
            <th>Avg Latency</th>
            <th>Stability Score</th>
            <th>Avg Generated Tokens</th>
          </tr>
        </thead>
        <tbody>
          {"".join([f'''<tr>
            <td><strong>{m}</strong></td>
            <td><strong style="color: var(--success);">{model_stats[m]["avg_speed"]} tok/s</strong></td>
            <td>{model_stats[m]["avg_latency"]}s</td>
            <td><span style="color: var(--accent); font-weight: 600;">{model_stats[m]["avg_stability"]}%</span></td>
            <td>{model_stats[m]["avg_tokens"]}</td>
          </tr>''' for m in models])}
        </tbody>
      </table>
    </div>
  </div>
</div>

<script>
  const rawData = {json.dumps(data)};
  const tasksMeta = {json.dumps(tasks_map)};

  // 1. Speed Chart
  new Chart(document.getElementById('speedChart'), {{
    type: 'bar',
    data: {{
      labels: {json.dumps(chart_task_names)},
      datasets: {json.dumps(speed_datasets)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }}, maxRotation: 45, minRotation: 35 }}, grid: {{ color: '#334155' }} }},
        y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, title: {{ display: true, text: 'Tokens / Sec', color: '#cbd5e1' }} }}
      }}
    }}
  }});

  // 2. Latency Chart
  new Chart(document.getElementById('latencyChart'), {{
    type: 'bar',
    data: {{
      labels: {json.dumps(chart_task_names)},
      datasets: {json.dumps(latency_datasets)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }}, maxRotation: 45, minRotation: 35 }}, grid: {{ color: '#334155' }} }},
        y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, title: {{ display: true, text: 'Seconds', color: '#cbd5e1' }} }}
      }}
    }}
  }});

  // 3. Radar Chart
  new Chart(document.getElementById('radarChart'), {{
    type: 'radar',
    data: {{
      labels: {json.dumps(categories)},
      datasets: {json.dumps(radar_datasets)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }},
      scales: {{
        r: {{
          angleLines: {{ color: '#334155' }},
          grid: {{ color: '#334155' }},
          pointLabels: {{ color: '#cbd5e1', font: {{ size: 11 }} }},
          ticks: {{ backdropColor: 'transparent', color: '#94a3b8' }}
        }}
      }}
    }}
  }});

  // 4. Stability Chart
  new Chart(document.getElementById('stabilityChart'), {{
    type: 'bar',
    data: {{
      labels: {json.dumps(chart_task_names)},
      datasets: {json.dumps(stability_datasets)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 9 }}, maxRotation: 45, minRotation: 35 }}, grid: {{ color: '#334155' }} }},
        y: {{ max: 100, min: 0, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, title: {{ display: true, text: 'Stability %', color: '#cbd5e1' }} }}
      }}
    }}
  }});

  // Task Inspector logic
  function updateTaskView() {{
    const select = document.getElementById('taskSelect');
    const tid = select.value;
    const taskInfo = tasksMeta[tid] || {{}};
    document.getElementById('promptText').innerText = taskInfo.prompt || '';

    const container = document.getElementById('modelOutputsContainer');
    container.innerHTML = '';

    for (const model of {json.dumps(models)}) {{
      const taskObj = (rawData[model] && rawData[model][tid]) || {{}};
      const runs = taskObj.runs || [];
      const stats = taskObj.stats || {{}};

      let runsHtml = '';
      runs.forEach((r, idx) => {{
        const isTruncated = r.done_reason === 'length' && (!r.output || r.output.trim().length === 0);
        runsHtml += `
          <div style="margin-top: 10px; border-top: 1px dashed #334155; padding-top: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; margin-bottom: 4px;">
              <span>Run #${{r.iteration || idx+1}}</span>
              <span>${{r.tokens_per_sec || 0}} tok/s | ${{r.total_duration_sec || 0}}s | <em>${{r.done_reason || 'done'}}</em></span>
            </div>
            ${{r.thinking ? `<details><summary style="color: ${{isTruncated ? '#f59e0b' : '#38bdf8'}}; font-weight: 600;">
              ${{isTruncated ? '⚠️ Truncated in Reasoning (Click to view thinking draft)' : `View Reasoning (${{r.thinking.length}} chars)`}}
            </summary><pre style="border-left: 3px solid ${{isTruncated ? '#f59e0b' : '#38bdf8'}};">${{escapeHtml(r.thinking)}}</pre></details>` : ''}}
            ${{isTruncated ? 
              '<p style="color: #f59e0b; font-size: 12px; background: rgba(245,158,11,0.1); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(245,158,11,0.3); margin-top: 4px;">⚠️ <strong>Token Budget Exhausted Mid-Thought:</strong> Model spent all tokens on internal reasoning before emitting final answer. (Fix: Increase num_predict to 650+ or use System-1 Jev router).</p>' : 
              `<pre>${{escapeHtml(r.output || '(No response text)')}}</pre>`
            }}
          </div>
        `;
      }});

      const card = document.createElement('div');
      card.className = 'output-card';
      card.innerHTML = `
        <h3>${{model}}</h3>
        <div style="font-size: 12px; color: #cbd5e1; margin-bottom: 6px;">
          <strong>Mean Speed:</strong> ${{stats.mean_tokens_per_sec || 'N/A'}} tok/s &nbsp;|&nbsp;
          <strong>Mean Latency:</strong> ${{stats.mean_latency_sec || 'N/A'}}s &nbsp;|&nbsp;
          <strong>Stability:</strong> ${{stats.stability_score || 'N/A'}}%
        </div>
        ${{runsHtml || '<p style="color: #64748b; font-size: 12px;">No runs recorded.</p>'}}
      `;
      container.appendChild(card);
    }}
  }}

  function escapeHtml(text) {{
    const map = {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }};
    return text.replace(/[&<>"']/g, function(m) {{ return map[m]; }});
  }}

  // Initialize
  updateTaskView();
</script>
</body>
</html>"""

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Dashboard Generated successfully: {DASHBOARD_FILE}]")

if __name__ == "__main__":
    generate_html_dashboard()
