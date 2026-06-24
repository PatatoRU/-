from __future__ import annotations

import argparse
import asyncio
import time
import urllib.request


def _fetch(url: str, timeout: float) -> tuple[int, float]:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=timeout) as response:
        response.read()
        return response.status, time.perf_counter() - started


async def _worker(url: str, requests_count: int, timeout: float) -> list[tuple[int, float]]:
    results: list[tuple[int, float]] = []
    for _ in range(requests_count):
        results.append(await asyncio.to_thread(_fetch, url, timeout))
    return results


async def run(url: str, concurrency: int, requests_count: int, timeout: float) -> int:
    started = time.perf_counter()
    per_worker = max(1, requests_count // concurrency)
    tasks = [_worker(url, per_worker, timeout) for _ in range(concurrency)]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    statuses: list[int] = []
    latencies: list[float] = []
    errors = 0
    for item in nested:
        if isinstance(item, Exception):
            errors += 1
            continue
        for status, latency in item:
            statuses.append(status)
            latencies.append(latency)
    elapsed = time.perf_counter() - started
    ok = sum(1 for status in statuses if 200 <= status < 400)
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1] if latencies else 0
    rps = ok / elapsed if elapsed else 0
    print({"url": url, "ok": ok, "errors": errors, "elapsed_sec": round(elapsed, 3), "rps": round(rps, 2), "p95_ms": round(p95 * 1000, 2)})
    return 0 if errors == 0 and ok == len(statuses) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple HTTP load smoke check")
    parser.add_argument("--url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    return asyncio.run(run(args.url, args.concurrency, args.requests, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
