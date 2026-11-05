import requests
import json
import time
import sys
import os
import re
import argparse
from typing import List, Dict, Any

OLLAMA_URL = "http://localhost:11434"
RESULTS_FILE = "hackathon_benchmark_results.json"
REPORT_FILE = "hackathon_benchmark_report.md"
DASHBOARD_FILE = "hackathon_dashboard.html"

MODELS = [
    "granite4.2:3b",
    "nemotron-3-nano:4b",
    "qwen3.5:4b"
]

def normalize_text(text: str) -> str:
    """Removes unicode spaces, commas, and formatting to handle European numbers cleanly."""
    return text.replace("\u202f", "").replace("\u00a0", "").replace(",", "").replace(" ", "")

# The 5 Core Challenges for the IBM Vienna Hackathon
HACKATHON_TASKS = [
    {
        "id": "messy_document_extraction",
        "name": "Messy Data & Document Parsing",
        "category": "Unstructured Data",
        "description": "Parse noisy, unstructured data with mixed formatting and extract key financial entities.",
        "use_think": False,  # Fast extraction doesn't need 500 thinking tokens
        "prompt": (
            "You are an AI agent analyzing noisy, raw invoice data from a corrupted text dump:\n\n"
            "--- START RAW DATA ---\n"
            "** VENDOR:   Acme Cloud Solutions GmbH (Reg: ATU99281726) ***\n"
            "Invoice #INV-2026-8819  ///  Date: 2026-10-24\n"
            "Line Items: [item: Cloud Compute vCPU (qty: 4, rate: 45.00) => 180.00 EUR]\n"
            "-- err: log stream interrupted --\n"
            "[item: Object Storage TB (qty: 2, rate: 20.00) => 40.00 EUR]\n"
            "Subtotal: EUR 220.00 | VAT Rate: 20% | VAT Amount: 44.00 EUR\n"
            "TOTAL PAYABLE: 264.00 EUR\n"
            "Payment Status: PENDING_APPROVAL\n"
            "--- END RAW DATA ---\n\n"
            "Extract into pure JSON only:\n"
            "{\"vendor\": str, \"vat_id\": str, \"invoice_number\": str, \"subtotal\": float, \"total\": float, \"currency\": str}"
        ),
        "expected_check": lambda text: (
            "264" in text and "220" in text and "Acme" in text and "ATU99281726" in text
        ),
        "max_tokens": 250
    },
    {
        "id": "conflict_resolution",
        "name": "Conflicting Information Resolution",
        "category": "Information Synthesis",
        "description": "Reconcile two opposing internal company documents using timestamp and precedence rules.",
        "use_think": True,  # Policy audit benefits from quick validation
        "prompt": (
            "You are an autonomous auditor resolving conflicting company policies:\n\n"
            "[Document Alpha - Policy Memo #412]\n"
            "Date: October 12, 2026\n"
            "Author: HR Operations\n"
            "Policy: 'Employee annual remote equipment stipend is set to 500 EUR per calendar year. All requests require VP sign-off.'\n\n"
            "[Document Beta - Executive Directive #089]\n"
            "Date: November 02, 2026\n"
            "Author: Chief People Officer\n"
            "Policy: 'Effective immediately and superseding all prior policies: The annual remote equipment stipend is updated to 850 EUR. Approval requires only Direct Manager sign-off.'\n\n"
            "Question: An employee requests 750 EUR for a home monitor today. Is this within policy, what is the max allowance, and who must approve it? "
            "Resolve the conflict using document recency and authority. Give a direct 2-sentence answer."
        ),
        "expected_check": lambda text: (
            "850" in text and ("manager" in text.lower() or "direct manager" in text.lower()) and ("yes" in text.lower() or "within" in text.lower())
        ),
        "max_tokens": 300
    },
    {
        "id": "constrained_decision_making",
        "name": "Decision Under Multi-Constraint Optimization",
        "category": "Reasoning & Constraints",
        "description": "Choose the optimal vendor tier satisfying strict budget, RAM, SLA, and GDPR constraints.",
        "use_think": False,  # Direct evaluation avoids overthinking loops
        "prompt": (
            "You are an infrastructure agent choosing a database hosting tier under STRICT business constraints:\n"
            "- Constraint 1: Maximum budget is $180 / month (HARD LIMIT).\n"
            "- Constraint 2: Must provide at least 16 GB RAM.\n"
            "- Constraint 3: Uptime SLA must be at least 99.95%.\n"
            "- Constraint 4: Data center must be inside the European Union (EU).\n\n"
            "Available Hosting Options:\n"
            "Option A: $140/mo | 16 GB RAM | 99.90% SLA | Location: Frankfurt (EU)\n"
            "Option B: $175/mo | 16 GB RAM | 99.99% SLA | Location: Vienna (EU)\n"
            "Option C: $160/mo | 32 GB RAM | 99.99% SLA | Location: US-East (Virginia)\n"
            "Option D: $210/mo | 32 GB RAM | 99.99% SLA | Location: Dublin (EU)\n\n"
            "Which single option satisfies ALL 4 constraints? Respond in JSON: {\"selected_option\": \"Option X\", \"justification\": \"<1 sentence>\"}"
        ),
        "expected_check": lambda text: (
            "Option B" in text or "option b" in text.lower()
        ),
        "max_tokens": 250
    },
    {
        "id": "self_verification",
        "name": "Self-Verification & Hallucination Catching",
        "category": "Verification Harness",
        "description": "Audit an AI sub-agent calculation and pinpoint the exact arithmetic or logical error.",
        "use_think": True,  # Verification harness needs calculation headroom
        "prompt": (
            "You are a verification harness auditing an AI sub-agent's work.\n\n"
            "Sub-Agent Trace:\n"
            "Step 1: Raw user traffic = 50,000 visitors.\n"
            "Step 2: Conversion rate = 4% -> 2,000 paying customers.\n"
            "Step 3: Average order value = 35 EUR -> Gross revenue = 2,000 * 35 = 70,000 EUR.\n"
            "Step 4: Platform fee is 15% -> Fee = 70,000 * 0.15 = 10,500 EUR.\n"
            "Step 5: Net revenue = Gross revenue - Platform fee = 70,000 - 10,500 = 62,500 EUR.\n\n"
            "Audit the trace carefully step-by-step. Is Step 5 mathematically correct? "
            "Identify the exact arithmetic error in Step 5, compute the true net revenue, and provide the corrected value."
        ),
        "expected_check": lambda text: (
            "59500" in normalize_text(text)
        ),
        "max_tokens": 350
    },
    {
        "id": "system1_fast_typed_routing",
        "name": "System-1 Fast Typed Decision",
        "category": "Fast Typed (Jev 1.14)",
        "description": "Simulate Jev 1.14: Fast, deterministic classification into typed schema without verbose overhead.",
        "use_think": False,  # System-1 models do not use thinking overhead
        "prompt": (
            "Perform instant typed classification. Classify the following 3 user tickets into EXACTLY one category per ticket:\n"
            "Categories: [TECH_OUTAGE, BILLING_DISPUTE, FEATURE_REQUEST, SPAM]\n\n"
            "Ticket 1: 'I was charged twice for the Pro plan on my Mastercard this morning.'\n"
            "Ticket 2: 'Our entire API gateway is throwing 502 Bad Gateway across all endpoints.'\n"
            "Ticket 3: 'Can you please add dark mode support to the mobile settings tab?'\n\n"
            "Output pure JSON only:\n"
            "{\"ticket_1\": \"<CATEGORY>\", \"ticket_2\": \"<CATEGORY>\", \"ticket_3\": \"<CATEGORY>\"}"
        ),
        "expected_check": lambda text: (
            "BILLING_DISPUTE" in text and "TECH_OUTAGE" in text and "FEATURE_REQUEST" in text
        ),
        "max_tokens": 200
    }
]

