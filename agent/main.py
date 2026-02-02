import time
import httpx

from config import API_URL, HOSTNAME, INTERVAL
from collector import collect_metrics


def send_metrics(metrics: dict):
    payload = {"host": HOSTNAME, **metrics}

    try:
        response = httpx.post(f"{API_URL}/metrics", json=payload, timeout=10)
        response.raise_for_status()
        print(f"Sent: cpu={metrics['cpu_percent']:.1f}% mem={metrics['memory_percent']:.1f}% disk={metrics['disk_percent']:.1f}%")
    except httpx.RequestError as e:
        print(f"Failed to send metrics: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Server error: {e.response.status_code}")


def main():
    print(f"Nazar Agent starting...")
    print(f"  API: {API_URL}")
    print(f"  Host: {HOSTNAME}")
    print(f"  Interval: {INTERVAL}s")
    print()

    while True:
        try:
            metrics = collect_metrics()
            send_metrics(metrics)
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
