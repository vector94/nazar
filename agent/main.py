import time
import httpx

from config import API_URL, HOSTNAME, INTERVAL
from collector import collect_metrics


def aggregate(samples: list) -> dict:
    """Aggregate multiple 1-second samples into min/max/avg."""
    keys = ["cpu_percent", "memory_percent", "disk_percent"]
    result = {}

    for key in keys:
        values = [s[key] for s in samples if s[key] is not None]
        if values:
            prefix = key.split("_")[0]  # cpu, memory, disk
            result[key] = sum(values) / len(values)
            result[f"{prefix}_min"] = min(values)
            result[f"{prefix}_max"] = max(values)

    # Use latest network counters
    result["network_in"] = samples[-1]["network_in"]
    result["network_out"] = samples[-1]["network_out"]

    return result


def send_metrics(metrics: dict):
    payload = {"host": HOSTNAME, **metrics}

    try:
        response = httpx.post(f"{API_URL}/metrics", json=payload, timeout=10)
        response.raise_for_status()
        cpu = metrics.get("cpu_percent", 0)
        cpu_max = metrics.get("cpu_max", cpu)
        mem = metrics.get("memory_percent", 0)
        mem_max = metrics.get("memory_max", mem)
        print(
            f"Sent: cpu={cpu:.1f}% (max={cpu_max:.1f}%) "
            f"mem={mem:.1f}% (max={mem_max:.1f}%)"
        )
    except httpx.RequestError as e:
        print(f"Failed to send metrics: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Server error: {e.response.status_code}")


def main():
    print("Nazar Agent starting...")
    print(f"  API: {API_URL}")
    print(f"  Host: {HOSTNAME}")
    print(f"  Interval: {INTERVAL}s (sampling every 1s)")
    print()

    samples = []

    while True:
        try:
            sample = collect_metrics()
            samples.append(sample)

            if len(samples) >= INTERVAL:
                metrics = aggregate(samples)
                send_metrics(metrics)
                samples = []
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
