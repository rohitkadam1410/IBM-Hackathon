import requests
import json
import time
import sys
import os
import argparse
from typing import List, Dict, Any

OLLAMA_URL = "http://localhost:11434"
RESULTS_FILE = "benchmark_results.json"
REPORT_FILE = "benchmark_report.md"

ALL_MODELS = [
    "granite4.2:3b",
    "nemotron-3-nano:4b",
    "qwen3.5:4b"
]

TASKS = [
    {
        "id": "tool_calling",
        "name": "Tool Use / JSON Calling",
        "prompt": (
            "You are an AI agent. When asked for real-time information, respond ONLY with a raw JSON object.\n"
            "Tools available:\n"
            "- get_stock_price(ticker: str)\n"
            "- search_database(query: str)\n\n"
            "User: 'Check the stock price for IBM'\n"
            "Format: {\"tool\": \"<function_name>\", \"arguments\": {\"<arg>\": \"<val>\"}}"
        ),
        "max_tokens": 400,
        "temperature": 0.0
    },
    {
        "id": "python_agent_tool",
        "name": "Agent Tool Implementation",
        "prompt": (
            "Write a clean, self-contained Python function `search_knowledge_base(query: str, top_k: int = 3) -> list[dict]` "
            "that simulates querying vector embeddings and returns mocked documents with 'title' and 'score'. Include only the function."
        ),
        "max_tokens": 450,
        "temperature": 0.2
    },
    {
        "id": "reasoning_planning",
        "name": "Multi-Step Agent Planning",
        "prompt": (
            "You are an autonomous orchestrator agent. Break down the task 'Audit the security and API latency of our backend' "
            "into a strict 3-step execution plan. Provide 1 concise sentence per step."
        ),
        "max_tokens": 350,
        "temperature": 0.2
    }
]

def load_existing_results() -> Dict[str, Any]:
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_results(results: Dict[str, Any]):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

def unload_model_from_memory(model: str):
    """Frees RAM and VRAM by setting keep_alive to 0."""
    try:
        print(f"\n[Memory Management] Unloading '{model}' from RAM/VRAM...")
        requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "keep_alive": 0},
            timeout=10
        )
        time.sleep(1)
        print(f"[Memory Management] '{model}' unloaded. Memory freed.")
    except Exception as e:
        print(f"[Warning] Failed to unload {model}: {e}")

def run_task(model: str, task: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": task["prompt"]}],
        "stream": True,
        "options": {
            "num_predict": task["max_tokens"],
            "temperature": task["temperature"]
        },
        "keep_alive": "5m"
    }

    print(f"\n{'='*70}")
    print(f"Task: [{task['name']}] | Model: [{model}]")
    print(f"{'='*70}")

    start_time = time.time()
    first_token_time = None
    thinking_text = ""
    response_text = ""
    metrics = {}
    in_thinking_mode = False

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
                    if not in_thinking_mode:
                        in_thinking_mode = True
                        sys.stdout.write("[Thinking] ")
                    thinking_text += think
                    sys.stdout.write(think)
                    sys.stdout.flush()

                if content:
                    if in_thinking_mode:
                        in_thinking_mode = False
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
        print(f"\n[Error executing {model}]: {e}")
        return {
            "task_id": task["id"],
            "error": str(e),
            "output": "",
            "thinking": "",
            "tokens_per_sec": 0,
            "ttft_sec": 0,
            "total_duration_sec": 0
        }

    eval_dur = metrics.get("eval_duration", 0)
    eval_count = metrics.get("eval_count", 0)
    tok_per_sec = (eval_count / eval_dur) if eval_dur > 0 else 0
    ttft = (first_token_time - start_time) if first_token_time else 0

    return {
        "task_id": task["id"],
        "task_name": task["name"],
        "model": model,
        "output": response_text.strip(),
        "thinking": thinking_text.strip(),
        "done_reason": metrics.get("done_reason", ""),
        "load_time_sec": round(metrics.get("load_duration", 0), 2),
        "prompt_tokens": metrics.get("prompt_eval_count", 0),
        "eval_tokens": eval_count,
        "tokens_per_sec": round(tok_per_sec, 2),
        "ttft_sec": round(ttft, 2),
        "total_duration_sec": round(metrics.get("total_duration", 0), 2)
    }