def unload_model(model: str):
    try:
        print(f"\n[Memory Management] Flushing '{model}' from RAM/VRAM...")
        requests.post(f"{OLLAMA_URL}/api/chat", json={"model": model, "keep_alive": 0}, timeout=10)
        time.sleep(1.5)
        print(f"[Memory Management] '{model}' unloaded successfully.")
    except Exception as e:
        print(f"[Warning] Failed to unload {model}: {e}")

def run_task(model: str, task: Dict[str, Any], think_mode: str = "smart") -> Dict[str, Any]:
    # Decide whether to enable thinking
    if think_mode == "off":
        use_think = False
    elif think_mode == "on":
        use_think = True
    else:  # "smart"
        use_think = task.get("use_think", False)

    # If thinking is enabled, allocate ample headroom so it never truncates mid-thought
    num_predict = task["max_tokens"] if not use_think else max(1000, task["max_tokens"] + 650)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": task["prompt"]}],
        "stream": True,
        "think": use_think,
        "options": {
            "num_predict": num_predict,
            "temperature": 0.0
        },
        "keep_alive": "10m"
    }

    print(f"\n{'='*75}")
    print(f"Task: [{task['name']}] | Model: [{model}] | Think: {use_think} (Budget: {num_predict} tokens)")
    print(f"{'='*75}")

    start_time = time.time()
    first_token_time = None
    response_text = ""
    thinking_text = ""
    in_thinking = False
    metrics = {}

    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=240)
        res.raise_for_status()

        for line in res.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                msg = chunk.get("message", {})
                think = msg.get("thinking", "")
                content = msg.get("content", "")

                if (think or content) and first_token_time is None:
                    first_token_time = time.time()

                if think:
                    if not in_thinking:
                        in_thinking = True
                        sys.stdout.write("[Thinking] ")
                    thinking_text += think
                    sys.stdout.write(think)
                    sys.stdout.flush()

                if content:
                    if in_thinking:
                        in_thinking = False
                        sys.stdout.write("\n[Response] ")
                    response_text += content
                    sys.stdout.write(content)
                    sys.stdout.flush()

                if chunk.get("done"):
                    metrics = {
                        "total_duration": chunk.get("total_duration", 0) / 1e9,
                        "load_duration": chunk.get("load_duration", 0) / 1e9,
                        "prompt_eval_duration": chunk.get("prompt_eval_duration", 0) / 1e9,
                        "prompt_eval_count": chunk.get("prompt_eval_count", 0),
                        "eval_duration": chunk.get("eval_duration", 0) / 1e9,
                        "eval_count": chunk.get("eval_count", 0),
                        "done_reason": chunk.get("done_reason", "")
                    }
        print()

    except Exception as e:
        print(f"\n[Execution Error {model} on {task['id']}]: {e}")
        return {
            "error": str(e),
            "output": "",
            "thinking": "",
            "passed": False,
            "recovered": False,
            "tokens_per_sec": 0.0,
            "ttft_sec": 0.0,
            "total_duration_sec": 0.0,
            "eval_tokens": 0
        }

    eval_dur = metrics.get("eval_duration", 0)
    eval_count = metrics.get("eval_count", 0)
    tok_per_sec = (eval_count / eval_dur) if eval_dur > 0 else 0
    ttft = (first_token_time - start_time) if first_token_time else 0

    # Smart Harness Fallback: If content was empty due to truncation, recover from thinking draft
    recovered = False
    clean_output = response_text.strip()
    if not clean_output and thinking_text.strip():
        if task["expected_check"](thinking_text):
            recovered = True
            json_match = re.findall(r"\{[^{}]*\}", thinking_text, re.DOTALL)
            clean_output = json_match[-1] if json_match else thinking_text.strip().split("\n")[-1]

    # Accuracy / Verification check
    passed = False
    try:
        passed = task["expected_check"](clean_output) or (recovered and task["expected_check"](thinking_text))
    except Exception:
        passed = False

    return {
        "output": clean_output,
        "thinking": thinking_text.strip(),
        "passed": passed,
        "recovered": recovered,
        "think_enabled": use_think,
        "done_reason": metrics.get("done_reason", ""),
        "load_time_sec": round(metrics.get("load_duration", 0), 2),
        "prompt_tokens": metrics.get("prompt_eval_count", 0),
        "eval_tokens": eval_count,
        "total_tokens": metrics.get("prompt_eval_count", 0) + eval_count,
        "tokens_per_sec": round(tok_per_sec, 2),
        "ttft_sec": round(ttft, 2),
        "total_duration_sec": round(metrics.get("total_duration", 0), 2)
    }

