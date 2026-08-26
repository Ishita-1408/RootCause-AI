#!/usr/bin/env python3
"""Unified Quality Gate & Production Verification Script for RootCause AI.

Executes all verification tiers:
1. Ruff code formatting & linting
2. Mypy static type checking
3. Pytest backend test suite (258+ tests)
4. Vitest frontend test suite
5. Vite frontend production build
6. Canonical forensic causal benchmark (Phase B)
7. Claim-level hallucination benchmark (Phase G)

Usage:
    uv run python scripts/verify.py
"""

import subprocess
import sys
import time
from typing import NamedTuple


class GateResult(NamedTuple):
    name: str
    command: str
    passed: bool
    duration_sec: float
    output: str


def run_command(name: str, cmd: list[str]) -> GateResult:
    """Execute a single quality gate command with timing."""
    print(f"\n[ RUNNING ] {name}...")
    print(f"            Command: {' '.join(cmd)}")
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=(sys.platform == "win32" and cmd[0] in {"npm", "npm.cmd", "make"}),
    )
    duration = time.perf_counter() - start

    if proc.returncode == 0:
        print(f"[ PASSED  ] {name} ({duration:.2f}s)")
        return GateResult(name, " ".join(cmd), True, duration, proc.stdout)
    else:
        print(f"[ FAILED  ] {name} ({duration:.2f}s)")
        print("\n--- Command Output ---")
        print(proc.stdout)
        print("----------------------\n")
        return GateResult(name, " ".join(cmd), False, duration, proc.stdout)


def main() -> int:
    """Run all quality gates and print summary report card."""
    print("=" * 70)
    print(" RootCause AI — Full Production Verification Suite")
    print("=" * 70)

    npm_bin = "npm.cmd" if sys.platform == "win32" else "npm"

    gates = [
        (
            "Ruff Format Check",
            ["uv", "run", "ruff", "format", "--check", "."],
        ),
        (
            "Ruff Linter",
            ["uv", "run", "ruff", "check", "."],
        ),
        (
            "Mypy Type Checking",
            ["uv", "run", "mypy", "apps", "tests", "scripts", "evaluation"],
        ),
        (
            "Pytest Test Suite",
            ["uv", "run", "pytest", "-v"],
        ),
        (
            "Vitest Frontend Tests",
            [npm_bin, "test", "--prefix", "apps/web"],
        ),
        (
            "Vite Frontend Build",
            [npm_bin, "run", "build", "--prefix", "apps/web"],
        ),
        (
            "Canonical Causal Benchmark",
            [
                "uv",
                "run",
                "python",
                "-m",
                "evaluation.runners.run_benchmark",
                "--verbose",
            ],
        ),
        (
            "Claim Hallucination Benchmark",
            [
                "uv",
                "run",
                "python",
                "-m",
                "evaluation.runners.run_hallucination_benchmark",
                "--verbose",
            ],
        ),
    ]

    results: list[GateResult] = []
    overall_start = time.perf_counter()

    for name, cmd in gates:
        res = run_command(name, cmd)
        results.append(res)
        if not res.passed:
            print(f"\n[!] Verification halted early due to failure in: {name}")
            break

    total_time = time.perf_counter() - overall_start
    all_passed = all(r.passed for r in results) and len(results) == len(gates)

    print("\n" + "=" * 70)
    print(" Quality Gate Summary Report")
    print("=" * 70)
    for r in results:
        status_tag = "PASS" if r.passed else "FAIL"
        print(f"  [{status_tag:4s}] {r.name:<32s} ({r.duration_sec:6.2f}s)")

    if len(results) < len(gates):
        for name, _ in gates[len(results) :]:
            print(f"  [SKIP] {name:<32s}")

    print("-" * 70)
    print(f" Total Verification Time: {total_time:.2f}s")
    if all_passed:
        print(" OVERALL STATUS: ALL QUALITY GATES PASSED (100% GREEN)")
        print("=" * 70)
        return 0
    else:
        print(" OVERALL STATUS: VERIFICATION FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
