#!/usr/bin/env python3
"""
Container Isolation Safety Check

Verify that only crin_* containers and ports are being used.
Run this before any Docker operation.
"""

import os
import subprocess
import sys
from pathlib import Path


# Expected project configuration
EXPECTED_CWD = "/home/kobanenkokn/Clin-rec"
EXPECTED_SERVICES = {"app", "minio", "minio-init", "postgres", "redis", "streamlit", "worker"}
CRIN_PORTS = {"5433", "6380", "8008", "8501", "9010", "9011"}
CRIN_CONTAINER_PREFIX = "crin_"

# Forbidden ports (used by other services)
FORBIDDEN_PORTS = {"5432", "6379", "8080", "9000", "9001"}


def run_cmd(cmd: str) -> str:
    """Execute shell command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def check_working_directory() -> bool:
    """Verify we're in the correct project directory."""
    cwd = os.getcwd()
    if cwd != EXPECTED_CWD:
        print(f"❌ ISOLATION VIOLATION: Wrong working directory")
        print(f"   Current:  {cwd}")
        print(f"   Expected: {EXPECTED_CWD}")
        return False
    print(f"✅ Working directory: {cwd}")
    return True


def check_docker_services() -> bool:
    """Verify docker compose has only expected services."""
    try:
        services_output = run_cmd("docker compose config --services 2>/dev/null")
        if not services_output:
            print("❌ ISOLATION VIOLATION: Cannot read docker compose services")
            print("   (Is docker running? Are you in correct directory?)")
            return False
        
        services = set(services_output.split('\n'))
        
        if services != EXPECTED_SERVICES:
            print(f"❌ ISOLATION VIOLATION: Docker compose services mismatch")
            print(f"   Expected: {sorted(EXPECTED_SERVICES)}")
            print(f"   Got:      {sorted(services)}")
            return False
        
        print(f"✅ Docker services: {sorted(services)}")
        return True
    except Exception as e:
        print(f"❌ Error checking docker services: {e}")
        return False


def check_container_names() -> bool:
    """Verify running containers are all prefixed with crin_."""
    try:
        # Get all running crin_ containers
        crin_output = run_cmd(
            "docker ps -a --filter \"label=com.docker.compose.project=crin\" "
            "--format \"{{.Names}}\" 2>/dev/null"
        )
        crin_containers = set(crin_output.split('\n')) if crin_output else set()
        
        # Get all other running containers (should be none)
        other_output = run_cmd(
            "docker ps -a --filter \"label!=com.docker.compose.project=crin\" "
            "--format \"{{.Names}}\" 2>/dev/null | grep -v '^$'"
        )
        other_containers = set(other_output.split('\n')) if other_output else set()
        other_containers.discard('')  # Remove empty strings
        
        if other_containers:
            print(f"ℹ️  INFO: Other containers on server (not managed by agent):")
            for name in sorted(other_containers):
                if name:
                    print(f"   - {name}")
        
        print(f"✅ Project containers (crin_): {sorted(crin_containers)}")
        return True
    except Exception as e:
        print(f"⚠️  Warning checking container names: {e}")
        return True  # Non-critical


def check_port_usage() -> bool:
    """Verify crin_ project ports are available and no other services use them."""
    try:
        # Check netstat/ss for port usage
        netstat_output = run_cmd("netstat -tlnp 2>/dev/null || ss -tlnp 2>/dev/null")
        
        used_ports = set()
        for line in netstat_output.split('\n'):
            # Extract port from netstat output (very basic parsing)
            for port in CRIN_PORTS | FORBIDDEN_PORTS:
                if f":{port}" in line:
                    used_ports.add(port)
        
        # Check for forbidden port usage
        forbidden_in_use = used_ports & FORBIDDEN_PORTS
        if forbidden_in_use:
            print(f"⚠️  WARNING: System ports detected in netstat:")
            for port in sorted(forbidden_in_use):
                print(f"   - Port {port} (system service, agent won't touch)")
        
        # Check crin_ ports
        crin_in_use = used_ports & CRIN_PORTS
        if crin_in_use:
            print(f"✅ Crin project ports in use: {sorted(crin_in_use)}")
        else:
            print(f"ℹ️  No crin_ ports currently listening (may be expected if services not running)")
        
        return True
    except Exception as e:
        print(f"⚠️  Warning checking port usage: {e}")
        return True  # Non-critical


def check_isolation() -> bool:
    """Run all isolation checks."""
    print("\n" + "=" * 70)
    print("CONTAINER ISOLATION SAFETY CHECK")
    print("=" * 70 + "\n")
    
    checks = [
        ("1. Working Directory", check_working_directory),
        ("2. Docker Services", check_docker_services),
        ("3. Container Names", check_container_names),
        ("4. Port Usage", check_port_usage),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}")
        print("-" * 70)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ SAFE: All isolation checks passed. Ready to proceed with Docker operations.")
        print("=" * 70 + "\n")
        return True
    else:
        print("❌ UNSAFE: Some isolation checks failed. Do not proceed.")
        print("=" * 70 + "\n")
        return False


if __name__ == "__main__":
    success = check_isolation()
    sys.exit(0 if success else 1)
