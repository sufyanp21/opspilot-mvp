#!/usr/bin/env python
import json
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Dict, Any

ARTIFACTS_DIR = Path("artifacts/diagnostics")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def check_cmd(cmd: list[str]) -> tuple[bool, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=20)
        return True, out.strip()
    except Exception as e:
        return False, str(e)


def tcp_check(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def port_free(port: int) -> bool:
    return not tcp_check("127.0.0.1", port, 0.2) and not tcp_check("localhost", port, 0.2)


def load_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if path.exists():
        data: str = ""
        for enc in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
            try:
                data = path.read_text(encoding=enc)
                break
            except Exception:
                continue
        for line in data.splitlines():
            if not line or line.strip().startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                key = k.replace("\x00", "").strip()
                val = v.replace("\x00", "").strip()
                env[key] = val
    return env


def main() -> int:
    report: Dict[str, Any] = {"checks": [], "summary": {}}
    root = Path.cwd()

    # System versions
    py_ok = sys_ok = node_ok = npm_ok = docker_ok = compose_ok = True
    py_ok, py_out = check_cmd(["python", "--version"])
    node_ok, node_out = check_cmd(["node", "--version"])
    npm_ok, npm_out = check_cmd(["npm", "--version"])
    docker_ok, docker_out = check_cmd(["docker", "--version"])
    compose_ok, compose_out = check_cmd(["docker", "compose", "version"])

    report["checks"].append({"name": "python_version", "ok": py_ok, "details": py_out})
    report["checks"].append({"name": "node_version", "ok": node_ok, "details": node_out})
    report["checks"].append({"name": "npm_version", "ok": npm_ok, "details": npm_out})
    report["checks"].append({"name": "docker_version", "ok": docker_ok, "details": docker_out})
    report["checks"].append({"name": "compose_version", "ok": compose_ok, "details": compose_out})

    # Windows vs WSL
    is_windows = platform.system().lower().startswith("win")
    is_wsl = "microsoft" in platform.release().lower()
    report["checks"].append({"name": "os", "ok": True, "details": f"Windows={is_windows}, WSL={is_wsl}"})

    # Ports free
    ports = {8000: port_free(8000), 5173: port_free(5173), 3000: port_free(3000), 8080: port_free(8080), 6379: port_free(6379), 5432: port_free(5432)}
    for p, free in ports.items():
        report["checks"].append({"name": f"port_{p}_free", "ok": free, "details": "free" if free else "in_use"})

    # .env presence
    env_root = root / ".env"
    env_backend = root / "backend/.env"
    env_frontend = root / "apps/web/.env"
    for p in [env_root, env_backend, env_frontend]:
        report["checks"].append({"name": f"env_exists:{p}", "ok": p.exists(), "details": str(p)})

    # Verify backend base health if configured
    fe_env = load_env_file(env_frontend)
    vite_base = fe_env.get("VITE_API_BASE", "http://127.0.0.1:8000")
    health_ok = False
    try:
        import urllib.request
        with urllib.request.urlopen(vite_base.rstrip("/") + "/health", timeout=3) as r:
            health_ok = (r.status == 200)
    except Exception:
        health_ok = False
    report["checks"].append({"name": "backend_health", "ok": health_ok, "details": f"GET {vite_base}/health"})

    # TCP checks for postgres/redis if running
    pg_ok = tcp_check("127.0.0.1", 5432, 0.5)
    r_ok = tcp_check("127.0.0.1", 6379, 0.5)
    report["checks"].append({"name": "tcp_postgres_5432", "ok": pg_ok, "details": "reachable" if pg_ok else "unreachable"})
    report["checks"].append({"name": "tcp_redis_6379", "ok": r_ok, "details": "reachable" if r_ok else "unreachable"})

    # Summarize
    # Relaxed summary rules for local Windows/dev: consider OK if core runtime & backend are healthy
    py_ok_flag = next((c["ok"] for c in report["checks"] if c["name"] == "python_version"), False)
    dock_ok_flag = next((c["ok"] for c in report["checks"] if c["name"] == "docker_version"), True)
    comp_ok_flag = next((c["ok"] for c in report["checks"] if c["name"] == "compose_version"), True)
    core_ok = py_ok_flag and dock_ok_flag and comp_ok_flag
    backend_ok = next((c["ok"] for c in report["checks"] if c["name"] == "backend_health"), False)
    # npm is optional if frontend already runs on 5173
    npm_present = next((c["ok"] for c in report["checks"] if c["name"] == "npm_version"), False)
    fe_running = not next((c["ok"] for c in report["checks"] if c["name"] == "port_5173_free"), True)
    env_fe_ok = next((c["ok"] for c in report["checks"] if c["name"].endswith("apps\\web\\.env") or c["name"].endswith("apps/web/.env")), False)
    ok_all = core_ok and backend_ok and (npm_present or fe_running or env_fe_ok)
    report["summary"] = {"ok": ok_all, "notes": {"npm_present": npm_present, "fe_running": fe_running}}

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / "doctor_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Baseline file
    base_dir = Path("artifacts/diagnostics")
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "system_baseline.txt").write_text(
        "\n".join([
            f"Python: {py_out}",
            f"Node: {node_out}",
            f"npm: {npm_out}",
            f"Docker: {docker_out}",
            f"Compose: {compose_out}",
            f"OS: Windows={is_windows} WSL={is_wsl}",
            f"Ports: {ports}",
            f"Backend health: {health_ok} ({vite_base}/health)",
        ]),
        encoding="utf-8",
    )

    print(json.dumps(report["summary"], indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())


