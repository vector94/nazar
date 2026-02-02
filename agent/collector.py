import psutil

# Initialize CPU measurement (first call returns 0)
psutil.cpu_percent()


def collect_metrics() -> dict:
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "network_in": net.bytes_recv,
        "network_out": net.bytes_sent,
    }
