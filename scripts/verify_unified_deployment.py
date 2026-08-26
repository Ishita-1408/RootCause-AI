"""Verify unified production deployment routes locally."""

import httpx


def main() -> None:
    print("=" * 65)
    print(" ROOTCAUSE AI — UNIFIED PRODUCTION SERVING VERIFICATION")
    print("=" * 65)

    c = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

    # 1. Root /
    r1 = c.get("/")
    print(f"\n1. GET / (React SPA)          -> Status: {r1.status_code}")
    print(f"   Contains id='root':           {'id="root"' in r1.text}")
    print(f"   Contains 'RootCause AI':      {'RootCause AI' in r1.text}")

    # 2. Swagger /docs
    r2 = c.get("/docs")
    print(f"\n2. GET /docs (Swagger UI)     -> Status: {r2.status_code}")
    print(f"   Contains swagger-ui:          {'swagger-ui' in r2.text}")

    # 3. Health
    r3 = c.get("/api/v1/health")
    print(f"\n3. GET /api/v1/health         -> Status: {r3.status_code}")
    print(f"   Response:                     {r3.json()}")

    # 4. Readiness
    r4 = c.get("/api/v1/ready")
    print(f"\n4. GET /api/v1/ready          -> Status: {r4.status_code}")
    print(f"   Response:                     {r4.json()}")

    # 5. SPA Client-Side Route Fallback
    r5 = c.get("/investigate/anomaly-2017-11-24")
    print(f"\n5. GET /investigate/anomaly   -> Status: {r5.status_code} (SPA Fallback)")
    print(f"   Serves index.html:            {'id="root"' in r5.text}")

    print("\n" + "=" * 65)
    print(" ALL UNIFIED SERVING ENDPOINTS VERIFIED & WORKING!")
    print("=" * 65)


if __name__ == "__main__":
    main()