def generate_markdown_report(all_results: Dict[str, Dict[str, Any]], filename=REPORT_FILE):
    models = list(all_results.keys())
    if not models:
        return

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Model Benchmark Report (IBM Hackathon)\n\n")
        f.write(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Models tested sequentially (one-by-one to preserve VRAM/RAM).\n\n")

        # Summary Table
        f.write("## 1. Performance Comparison Table\n\n")
        f.write("| Task | Model | Speed (Tokens/s) | TTFT | Total Duration | Output Tokens |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: |\n")

        for task in TASKS:
            t_id = task["id"]
            for model in models:
                m_res = all_results.get(model, {}).get(t_id, {})
                if not m_res:
                    f.write(f"| {task['name']} | `{model}` | *(Pending)* | - | - | - |\n")
                elif "error" in m_res:
                    f.write(f"| {task['name']} | `{model}` | **ERROR** | - | - | - |\n")
                else:
                    f.write(
                        f"| {task['name']} | `{model}` | "
                        f"**{m_res.get('tokens_per_sec', 0):.2f}** | "
                        f"{m_res.get('ttft_sec', 0):.2f}s | "
                        f"{m_res.get('total_duration_sec', 0):.2f}s | "
                        f"{m_res.get('eval_tokens', 0)} |\n"
                    )

        # Average Ranking
        f.write("\n## 2. Overall Model Rankings (Averages)\n\n")
        f.write("| Rank | Model | Avg Tokens/Sec | Avg Latency |\n")
        f.write("| :---: | :--- | :---: | :---: |\n")

        averages = []
        for model in models:
            tasks_res = [all_results[model][t["id"]] for t in TASKS if t["id"] in all_results[model] and "error" not in all_results[model][t["id"]]]
            if tasks_res:
                avg_tps = sum(r["tokens_per_sec"] for r in tasks_res) / len(tasks_res)
                avg_lat = sum(r["total_duration_sec"] for r in tasks_res) / len(tasks_res)
                averages.append((model, avg_tps, avg_lat))
            else:
                averages.append((model, 0.0, 999.0))

        averages.sort(key=lambda x: x[1], reverse=True)
        for rank, (model, avg_tps, avg_lat) in enumerate(averages, 1):
            f.write(f"| {rank} | `{model}` | **{avg_tps:.2f} tok/s** | {avg_lat:.2f}s |\n")

        # Detailed Task Outputs
        f.write("\n## 3. Qualitative Task Outputs\n\n")
        for task in TASKS:
            f.write(f"### Task: {task['name']}\n\n")
            f.write(f"> **Prompt:** {task['prompt'].replace(chr(10), ' ')}\n\n")
            for model in models:
                m_res = all_results.get(model, {}).get(task["id"], {})
                out = m_res.get("output", "")
                think = m_res.get("thinking", "")
                
                f.write(f"#### `{model}`\n\n")
                if think:
                    f.write(f"<details><summary>View Reasoning / Thinking Trace</summary>\n\n```\n{think}\n```\n\n</details>\n\n")
                if out:
                    f.write(f"```\n{out}\n```\n\n")
                elif not think:
                    f.write("*(No output or pending)*\n\n")

    print(f"\n[Report saved & updated: {filename}]")

def print_summary_table(all_results: Dict[str, Dict[str, Any]]):
    models = list(all_results.keys())
    print("\n" + "=" * 92)
    print("                              BENCHMARK SUMMARY METRICS")
    print("=" * 92)
    print(f"{'Task':<28} | {'Model':<20} | {'Tokens/s':<10} | {'TTFT':<8} | {'Total Time':<10} | {'Tokens':<6}")
    print("-" * 92)

    for task in TASKS:
        t_id = task["id"]
        for model in models:
            m_res = all_results.get(model, {}).get(t_id, {})
            if not m_res:
                print(f"{task['name']:<28} | {model:<20} | {'PENDING':<10} | {'-':<8} | {'-':<10} | {'-'}")
            elif "error" in m_res:
                print(f"{task['name']:<28} | {model:<20} | {'ERROR':<10} | {'-':<8} | {'-':<10} | {'-'}")
            else:
                tps = f"{m_res.get('tokens_per_sec', 0):.2f}"
                ttft = f"{m_res.get('ttft_sec', 0):.2f}s"
                tot = f"{m_res.get('total_duration_sec', 0):.2f}s"
                cnt = str(m_res.get("eval_tokens", 0))
                print(f"{task['name']:<28} | {model:<20} | {tps:<10} | {ttft:<8} | {tot:<10} | {cnt:<6}")
        print("-" * 92)

def benchmark_single_model(model: str, results: Dict[str, Any]):
    print(f"\n{'#'*65}")
    print(f"# STARTING BENCHMARK FOR MODEL: {model}")
    print(f"{'#'*65}")

    if model not in results:
        results[model] = {}

    for task in TASKS:
        task_res = run_task(model, task)
        results[model][task["id"]] = task_res
        save_results(results)
        generate_markdown_report(results)

    unload_model_from_memory(model)

def main():
    parser = argparse.ArgumentParser(description="Run LLM benchmarks one-by-one to preserve RAM/VRAM.")
    parser.add_argument("--model", type=str, help="Run only one specific model (e.g. --model granite4.2:3b)")
    parser.add_argument("--models", nargs="+", help="List of models to run sequentially in order")
    args = parser.parse_args()

    results = load_existing_results()

    if args.model:
        models_to_run = [args.model]
    elif args.models:
        models_to_run = args.models
    else:
        models_to_run = ALL_MODELS

    print("=" * 65)
    print("  SEQUENTIAL OLLAMA BENCHMARK (VRAM-Safe Mode)")
    print("=" * 65)
    print(f"Queue of models to benchmark: {models_to_run}\n")

    for i, model in enumerate(models_to_run, 1):
        print(f"\n>>> [{i}/{len(models_to_run)}] Preparing model: {model}")
        benchmark_single_model(model, results)

    print("\n" + "=" * 65)
    print("  ALL BENCHMARKS FINISHED!")
    print("=" * 65)
    print_summary_table(results)

if __name__ == "__main__":
    main()
