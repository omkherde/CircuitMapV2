"""
agent/tools.py — Bridge between Claude tool_use calls and service implementations.

All service functions are synchronous and blocking; they are run in a thread pool
to avoid blocking FastAPI's async event loop.
"""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

_executor = ThreadPoolExecutor(max_workers=4)


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    session_id: str,
    event_queue: asyncio.Queue
) -> str:
    """
    Execute a named tool and emit SSE events to the event queue.

    All tools are synchronous — run them in a thread pool.
    Returns a JSON string result to be included in the Claude message.
    """
    tool_functions = {
        "resolve_target": _resolve_target,
        "get_brain_expression": _get_brain_expression,
        "get_cognitive_associations": _get_cognitive_associations,
        "get_disease_map": _get_disease_map,
        "compute_overlap": _compute_overlap,
        "search_literature": _search_literature,
    }

    if tool_name not in tool_functions:
        error = {"error": f"Unknown tool: {tool_name}"}
        await event_queue.put({
            "type": "tool_result",
            "tool": tool_name,
            "summary": f"Error: unknown tool '{tool_name}'"
        })
        return json.dumps(error)

    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(
            _executor,
            lambda: tool_functions[tool_name](tool_input, session_id, event_queue)
        )

        # Emit summary event for the reasoning trace
        summary = _summarize_result(tool_name, result)
        await event_queue.put({
            "type": "tool_result",
            "tool": tool_name,
            "summary": summary,
            "result": result
        })

        # Emit brain_map event if applicable
        if tool_name in ("get_brain_expression", "get_disease_map"):
            if result.get("image_path") and result.get("map_id"):
                map_type = "expression" if tool_name == "get_brain_expression" else "disease"
                await event_queue.put({
                    "type": "brain_map",
                    "map_type": map_type,
                    "map_id": result["map_id"],
                    "image_url": f"/api/maps/{session_id}/{map_type}.png",
                    "top_regions": result.get("top_regions", [])
                })

        # Emit overlap_score event
        if tool_name == "compute_overlap" and "r" in result:
            await event_queue.put({
                "type": "overlap_score",
                "r": result["r"],
                "percentile": result["percentile"],
                "label": result.get("label", ""),
                "interpretation": result.get("interpretation", "")
            })

        return json.dumps(result, default=str)

    except Exception as e:
        error_result = {"error": str(e), "tool": tool_name}
        await event_queue.put({
            "type": "tool_result",
            "tool": tool_name,
            "summary": f"Error in {tool_name}: {str(e)}"
        })
        return json.dumps(error_result)


def _summarize_result(tool_name: str, result: dict) -> str:
    """Generate a human-readable one-line summary for the reasoning trace panel."""
    if "error" in result and not result.get("primary_target"):
        return f"Error: {result['error']}"

    summaries = {
        "resolve_target": lambda r: (
            f"Target: {r.get('primary_target', 'unknown')} | "
            f"Affinity: {r.get('binding_affinity', '?')} nM ({r.get('affinity_type', '')})"
            if r.get('primary_target') else f"No target found: {r.get('error', '')}"
        ),
        "get_brain_expression": lambda r: (
            f"Top region: {r['top_regions'][0]['region']} "
            f"({r['top_regions'][0]['percentile']:.0f}th pct) | "
            f"Atlas: {r.get('atlas', 'DK')}"
            if r.get('top_regions') else f"No data: {r.get('error', '')}"
        ),
        "get_cognitive_associations": lambda r: (
            f"Top functions: {', '.join([a['function'] for a in r.get('cognitive_associations', [])[:3]])}"
            if r.get('cognitive_associations') else "No associations found"
        ),
        "get_disease_map": lambda r: (
            f"Term: '{r.get('neurosynth_term', '?')}' | "
            f"Studies: {r.get('n_studies', 0)} | "
            f"Top region: {r['top_regions'][0]['region']}"
            if r.get('top_regions') else f"No data: {r.get('error', '')}"
        ),
        "compute_overlap": lambda r: (
            f"r = {r.get('r', 0):.3f} | "
            f"Percentile: {r.get('percentile', 0)}th | "
            f"Alignment: {r.get('interpretation', 'unknown')} | "
            f"n_regions = {r.get('n_regions', 0)}"
        ),
        "search_literature": lambda r: (
            f"Found {r.get('total_results', 0)} abstracts | "
            f"Top: {r['results'][0]['title'][:60]}..."
            if r.get('results') else "No abstracts found or RAG not initialized"
        ),
    }

    fn = summaries.get(tool_name, lambda r: str(r)[:120])
    try:
        return fn(result)
    except Exception:
        return str(result)[:120]


# ── Service wrappers ──────────────────────────────────────────────────────────

def _resolve_target(inp: dict, session_id: str, eq) -> dict:
    from services.chembl_service import resolve_target
    return resolve_target(inp["query"], inp["query_type"])


def _get_brain_expression(inp: dict, session_id: str, eq) -> dict:
    from services.ahba_service import get_expression_map
    return get_expression_map(inp["gene_name"], session_id)


def _get_cognitive_associations(inp: dict, session_id: str, eq) -> dict:
    from services.neurosynth_service import get_cognitive_associations
    return get_cognitive_associations(inp["regions"], inp.get("top_n", 8))


def _get_disease_map(inp: dict, session_id: str, eq) -> dict:
    from services.neurosynth_service import get_disease_map
    return get_disease_map(inp["indication"], session_id)


def _compute_overlap(inp: dict, session_id: str, eq) -> dict:
    from services.correlation_service import compute_overlap
    return compute_overlap(inp["map1_id"], inp["map2_id"], inp.get("label", ""))


def _search_literature(inp: dict, session_id: str, eq) -> dict:
    from services.rag_service import search_literature
    return search_literature(inp["query"], inp.get("top_k", 5))
