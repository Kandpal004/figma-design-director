"""
main.py — run the Design Director agent.

Usage:
    python agent/main.py "<task>" [expected_output_file]

If an expected_output_file is given, the driver nudges the agent to keep going until that
file exists (up to MAX_NUDGES). This defends against the agent treating synchronous
subagent (Task) results as if they were async and ending its turn early without building.

The agent's own job: extract real data -> research/UX audit -> pick references ->
improvement plan -> build ONE section -> slop gate -> present and STOP for your approval.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# UTF-8 console on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from claude_agent_sdk import ClaudeSDKClient  # noqa: E402
from config import build_options              # noqa: E402

MAX_NUDGES = 3

_NUDGE = (
    "You have NOT yet written the required deliverable file: {path}\n"
    "Important: your subagents (the Task tool) return their results SYNCHRONOUSLY — you do "
    "NOT wait for them in the background. Never say you'll 'wait' for a subagent; read its "
    "returned result immediately and continue in the same turn.\n"
    "Continue NOW: finish building the header, WRITE it to exactly that path as a complete "
    "standalone HTML file grounded in the real extracted fonts/colors/images, run "
    "run_slop_gate on it, fix anything it blocks, then stop for my approval."
)


async def _drain(client: ClaudeSDKClient) -> None:
    async for msg in client.receive_response():
        for block in getattr(msg, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                print(text, end="", flush=True)
    print()


async def run(task: str, expect_file: str | None = None) -> None:
    async with ClaudeSDKClient(options=build_options()) as client:
        await client.query(task)
        await _drain(client)

        nudges = 0
        while expect_file and not Path(expect_file).exists() and nudges < MAX_NUDGES:
            nudges += 1
            print(f"\n[driver] deliverable missing; nudge {nudges}/{MAX_NUDGES}\n", flush=True)
            await client.query(_NUDGE.format(path=expect_file))
            await _drain(client)

        if expect_file:
            ok = Path(expect_file).exists()
            print(f"\n[driver] deliverable {'WRITTEN' if ok else 'STILL MISSING'}: {expect_file}",
                  flush=True)


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python agent/main.py "<task>" [expected_output_file]')
        raise SystemExit(2)
    task = sys.argv[1]
    expect = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(run(task, expect))


if __name__ == "__main__":
    main()