def generate_report(results: Dict[str, Any], models: List[str]):
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# IBM Vienna Hackathon: SLM Evaluation & Benchmark Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Evaluation Theme:** Small Model. Smart Harness. (Accuracy vs. Cost Efficiency)  \n\n")

        # Scorecard Formula
        f.write("## 1. Hackathon Leaderboard & Efficiency Ranking\n\n")
        f.write("Evaluation criteria per hackathon guidelines: **Accuracy and Cost count equally**.\n")
        f.write("$$\\text{Efficiency Score} = \\frac{\\text{Accuracy Rate (\\%)}}{\\text{Avg Total Tokens}} \\times 10,000$$\n\n")
        f.write("| Rank | Model | Accuracy | Passed Tasks | Avg Tokens / Task | Avg Speed | Hackathon Efficiency Score |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :---: | :---: |\n")

        model_summaries = []
        for m in models:
            m_tasks = results.get(m, {})
            total_tasks = len(HACKATHON_TASKS)
            passed_tasks = sum(1 for t in HACKATHON_TASKS if m_tasks.get(t["id"], {}).get("passed", False))
            acc_rate = (passed_tasks / total_tasks) * 100

            total_toks = sum(m_tasks.get(t["id"], {}).get("total_tokens", 0) for t in HACKATHON_TASKS)
            avg_toks = (total_toks / total_tasks) if total_tasks > 0 else 1

            speeds = [m_tasks.get(t["id"], {}).get("tokens_per_sec", 0) for t in HACKATHON_TASKS if m_tasks.get(t["id"], {}).get("tokens_per_sec", 0) > 0]
            avg_speed = sum(speeds) / len(speeds) if speeds else 0

            efficiency = (acc_rate / avg_toks) * 10000 if avg_toks > 0 else 0
            model_summaries.append((m, acc_rate, passed_tasks, avg_toks, avg_speed, efficiency))

        model_summaries.sort(key=lambda x: (x[1], x[5]), reverse=True)

        for rank, (m, acc, passed, avg_toks, spd, eff) in enumerate(model_summaries, 1):
            f.write(f"| {rank} | `{m}` | **{acc:.1f}%** | {passed}/{len(HACKATHON_TASKS)} | {avg_toks:.0f} tokens | {spd:.2f} tok/s | **{eff:.2f}** |\n")

        # Task by Task Detailed Table
        f.write("\n## 2. Task-by-Task Performance Matrix\n\n")
        f.write("| Task | Model | Status | Speed | Latency | Tokens | Content Generated |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")

        for task in HACKATHON_TASKS:
            tid = task["id"]
            for m in models:
                res = results.get(m, {}).get(tid, {})
                status_icon = "✅ PASS" if res.get("passed", False) else "❌ FAIL"
                if res.get("recovered"):
                    has_content = "⚡ Recovered from Draft"
                elif res.get("output", "").strip():
                    has_content = "Yes"
                else:
                    has_content = "⚠️ Truncated"
                f.write(f"| {task['name']} | `{m}` | {status_icon} | {res.get('tokens_per_sec', 0):.2f} tok/s | {res.get('total_duration_sec', 0):.2f}s | {res.get('eval_tokens', 0)} | {has_content} |\n")

        # Qualitative Answers
        f.write("\n## 3. Qualitative Model Outputs\n\n")
        for task in HACKATHON_TASKS:
            tid = task["id"]
            f.write(f"### {task['name']}\n\n")
            f.write(f"> **Scenario:** {task['description']}\n\n")
            for m in models:
                res = results.get(m, {}).get(tid, {})
                think = res.get("thinking", "")
                out = res.get("output", "")
                f.write(f"#### `{m}`\n\n")
                if think:
                    f.write(f"<details><summary>Reasoning Trace ({len(think)} chars)</summary>\n\n```\n{think}\n```\n\n</details>\n\n")
                if out:
                    f.write(f"```\n{out}\n```\n\n")
                else:
                    f.write("*(No final output)*\n\n")

    print(f"\n[Generated Hackathon Report: {REPORT_FILE}]")

