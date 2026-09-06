#!/usr/bin/env python3
"""Exercise Agent Graph through the stdio proxy and keyed Unix-socket daemon."""
from __future__ import annotations

import argparse
import hashlib
import json
import selectors
import subprocess
import time
from pathlib import Path
from typing import Any


class McpClient:
    def __init__(self, proxy: Path, socket: Path, timeout: float) -> None:
        self.timeout = timeout
        self.next_id = 0
        self.process = subprocess.Popen(
            [str(proxy), "--socket", str(socket), "--connect-timeout-ms", "2000"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hwos-preformat-smoke", "version": "1"},
            },
        )
        self.notify("notifications/initialized", {})

    def _send(self, value: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.next_id += 1
        request_id = self.next_id
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        deadline = time.monotonic() + self.timeout
        assert self.process.stdout is not None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError(f"MCP request timed out: {method}")
            line = self.process.stdout.readline()
            if not line:
                stderr = ""
                if self.process.stderr is not None:
                    stderr = self.process.stderr.read()[-1000:]
                raise RuntimeError(f"proxy closed during {method}: {stderr}")
            response = json.loads(line)
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(f"MCP error for {method}: {response['error']}")
                return response

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        response = self.request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        result = response.get("result", {})
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        for item in result.get("content", []):
            if item.get("type") == "text":
                parsed = json.loads(item.get("text", "{}"))
                if isinstance(parsed, dict):
                    return parsed
        raise RuntimeError(f"tool returned no structured object: {name}")

    def tools(self) -> list[str]:
        response = self.request("tools/list", {})
        return [tool["name"] for tool in response["result"]["tools"]]

    def close(self) -> None:
        try:
            if self.process.stdin is not None:
                self.process.stdin.close()
            self.process.wait(timeout=5)
        except Exception:
            self.process.kill()
            self.process.wait(timeout=5)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", type=Path, required=True)
    parser.add_argument("--socket", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--mode", choices=("create", "verify"), required=True)
    parser.add_argument("--graph-id", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    client = McpClient(args.proxy, args.socket, args.timeout)
    started = time.monotonic()
    try:
        tools = client.tools()
        required = {
            "graph_create",
            "graph_execute",
            "graph_inspect",
            "graph_run_get",
            "graph_run_receipt",
            "graph_status",
        }
        missing = sorted(required.difference(tools))
        if missing:
            raise RuntimeError(f"required tools missing: {missing}")

        server = client.call("graph_status", {"resource": "server"})
        payload: dict[str, Any] = {
            "schema_version": 1,
            "kind": "agent-graph-keyed-daemon-proxy-smoke",
            "mode": args.mode,
            "graph_id": args.graph_id,
            "tool_count": len(tools),
            "required_tools_present": True,
            "proxy_sha256": sha256(args.proxy),
            "server_status": server.get("data", server),
        }

        if args.mode == "create":
            spec = {
                "name": args.graph_id,
                "entry": "start",
                "nodes": [{"id": "start", "type": "passthrough"}],
                "edges": [{"from": "start", "to": "END"}],
            }
            created = client.call("graph_create", {"spec": spec})
            executed = client.call(
                "graph_execute",
                {
                    "graph_id": args.graph_id,
                    "input": {"probe": "stdio-proxy-keyed-daemon"},
                    "mode": "sync",
                },
            )
            run_id = executed.get("run_id")
            if not run_id:
                raise RuntimeError(f"execution returned no run_id: {executed}")
            receipt = client.call("graph_run_receipt", {"run_id": run_id})
            data = executed.get("data", executed)
            if data.get("success") is not True:
                raise RuntimeError(f"execution did not succeed: {executed}")
            if data.get("final_state", {}).get("probe") != "stdio-proxy-keyed-daemon":
                raise RuntimeError(f"terminal state mismatch: {executed}")
            payload.update(
                {
                    "created": created,
                    "run_id": run_id,
                    "execution_success": True,
                    "terminal_state_verified": True,
                    "canonical_receipt_present": bool(receipt),
                }
            )
        else:
            if not args.run_id:
                raise RuntimeError("--run-id is required in verify mode")
            inspected = client.call("graph_inspect", {"graph_id": args.graph_id})
            run = client.call("graph_run_get", {"run_id": args.run_id})
            receipt = client.call("graph_run_receipt", {"run_id": args.run_id})
            run_data = run.get("data", run)
            if run_data.get("status") != "completed":
                raise RuntimeError(f"persisted run is not completed: {run}")
            payload.update(
                {
                    "run_id": args.run_id,
                    "graph_survived_restart": bool(inspected),
                    "run_survived_restart": True,
                    "canonical_receipt_survived_restart": bool(receipt),
                }
            )

        payload["elapsed_seconds"] = round(time.monotonic() - started, 3)
        payload["passed"] = True
        write_receipt(args.receipt, payload)
        print(json.dumps(payload, sort_keys=True))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
