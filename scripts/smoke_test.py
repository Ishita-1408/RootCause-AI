"""Production smoke test CLI utility for live RootCause AI instances."""

import argparse
import sys

import httpx


def run_smoke_tests(base_url: str) -> bool:
    """Run sequential smoke test suite against target base URL."""
    print("=" * 65)
    print(f" ROOTCAUSE AI — PRODUCTION SMOKE TEST SUITE ({base_url})")
    print("=" * 65)

    passed = 0
    total = 0

    with httpx.Client(base_url=base_url.rstrip("/"), timeout=15.0) as client:
        # 1. Health Liveness
        total += 1
        print("\n[1/5] Testing GET /api/v1/health...")
        try:
            res = client.get("/api/v1/health")
            if res.status_code == 200 and res.json().get("status") == "ok":
                print("      PASS: Service is live.")
                passed += 1
            else:
                print(f"      FAIL: Status {res.status_code} - {res.text}")
        except Exception as e:
            print(f"      FAIL: Connection error: {e}")

        # 2. Database Readiness
        total += 1
        print("\n[2/5] Testing GET /api/v1/ready...")
        try:
            res = client.get("/api/v1/ready")
            if res.status_code == 200 and res.json().get("database") == "connected":
                print("      PASS: Database connectivity verified.")
                passed += 1
            else:
                print(f"      FAIL: Status {res.status_code} - {res.text}")
        except Exception as e:
            print(f"      FAIL: Connection error: {e}")

        # 3. Anomaly Detection Pipeline
        total += 1
        print("\n[3/5] Testing POST /api/v1/anomalies/detect...")
        try:
            res = client.post(
                "/api/v1/anomalies/detect",
                json={
                    "metric": "total_gmv",
                    "start_date": "2017-11-01",
                    "end_date": "2017-11-30",
                    "window": 7,
                    "z_threshold": 2.0,
                },
            )
            if res.status_code == 200 and "results" in res.json():
                anom_cnt = res.json().get("anomalies_count", 0)
                print(f"      PASS: Detected {anom_cnt} anomalies successfully.")
                passed += 1
            else:
                print(f"      FAIL: Status {res.status_code} - {res.text}")
        except Exception as e:
            print(f"      FAIL: Error: {e}")

        # 4. Deterministic Root-Cause Investigation
        total += 1
        print("\n[4/5] Testing POST /api/v1/rootcause/investigate...")
        try:
            res = client.post(
                "/api/v1/rootcause/investigate",
                json={
                    "metric": "total_gmv",
                    "anomaly_date": "2017-11-24",
                    "comparison_days": 7,
                    "dimensions": ["product_category", "customer_state"],
                },
            )
            if res.status_code == 200 and "decomposition" in res.json():
                pct = res.json().get("summary", {}).get("percentage_change")
                pct_str = f"{pct:+.1f}%" if pct is not None else "N/A"
                print(f"      PASS: Root-cause executed (Delta={pct_str}).")
                passed += 1
            else:
                print(f"      FAIL: Status {res.status_code} - {res.text}")
        except Exception as e:
            print(f"      FAIL: Error: {e}")

        # 5. Autonomous Agent Pipeline
        total += 1
        print("\n[5/5] Testing POST /api/v1/agent/investigate...")
        try:
            res = client.post(
                "/api/v1/agent/investigate",
                json={
                    "metric": "total_gmv",
                    "anomaly_date": "2017-11-24",
                    "comparison_days": 7,
                    "dimensions": ["product_category", "customer_state"],
                    "max_investigation_steps": 4,
                },
            )
            if res.status_code == 200 and "trace" in res.json():
                status_str = res.json().get("investigation_status")
                print(f"      PASS: Agent investigation completed ({status_str}).")
                passed += 1
            else:
                print(f"      FAIL: Status {res.status_code} - {res.text}")
        except Exception as e:
            print(f"      FAIL: Error: {e}")

    print("\n" + "=" * 65)
    print(f" SMOKE TEST SUMMARY: {passed}/{total} Passed")
    print("=" * 65)

    return passed == total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RootCause AI Production Smoke Test Runner"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Target RootCause AI base URL",
    )
    args = parser.parse_args()

    success = run_smoke_tests(base_url=args.url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