def generate_dashboard(results: Dict[str, Any], models: List[str]):
    tasks_meta = {t["id"]: {"name": t["name"], "category": t["category"], "desc": t["description"], "prompt": t["prompt"]} for t in HACKATHON_TASKS}
    task_names = [t["name"] for t in HACKATHON_TASKS]

    model_stats = {}
    for m in models:
        passed = sum(1 for t in HACKATHON_TASKS if results.get(m, {}).get(t["id"], {}).get("passed", False))
        speeds = [results.get(m, {}).get(t["id"], {}).get("tokens_per_sec", 0) for t in HACKATHON_TASKS]
        latencies = [results.get(m, {}).get(t["id"], {}).get("total_duration_sec", 0) for t in HACKATHON_TASKS]
        toks = [results.get(m, {}).get(t["id"], {}).get("total_tokens", 0) for t in HACKATHON_TASKS]
        
        acc = (passed / len(HACKATHON_TASKS)) * 100
        avg_spd = sum(speeds) / len(speeds) if speeds else 0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0
        avg_tok = max(1, sum(toks) / len(toks) if toks else 1)
        eff = (acc / avg_tok) * 10000

        model_stats[m] = {
            "passed": passed,
            "accuracy": acc,
            "avg_speed": round(avg_spd, 2),
            "avg_latency": round(avg_lat, 2),
            "avg_tokens": round(avg_tok, 0),
            "efficiency": round(eff, 2)
        }

    colors = [
        {"border": "#3b82f6", "bg": "rgba(59, 130, 246, 0.7)"},
        {"border": "#10b981", "bg": "rgba(16, 185, 129, 0.7)"},
        {"border": "#f59e0b", "bg": "rgba(245, 158, 11, 0.7)"}
    ]

    speed_datasets = []
    token_datasets = []
    for idx, m in enumerate(models):
        c = colors[idx % len(colors)]
        t_speeds = [results.get(m, {}).get(t["id"], {}).get("tokens_per_sec", 0) for t in HACKATHON_TASKS]
        t_tokens = [results.get(m, {}).get(t["id"], {}).get("total_tokens", 0) for t in HACKATHON_TASKS]
        speed_datasets.append({"label": m, "data": t_speeds, "backgroundColor": c["bg"], "borderColor": c["border"], "borderWidth": 1.5})
        token_datasets.append({"label": m, "data": t_tokens, "backgroundColor": c["bg"], "borderColor": c["border"], "borderWidth": 1.5})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>IBM Vienna Hackathon: SLM Evaluation Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{ --bg: #0b0f19; --card: #151d2f; --border: #23304a; --text: #f1f5f9; --muted: #94a3b8; --accent: #38bdf8; --success: #10b981; --warning: #f59e0b; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: var(--bg); color: var(--text); padding: 24px; }}
    .container {{ max-width: 1350px; margin: 0 auto; }}
    header {{ border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .badge {{ background: #0284c7; color: #fff; padding: 5px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
    .grid-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
    .card-title {{ font-size: 13px; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: 8px; }}
    .card-val {{ font-size: 32px; font-weight: 800; color: #fff; }}
    .card-sub {{ font-size: 13px; color: var(--accent); margin-top: 4px; }}
    .grid-charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .chart-box {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
    .chart-box h2 {{ font-size: 17px; margin-bottom: 14px; color: #fff; }}
    .full {{ grid-column: 1 / -1; }}
    select {{ width: 100%; padding: 10px 14px; background: #0f172a; color: #fff; border: 1px solid var(--border); border-radius: 8px; font-size: 15px; margin-bottom: 14px; }}
    .outputs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-top: 14px; }}
    .out-card {{ background: #0c1222; border: 1px solid var(--border); border-radius: 8px; padding: 16px; }}
    pre {{ background: #050811; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; font-family: ui-monospace, Menlo, monospace; color: #e2e8f0; max-height: 260px; }}
    details {{ margin-bottom: 10px; font-size: 13px; }}
    summary {{ cursor: pointer; color: var(--accent); font-weight: 600; }}
  </style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>🏆 IBM Vienna Hackathon: SLM Evaluation Dashboard</h1>
      <p style="color: var(--muted); font-size: 14px; margin-top: 4px;">Small Model. Smart Harness. — Accuracy vs. Cost-Efficiency Evaluation</p>
    </div>
    <span class="badge">Adaptive Think Harness</span>
  </header>

  <div class="grid-cards">
    {"".join([f'''<div class="card">
      <div class="card-title">Model: {m}</div>
      <div class="card-val">{model_stats[m]["accuracy"]}% <span style="font-size: 16px; font-weight: normal; color: var(--muted);">({model_stats[m]["passed"]}/5 tasks)</span></div>
      <div class="card-sub">⚡ {model_stats[m]["avg_speed"]} tok/s | 🪙 {model_stats[m]["avg_tokens"]} avg tokens</div>
      <div style="margin-top: 8px; font-size: 14px; font-weight: bold; color: var(--success);">Efficiency Score: {model_stats[m]["efficiency"]}</div>
    </div>''' for m in models])}
  </div>

  <div class="grid-charts">
    <div class="chart-box">
      <h2>Throughput by Hackathon Challenge (Tokens / Second)</h2>
      <canvas id="speedChart" height="150"></canvas>
    </div>
    <div class="chart-box">
      <h2>Total Token Cost per Task (Lower is Cheaper)</h2>
      <canvas id="tokenChart" height="150"></canvas>
    </div>
  </div>

  <div class="chart-box full" style="margin-bottom: 24px;">
    <h2>🔍 Interactive Challenge Output & Verification Inspector</h2>
    <select id="taskSelect" onchange="updateView()">
      {"".join([f'<option value="{t["id"]}">{t["name"]}</option>' for t in HACKATHON_TASKS])}
    </select>
    <div id="descBox" style="background: #080d1a; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 14px; font-size: 13px;">
      <strong style="color: var(--accent);">Challenge Goal:</strong> <span id="taskDesc"></span>
    </div>
    <div id="outputsContainer" class="outputs"></div>
  </div>
</div>

<script>
  const results = {json.dumps(results)};
  const tasksMeta = {json.dumps(tasks_meta)};
  const models = {json.dumps(models)};

  new Chart(document.getElementById('speedChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(task_names)}, datasets: {json.dumps(speed_datasets)} }},
    options: {{ responsive: true, plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }}, scales: {{ x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}, y: {{ ticks: {{ color: '#94a3b8' }} }} }} }}
  }});

  new Chart(document.getElementById('tokenChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(task_names)}, datasets: {json.dumps(token_datasets)} }},
    options: {{ responsive: true, plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }}, scales: {{ x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}, y: {{ ticks: {{ color: '#94a3b8' }} }} }} }}
  }});

  function updateView() {{
    const tid = document.getElementById('taskSelect').value;
    document.getElementById('taskDesc').innerText = tasksMeta[tid].desc;
    const container = document.getElementById('outputsContainer');
    container.innerHTML = '';

    for (const m of models) {{
      const r = (results[m] && results[m][tid]) || {{}};
      const passed = r.passed;
      let statusBadge = passed ? 
        '<span style="background: #065f46; color: #34d399; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">✅ PASSED</span>' :
        '<span style="background: #7f1d1d; color: #f87171; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">❌ FAILED</span>';

      if (r.recovered) {{
        statusBadge += ' <span style="background: #0284c7; color: #e0f2fe; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 4px;">⚡ RECOVERED FROM DRAFT</span>';
      }}

      const card = document.createElement('div');
      card.className = 'out-card';
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
          <h3 style="color: var(--accent); font-size: 15px;">${{m}}</h3>
          <div>${{statusBadge}}</div>
        </div>
        <div style="font-size: 12px; color: #94a3b8; margin-bottom: 8px;">
          Think: <strong>${{r.think_enabled ? 'ON' : 'OFF'}}</strong> | Speed: <strong>${{r.tokens_per_sec || 0}} tok/s</strong> | Latency: <strong>${{r.total_duration_sec || 0}}s</strong> | Tokens: <strong>${{r.eval_tokens || 0}}</strong>
        </div>
        ${{r.thinking ? `<details><summary>Reasoning Trace (${{r.thinking.length}} chars)</summary><pre>${{escapeHtml(r.thinking)}}</pre></details>` : ''}}
        <pre style="border-left: 3px solid ${{passed ? '#10b981' : '#ef4444'}};">${{escapeHtml(r.output || '(No response text)')}}</pre>
      `;
      container.appendChild(card);
    }}
  }}

  function escapeHtml(t) {{
    const m = {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }};
    return t.replace(/[&<>"']/g, c => m[c]);
  }}

  updateView();
</script>
</body>
</html>"""

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Generated Hackathon Dashboard: {DASHBOARD_FILE}]")

def main():
    parser = argparse.ArgumentParser(description="IBM Vienna Hackathon specific SLM benchmark suite.")
    parser.add_argument("--model", type=str, help="Run only one specific model")
    parser.add_argument("--think-mode", choices=["smart", "off", "on"], default="smart", 
                        help="smart (adaptive think per task), off (think=False for all), on (think=True for all)")
    args = parser.parse_args()

    models_to_run = [args.model] if args.model else MODELS

    print("=" * 75)
    print("   IBM VIENNA HACKATHON: LOCAL SLM EVALUATION SUITE")
    print("=" * 75)
    print(f"Models to evaluate : {models_to_run}")
    print(f"Think Mode         : {args.think_mode}")
    print(f"Challenge Tasks    : {len(HACKATHON_TASKS)} hackathon-specific scenarios")
    print("=" * 75)

    results = {}
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = {}

    for i, model in enumerate(models_to_run, 1):
        print(f"\n>>> [{i}/{len(models_to_run)}] Benchmarking Model: {model}")
        if model not in results:
            results[model] = {}

        for task_idx, task in enumerate(HACKATHON_TASKS, 1):
            print(f"\n--- [{task_idx}/{len(HACKATHON_TASKS)}] {task['name']} ---")
            task_res = run_task(model, task, think_mode=args.think_mode)
            results[model][task["id"]] = task_res

            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

        unload_model(model)
        generate_report(results, models_to_run)
        generate_dashboard(results, models_to_run)

    print("\n" + "=" * 75)
    print("  ALL HACKATHON BENCHMARKS COMPLETE!")
    print("=" * 75)

if __name__ == "__main__":
    main()
