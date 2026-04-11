"""
scripts/precompute_demo.py — Run all 3 demo scenarios and cache results.

Run this the night before the hackathon:
    cd backend
    python scripts/precompute_demo.py

Saves to cache/demo/:
  - alzheimers.json, schizophrenia.json, depression.json  (SSE event sequences)
  - *_expression.png, *_disease.png  (brain map PNGs)
"""
import asyncio
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

DEMO_DIR = os.getenv("DEMO_CACHE_DIR", "./cache/demo")
os.makedirs(DEMO_DIR, exist_ok=True)

SCENARIOS = [
    {
        "name": "alzheimers",
        "drug_query": "Chaetocin",
        "query_type": "name",
        "indication": "Alzheimer's disease"
    },
    {
        "name": "schizophrenia",
        "drug_query": "Tolcapone",
        "query_type": "name",
        "indication": "schizophrenia"
    },
    {
        "name": "depression",
        "drug_query": "Vorinostat",
        "query_type": "name",
        "indication": "major depressive disorder"
    },
]


async def precompute_scenario(scenario: dict) -> None:
    from agent.loop import run_agent_session

    session_id = f"demo_{scenario['name']}"
    queue = asyncio.Queue()
    events = []

    print(f"  Running agent for '{scenario['drug_query']}' / '{scenario['indication']}'...")

    # Run agent loop — this takes 1-3 minutes per scenario
    agent_task = asyncio.create_task(
        run_agent_session(
            session_id=session_id,
            drug_query=scenario["drug_query"],
            query_type=scenario["query_type"],
            indication=scenario["indication"],
            event_queue=queue
        )
    )

    # Collect events while agent runs
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=600.0)
            events.append(event)
            event_type = event.get("type", "")
            if event_type == "done":
                break
            elif event_type == "agent_thought":
                # Print dots to show progress
                print(".", end="", flush=True)
            elif event_type == "tool_call":
                print(f"\n  → {event.get('tool', '?')}", end="", flush=True)
            elif event_type == "tool_result":
                print(f"\n  ← {event.get('summary', '')[:60]}")
            elif event_type == "report_ready":
                print("\n  [REPORT READY]")
            elif event_type == "pdf_ready":
                print(f"  [PDF READY]: {event.get('filename', '')}")
        except asyncio.TimeoutError:
            print(f"\n  WARNING: Scenario '{scenario['name']}' timed out after 10 minutes")
            agent_task.cancel()
            break

    await agent_task

    # Save events to JSON
    events_to_save = [e for e in events if e.get("type") != "done"]
    output_json = os.path.join(DEMO_DIR, f"{scenario['name']}.json")
    with open(output_json, 'w') as f:
        json.dump(events_to_save, f, indent=2, default=str)
    print(f"\n  Saved {len(events_to_save)} events to {output_json}")

    # Copy brain map PNGs and PDF from session dir to demo dir
    sessions_dir = os.getenv("SESSIONS_DIR", "./sessions")
    for map_type in ["expression", "disease"]:
        src = os.path.join(sessions_dir, session_id, f"{map_type}.png")
        dst = os.path.join(DEMO_DIR, f"{scenario['name']}_{map_type}.png")
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Copied: {dst}")
        else:
            print(f"  WARNING: {src} not found — map may not have been generated")

    # Copy generated PDF to demo cache
    pdf_files = list(Path(os.path.join(sessions_dir, session_id)).glob("*.pdf"))
    if pdf_files:
        pdf_dst = os.path.join(DEMO_DIR, f"{scenario['name']}.pdf")
        shutil.copy2(str(pdf_files[0]), pdf_dst)
        print(f"  Copied: {pdf_dst}")
    else:
        print(f"  NOTE: No PDF in session dir — demo PDF will be generated on-the-fly on first request")


async def main():
    print(f"Precomputing demo scenarios → {os.path.abspath(DEMO_DIR)}\n")

    for scenario in SCENARIOS:
        print(f"{'='*60}")
        print(f"Scenario: {scenario['name'].upper()}")
        print(f"  Drug: {scenario['drug_query']} | Indication: {scenario['indication']}")
        print(f"{'='*60}")
        try:
            await precompute_scenario(scenario)
            print(f"Scenario '{scenario['name']}' COMPLETE\n")
        except Exception as e:
            print(f"\nScenario '{scenario['name']}' FAILED: {e}\n")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("All scenarios processed.")
    print(f"Demo cache: {os.path.abspath(DEMO_DIR)}")
    print("Files saved:")
    for f in sorted(os.listdir(DEMO_DIR)):
        fpath = os.path.join(DEMO_DIR, f)
        size = os.path.getsize(fpath)
        print(f"  {f} ({size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
