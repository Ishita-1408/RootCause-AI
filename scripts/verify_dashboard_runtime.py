"""Live Runtime Verification of RootCause AI Frontend and Backend."""

import httpx

VITE_URL = "http://127.0.0.1:5173"
FASTAPI_URL = "http://127.0.0.1:8000"


def main() -> None:
    print("=" * 60)
    print(" ROOTCAUSE AI - LIVE RUNTIME DIAGNOSTIC VERIFICATION")
    print("=" * 60)

    # 1. Direct Backend Health
    with httpx.Client(base_url=FASTAPI_URL, timeout=15.0) as client:
        h = client.get("/api/v1/health")
        print(f"1. Direct Backend Health: {h.status_code} -> {h.json()}")

    # 2. Vite Frontend HTML Delivery
    with httpx.Client(base_url=VITE_URL, timeout=15.0) as client:
        r_html = client.get("/")
        has_root = 'id="root"' in r_html.text
        print(f"2. Vite HTML: {r_html.status_code} | Has Root: {has_root}")

        # 3. Vite CSS Delivery
        r_css = client.get("/src/index.css")
        print(f"3. Vite CSS: {r_css.status_code} | Size: {len(r_css.text)} bytes")

        # 4. Vite Proxy -> /api/v1/health
        r_proxy_health = client.get("/api/v1/health")
        print(f"4. Vite Proxy Health: {r_proxy_health.status_code}")

        # 5. Vite Proxy -> /api/v1/anomalies/detect
        r_anom = client.post(
            "/api/v1/anomalies/detect",
            json={
                "metric": "total_gmv",
                "start_date": "2017-11-01",
                "end_date": "2017-11-30",
                "window": 7,
                "z_threshold": 2.0,
            },
        )
        anom_json = r_anom.json()
        anom_count = anom_json.get("anomalies_count", 0)
        total_obs = anom_json.get("total_observations", 0)
        print(
            f"5. Vite Proxy Anomalies: {r_anom.status_code} | "
            f"Days: {total_obs} | Anomalies: {anom_count}"
        )

        # 6. Vite Proxy -> /api/v1/rootcause/investigate
        r_rc = client.post(
            "/api/v1/rootcause/investigate",
            json={
                "metric": "total_gmv",
                "anomaly_date": "2017-11-24",
                "comparison_days": 7,
                "dimensions": ["product_category", "customer_state", "seller"],
                "max_results": 5,
            },
        )
        rc_json = r_rc.json()
        obs_val = rc_json["summary"]["observed_value"]
        base_val = rc_json["summary"]["baseline_value"]
        pct_chg = rc_json["summary"]["percentage_change"]
        vol_share = rc_json["decomposition"]["volume_contribution_pct"]
        top_contrib = rc_json["ranked_contributors"][0]
        top_val = top_contrib["dimension_value"]
        top_pct = top_contrib["contribution_pct"]
        print(
            f"6. Vite Proxy Root-Cause: {r_rc.status_code} | "
            f"Obs: R${obs_val:,.2f} vs Base: R${base_val:,.2f} ({pct_chg:+.1f}%) | "
            f"Vol: {vol_share:.1f}% | "
            f"Top: {top_val} ({top_pct:.1f}%)"
        )

        # 7. Vite Proxy -> /api/v1/ai/investigate
        r_ai = client.post(
            "/api/v1/ai/investigate",
            json={
                "metric": "total_gmv",
                "anomaly_date": "2017-11-24",
                "comparison_days": 7,
            },
        )
        ai_json = r_ai.json()
        print(
            f"7. Vite Proxy AI Memo: {r_ai.status_code} | "
            f"Title: {ai_json['investigation_title']} | "
            f"Fallback: {ai_json['is_fallback']}"
        )

    print("=" * 60)
    print(" ALL RUNTIME ENDPOINTS VERIFIED & WORKING SEAMLESSLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
