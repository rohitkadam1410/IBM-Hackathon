import requests
import json
import time
import sys

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "granite4.2:3b"

# Enable streaming to get tokens in real-time
STREAM = True
# Set to False to disable internal reasoning/thinking for instant responses
DISABLE_THINKING = True

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Explain how an AI agent uses Python tools. Give a concise 2-sentence summary and 1 code snippet."
        }
    ],
    "stream": STREAM,
    "think": not DISABLE_THINKING,
    "options": {
        # Limit max tokens generated (speeds up response dramatically)
        "num_predict": 250,
        # Temperature (lower is faster and more focused)
        "temperature": 0.2,
    }
}

def print_metrics(result):
    total_ns = result.get("total_duration", 0)
    load_ns = result.get("load_duration", 0)
    prompt_ns = result.get("prompt_eval_duration", 0)
    eval_ns = result.get("eval_duration", 0)
    
    prompt_tokens = result.get("prompt_eval_count", 0)
    eval_tokens = result.get("eval_count", 0)
    
    tok_per_sec = (eval_tokens / (eval_ns / 1e9)) if eval_ns > 0 else 0
    
    print("\n" + "=" * 45)
    print("           PERFORMANCE BREAKDOWN")
    print("=" * 45)
    print(f"Model Load Time   : {load_ns / 1e9:6.2f} s")
    print(f"Prompt Eval Time  : {prompt_ns / 1e9:6.2f} s ({prompt_tokens} tokens)")
    print(f"Token Generation  : {eval_ns / 1e9:6.2f} s ({eval_tokens} tokens)")
    print(f"Generation Speed  : {tok_per_sec:6.2f} tokens/sec")
    print(f"Total Duration    : {total_ns / 1e9:6.2f} s")
    print("=" * 45)

def main():
    print(f"Connecting to Ollama at {OLLAMA_URL}...")
    print(f"Model: {MODEL} | Streaming: {STREAM}")
    print("\nGenerating response...\n" + "-" * 30)

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=STREAM,
            timeout=120
        )
        response.raise_for_status()

        final_chunk = None

        if STREAM:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    content = chunk.get("message", {}).get("content", "")
                    sys.stdout.write(content)
                    sys.stdout.flush()
                    if chunk.get("done"):
                        final_chunk = chunk
            print("\n" + "-" * 30)
            if final_chunk:
                print_metrics(final_chunk)
        else:
            result = response.json()
            print(result["message"]["content"])
            print("-" * 30)
            print_metrics(result)

    except requests.exceptions.ConnectionError:
        print("\nError: Ollama server is not running.")
    except requests.exceptions.RequestException as e:
        print("\nAPI Error:", e)

if __name__ == "__main__":
    main()
