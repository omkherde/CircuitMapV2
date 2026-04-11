"""
agent/loop.py — Main agentic loop for CircuitMap.

Runs the Claude tool_use loop until:
  - The agent produces a final report (stop_reason == 'end_turn' with REPORT COMPLETE marker)
  - The tool call limit is reached (MAX_TOOL_CALLS)
  - An unrecoverable error occurs

All SSE events are emitted via the event_queue (asyncio.Queue).
"""
import asyncio
import json
import os
import time
from typing import AsyncGenerator

import anthropic

from agent.tools_schema import TOOLS
from agent.prompts import SYSTEM_PROMPT
from agent.tools import execute_tool

client = anthropic.Anthropic()

REPORT_MARKER = "TARGET VALIDATION REPORT COMPLETE"


async def run_agent_session(
    session_id: str,
    drug_query: str,
    query_type: str,
    indication: str,
    event_queue: asyncio.Queue
) -> None:
    """
    Main agentic loop. Streams events to event_queue throughout.

    Args:
        session_id: Unique session ID
        drug_query: Drug name or SMILES string
        query_type: 'name' or 'smiles'
        indication: Disease indication string
        event_queue: asyncio.Queue for SSE events
    """
    model = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")
    max_tool_calls = int(os.getenv("MAX_TOOL_CALLS", "20"))

    messages = [
        {
            "role": "user",
            "content": (
                f"Validate this CNS drug target for the following indication.\n\n"
                f"Drug input: {drug_query}\n"
                f"Input type: {query_type}\n"
                f"Disease indication: {indication}\n\n"
                f"Begin your investigation."
            )
        }
    ]

    tool_call_count = 0
    full_report_text = ""
    expression_map_id = None
    disease_map_id = None
    overlap_result = None
    report_emitted = False
    latest_target_result = None
    expression_results: dict[str, dict] = {}
    disease_result = None
    literature_result = None

    tool_limit_reached = False
    forced_wrapup_requested = False
    post_limit_tool_attempts = 0
    max_token_continuations = 0

    while True:
        full_text = ""
        tool_uses = []

        try:
            # Stream Claude's response
            with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            ) as stream:
                for text_chunk in stream.text_stream:
                    full_text += text_chunk
                    # Emit thought chunks to the trace panel
                    await event_queue.put({
                        "type": "agent_thought",
                        "content": text_chunk,
                        "timestamp": int(time.time())
                    })

                # IMPORTANT: get final message after context manager exits
                final_message = stream.get_final_message()

            stop_reason = final_message.stop_reason

            # Extract tool_use blocks from content
            for block in final_message.content:
                if block.type == "tool_use":
                    tool_uses.append(block)

            # Append assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": final_message.content
            })

        except anthropic.APIError as e:
            await event_queue.put({
                "type": "error",
                "message": f"Claude API error: {str(e)}",
                "recoverable": False,
                "timestamp": int(time.time())
            })
            return

        # ── Handle tool calls ─────────────────────────────────────────────
        if stop_reason == "tool_use" and tool_uses:
            tool_results = []

            if tool_limit_reached:
                post_limit_tool_attempts += 1
                for tool_block in tool_uses:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps({
                            "error": f"Tool call limit ({max_tool_calls}) already reached before executing '{tool_block.name}'."
                        })
                    })

                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                if post_limit_tool_attempts >= 2:
                    await event_queue.put({
                        "type": "error",
                        "message": "Agent requested additional tool calls after tool access was disabled.",
                        "recoverable": False,
                        "timestamp": int(time.time())
                    })
                    break

                forced_wrapup_requested = True
                messages.append({
                    "role": "user",
                    "content": (
                        "No more tool calls are available. "
                        "Write your final Target Validation Report now using only the evidence you already gathered. "
                        "Begin with 'TARGET VALIDATION REPORT COMPLETE' and use the exact required section headers."
                    )
                })
                continue

            skipped_tool_blocks = []

            for tool_block in tool_uses:
                if tool_call_count >= max_tool_calls:
                    tool_limit_reached = True
                    skipped_tool_blocks.append(tool_block)
                    break

                tool_call_count += 1

                # Emit tool_call event to the trace
                await event_queue.put({
                    "type": "tool_call",
                    "tool": tool_block.name,
                    "input": tool_block.input,
                    "timestamp": int(time.time())
                })

                # Execute tool (runs in thread pool)
                result_str = await execute_tool(
                    tool_name=tool_block.name,
                    tool_input=tool_block.input,
                    session_id=session_id,
                    event_queue=event_queue
                )

                # Track map IDs for PDF generation
                try:
                    result_dict = json.loads(result_str)
                    if tool_block.name == "get_brain_expression" and result_dict.get("map_id"):
                        expression_map_id = result_dict["map_id"]
                        expression_results[result_dict.get("gene_name", tool_block.input.get("gene_name", "unknown"))] = result_dict
                    elif tool_block.name == "get_disease_map" and result_dict.get("map_id"):
                        disease_map_id = result_dict["map_id"]
                        disease_result = result_dict
                    elif tool_block.name == "compute_overlap" and "r" in result_dict:
                        overlap_result = result_dict
                    elif tool_block.name == "resolve_target" and result_dict.get("primary_target"):
                        latest_target_result = result_dict
                    elif tool_block.name == "search_literature" and result_dict.get("results"):
                        literature_result = result_dict
                except json.JSONDecodeError:
                    pass

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result_str
                })

            if tool_limit_reached:
                remaining_blocks = tool_uses[len(tool_results) + len(skipped_tool_blocks):]
                skipped_tool_blocks.extend(remaining_blocks)

                for tool_block in skipped_tool_blocks:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps({
                            "error": f"Tool call limit ({max_tool_calls}) reached before executing '{tool_block.name}'."
                        })
                    })

            if tool_results:
                # Append tool results to conversation
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            # Hit tool call limit?
            if tool_limit_reached:
                await event_queue.put({
                    "type": "error",
                    "message": f"Tool call limit ({max_tool_calls}) reached. Forcing report generation.",
                    "recoverable": True,
                    "timestamp": int(time.time())
                })
                forced_wrapup_requested = True
                messages.append({
                    "role": "user",
                    "content": (
                        "You have reached the tool call limit. "
                        "Write your final Target Validation Report now with whatever evidence you have gathered. "
                        "Begin with 'TARGET VALIDATION REPORT COMPLETE' and use the exact required section headers. "
                        "Do not call any more tools."
                    )
                })
                continue

        # ── Handle end of conversation ────────────────────────────────────
        elif stop_reason == "max_tokens":
            max_token_continuations += 1
            if max_token_continuations > 2:
                await event_queue.put({
                    "type": "error",
                    "message": "Agent exceeded the token limit repeatedly while composing the report.",
                    "recoverable": False,
                    "timestamp": int(time.time())
                })
                break

            continue_prompt = (
                "Continue exactly where you left off and finish the Target Validation Report. "
                "Do not repeat completed text. "
                "Begin with 'TARGET VALIDATION REPORT COMPLETE' if you have not already done so. "
                "Use the exact required section headers. "
                "Do not call any more tools unless they are absolutely required."
            )
            if tool_limit_reached:
                continue_prompt += " No more tool calls are available."

            messages.append({
                "role": "user",
                "content": continue_prompt
            })
            continue

        elif stop_reason == "end_turn":
            full_report_text = full_text

            if REPORT_MARKER in full_report_text or _looks_like_structured_report(full_report_text):
                if REPORT_MARKER not in full_report_text:
                    full_report_text = f"{REPORT_MARKER}\n\n{full_report_text}"

                # Parse report sections
                report_sections = _parse_report_sections(full_report_text)

                # Emit confidence_update events parsed from the Confidence Assessment section
                for conf_event in _extract_confidence_events(report_sections):
                    await event_queue.put(conf_event)

                await event_queue.put({
                    "type": "report_ready",
                    "report_sections": report_sections,
                    "raw_report": full_report_text,
                    "timestamp": int(time.time())
                })
                report_emitted = True

                # Generate PDF
                try:
                    await _generate_and_emit_pdf(
                        session_id=session_id,
                        report_sections=report_sections,
                        full_report_text=full_report_text,
                        indication=indication,
                        event_queue=event_queue,
                        overlap_result=overlap_result
                    )
                except Exception as e:
                    await event_queue.put({
                        "type": "error",
                        "message": f"PDF generation failed: {e}",
                        "recoverable": True,
                        "timestamp": int(time.time())
                    })
            else:
                # Agent finished without producing a report — emit what we have
                await event_queue.put({
                    "type": "agent_thought",
                    "content": "\n[Agent completed without producing a structured report. Raw output above.]",
                    "timestamp": int(time.time())
                })
            break

        else:
            # Unexpected stop reason
            await event_queue.put({
                "type": "error",
                "message": f"Unexpected stop reason: {stop_reason}",
                "recoverable": False,
                "timestamp": int(time.time())
            })
            break

    if not report_emitted:
        fallback_sections = _build_fallback_report(
            target_result=latest_target_result,
            expression_results=expression_results,
            disease_result=disease_result,
            overlap_result=overlap_result,
            literature_result=literature_result,
            indication=indication,
        )

        if fallback_sections:
            raw_report = _report_sections_to_text(fallback_sections)

            for conf_event in _extract_confidence_events(fallback_sections):
                await event_queue.put(conf_event)

            await event_queue.put({
                "type": "report_ready",
                "report_sections": fallback_sections,
                "raw_report": raw_report,
                "timestamp": int(time.time())
            })

            try:
                await _generate_and_emit_pdf(
                    session_id=session_id,
                    report_sections=fallback_sections,
                    full_report_text=raw_report,
                    indication=indication,
                    event_queue=event_queue,
                    overlap_result=overlap_result
                )
            except Exception as e:
                await event_queue.put({
                    "type": "error",
                    "message": f"PDF generation failed: {e}",
                    "recoverable": True,
                    "timestamp": int(time.time())
                })


def _parse_report_sections(report_text: str) -> dict:
    """
    Parse the agent's final report text into a dict with frontend-normalized keys.

    Sections are delimited by '## ' headers. Keys are normalized to match the
    frontend's ReportSections TypeScript interface.
    """
    import re

    # Map PRD section headers → frontend snake_case keys
    HEADER_TO_KEY = {
        "executive summary": "executive_summary",
        "molecular target profile": "target_identification",
        "brain expression analysis": "expression_analysis",
        "functional circuit context": "circuit_interpretation",
        "target-pathology overlap": "spatial_overlap",
        "off-target risk assessment": "off_target_risk",
        "literature evidence summary": "literature_context",
        "recommended clinical endpoints": "recommendations",
        "confidence assessment": "confidence_assessment",
        "pre-clinical validation recommendations": "preclinical_validation",
        "data sources & limitations": "limitations",
        "data sources and limitations": "limitations",
        "limitations": "limitations",
        "references": "preclinical_validation",
    }

    # Find where the report starts (after REPORT_MARKER)
    marker_idx = report_text.find(REPORT_MARKER)
    report_body = report_text[marker_idx + len(REPORT_MARKER):].strip() if marker_idx >= 0 else report_text

    # Split on ## headers
    parts = re.split(r'\n## ', report_body)

    raw_sections = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        header = lines[0].strip().lstrip('#').strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        if header:
            raw_sections[header] = content

    # Normalize keys
    normalized = {}
    for header, content in raw_sections.items():
        key = HEADER_TO_KEY.get(header.lower().strip())
        if key:
            # If slot already taken (e.g. two sections map to same key), append
            if key in normalized:
                normalized[key] = normalized[key] + "\n\n" + content
            else:
                normalized[key] = content
        else:
            # Keep unknown sections under a sanitized key so nothing is lost
            fallback_key = re.sub(r'[^a-z0-9]+', '_', header.lower()).strip('_')
            normalized[fallback_key] = content

    return normalized


async def _generate_and_emit_pdf(
    session_id: str,
    report_sections: dict,
    full_report_text: str,
    indication: str,
    event_queue: asyncio.Queue,
    overlap_result: dict | None
) -> None:
    """Generate PDF and emit pdf_ready event."""
    import asyncio

    # Extract target from report sections
    target = _extract_target_from_report(report_sections, full_report_text)

    # Find image paths
    session_dir = os.path.join(os.getenv("SESSIONS_DIR", "./sessions"), session_id)
    expression_path = os.path.join(session_dir, "expression.png")
    disease_path = os.path.join(session_dir, "disease.png")

    # Run PDF generation in thread pool (synchronous ReportLab)
    loop = asyncio.get_event_loop()

    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)

    def _generate():
        from services.pdf_service import generate_pdf
        return generate_pdf(
            session_id=session_id,
            report_sections=report_sections,
            target=target,
            indication=indication,
            expression_image_path=expression_path if os.path.exists(expression_path) else None,
            disease_image_path=disease_path if os.path.exists(disease_path) else None,
            overlap_score=overlap_result
        )

    pdf_path = await loop.run_in_executor(executor, _generate)

    from datetime import date
    safe_indication = indication.replace(" ", "-").replace("'", "")
    filename = f"CircuitMap_{target}_{safe_indication}_{date.today().strftime('%Y-%m-%d')}.pdf"

    await event_queue.put({
        "type": "pdf_ready",
        "pdf_url": f"/api/report/{session_id}/download",
        "filename": filename,
        "timestamp": int(time.time())
    })


def _extract_confidence_events(report_sections: dict) -> list[dict]:
    """
    Parse the Confidence Assessment section and emit confidence_update SSE events.
    Handles formats like:
      "Target Resolution: HIGH - rationale"
      "Target resolution | HIGH | rationale"
    """
    section = report_sections.get("confidence_assessment", "")
    if not section:
        return []

    import re

    DIMENSION_MAP = {
        "target resolution": "target_resolution",
        "target": "target_resolution",
        "circuit alignment": "circuit_alignment",
        "circuit": "circuit_alignment",
        "literature support": "literature_support",
        "literature": "literature_support",
    }

    LEVEL_WORDS = {"HIGH", "MODERATE", "LOW"}

    events = []
    for line in section.split('\n'):
        line = line.strip().lstrip('-•*').strip()
        if not line:
            continue

        # Detect level
        level = None
        for lw in LEVEL_WORDS:
            if lw in line.upper():
                level = lw
                break
        if not level:
            continue

        # Detect dimension
        line_lower = line.lower()
        dimension = None
        for key, val in DIMENSION_MAP.items():
            if key in line_lower:
                dimension = val
                break
        if not dimension:
            continue

        # Extract rationale — everything after the level word
        rationale_match = re.search(r'(?:HIGH|MODERATE|LOW)[:\s\-–|]+(.+)', line, re.IGNORECASE)
        rationale = rationale_match.group(1).strip() if rationale_match else ""

        events.append({
            "type": "confidence_update",
            "dimension": dimension,
            "level": level,
            "rationale": rationale,
            "timestamp": int(time.time()),
        })

    return events


def _extract_target_from_report(report_sections: dict, full_text: str) -> str:
    """Extract target gene name from Molecular Target Profile section."""
    profile = report_sections.get("target_identification", "")
    if not profile:
        profile = full_text

    # Try to find gene name patterns (e.g., SUV39H1, COMT, HDAC2)
    import re
    # Look for uppercase gene symbols (2-8 letters/digits)
    matches = re.findall(r'\b([A-Z][A-Z0-9]{1,7})\b', profile[:300])
    # Filter out common non-gene words
    stop_words = {'THE', 'AND', 'OR', 'FOR', 'IN', 'IS', 'ARE', 'A', 'AN',
                  'CNS', 'DNA', 'RNA', 'CNS', 'HIGH', 'LOW', 'MODERATE',
                  'NOT', 'HAS', 'FROM', 'WITH', 'TARGET', 'CLASS', 'DATA'}
    for match in matches:
        if match not in stop_words and len(match) >= 3:
            return match
    return "Unknown"


def _looks_like_structured_report(text: str) -> bool:
    """Heuristic for accepting a report even if the model omitted the marker."""
    required_headers = [
        "## Executive Summary",
        "## Molecular Target Profile",
        "## Confidence Assessment",
    ]
    return sum(header in text for header in required_headers) >= 2


def _build_fallback_report(
    target_result: dict | None,
    expression_results: dict[str, dict],
    disease_result: dict | None,
    overlap_result: dict | None,
    literature_result: dict | None,
    indication: str,
) -> dict | None:
    """Synthesize a minimal report from tool outputs when the model omits one."""
    if not any([target_result, expression_results, disease_result, overlap_result, literature_result]):
        return None

    primary_target = (target_result or {}).get("primary_target", "Unknown")
    target_class = (target_result or {}).get("target_class", "Unknown")
    affinity = (target_result or {}).get("binding_affinity")
    affinity_type = (target_result or {}).get("affinity_type", "")
    off_targets = (target_result or {}).get("off_targets", [])

    expression_result = expression_results.get(primary_target) or next(iter(expression_results.values()), None)
    expression_regions = (expression_result or {}).get("top_regions", [])[:5]
    disease_regions = (disease_result or {}).get("top_regions", [])[:5]
    literature_hits = (literature_result or {}).get("results", [])[:3]

    if target_result:
        target_summary = [
            f"Primary target: {primary_target}",
            f"Target class: {target_class}",
        ]
        if affinity is not None:
            target_summary.append(f"Binding affinity: {affinity} nM ({affinity_type})")
        if off_targets:
            target_summary.append(
                "Notable off-targets: " + ", ".join(
                    f"{item.get('gene_name', 'Unknown')} ({item.get('binding_affinity', '?')} nM)"
                    for item in off_targets[:3]
                )
            )
        target_identification = "\n".join(target_summary)
    else:
        target_identification = "Target data unavailable in this session."

    if expression_regions:
        expression_analysis = (
            f"{expression_result.get('gene_name', primary_target)} expression is highest in: "
            + ", ".join(
                f"{region['region']} ({region.get('percentile', 0):.0f}th pct)"
                for region in expression_regions
            )
            + "."
        )
    else:
        expression_analysis = "Brain expression data was not available in this session."

    if disease_regions:
        circuit_interpretation = (
            f"{indication} anatomy was concentrated in: "
            + ", ".join(region["region"] for region in disease_regions)
            + "."
        )
    else:
        circuit_interpretation = f"No disease-anatomy map was available for {indication}."

    if overlap_result and "r" in overlap_result:
        spatial_overlap = (
            f"Spatial overlap r = {overlap_result.get('r', 0):.3f}, "
            f"{overlap_result.get('percentile', 0)}th percentile, "
            f"interpreted as {overlap_result.get('interpretation', 'unknown')} alignment."
        )
    else:
        spatial_overlap = "Spatial overlap could not be computed from the available maps."

    off_target_risk = (
        "Off-target liabilities were identified: "
        + ", ".join(
            f"{item.get('gene_name', 'Unknown')} ({item.get('binding_affinity', '?')} nM)"
            for item in off_targets[:3]
        )
        if off_targets else
        "No additional off-targets were captured in the available target-resolution output."
    )

    if literature_hits:
        literature_context = (
            "Top literature hits: "
            + "; ".join(
                f"{hit.get('title', 'Untitled')} ({hit.get('year', 'n.d.')})"
                for hit in literature_hits
            )
            + "."
        )
    else:
        literature_context = "No literature hits were available in this session."

    target_confidence = "HIGH" if target_result and target_result.get("confidence") == "confirmed" else "MODERATE"
    circuit_confidence = "LOW"
    if overlap_result and overlap_result.get("percentile", 0) >= 75:
        circuit_confidence = "HIGH"
    elif overlap_result and overlap_result.get("percentile", 0) >= 50:
        circuit_confidence = "MODERATE"
    elif expression_result and disease_result:
        circuit_confidence = "MODERATE"

    literature_confidence = "MODERATE" if literature_hits else "LOW"

    confidence_assessment = "\n".join([
        f"Target Resolution: {target_confidence} - Derived from the available target-resolution output.",
        f"Circuit Alignment: {circuit_confidence} - Based on the available expression, disease-map, and overlap evidence.",
        f"Literature Support: {literature_confidence} - Based on the retrieved local literature cache results.",
    ])

    executive_summary = (
        f"{primary_target} was identified as the leading target for the submitted molecule in the context of {indication}. "
        f"This fallback report was synthesized directly from tool outputs because the model did not return the required final report format."
    )

    return {
        "executive_summary": executive_summary,
        "target_identification": target_identification,
        "expression_analysis": expression_analysis,
        "circuit_interpretation": circuit_interpretation,
        "spatial_overlap": spatial_overlap,
        "off_target_risk": off_target_risk,
        "literature_context": literature_context,
        "recommendations": "Suggested clinical endpoints: cognition, disease MRI/fMRI, and a target-engagement biomarker.",
        "confidence_assessment": confidence_assessment,
        "preclinical_validation": (
            "Suggested next steps: confirm CNS exposure, validate selectivity, "
            "repeat disease-model testing, and verify chromatin or pathway engagement."
        ),
        "limitations": (
            "This report was auto-generated from intermediate tool outputs after the live model session ended "
            "without producing the required structured report marker."
        ),
    }


def _report_sections_to_text(report_sections: dict) -> str:
    """Render normalized report sections back into the canonical markdown report format."""
    ordered_sections = [
        ("Executive Summary", "executive_summary"),
        ("Molecular Target Profile", "target_identification"),
        ("Brain Expression Analysis", "expression_analysis"),
        ("Functional Circuit Context", "circuit_interpretation"),
        ("Target-Pathology Overlap", "spatial_overlap"),
        ("Off-Target Risk Assessment", "off_target_risk"),
        ("Literature Evidence Summary", "literature_context"),
        ("Recommended Clinical Endpoints", "recommendations"),
        ("Confidence Assessment", "confidence_assessment"),
        ("Pre-Clinical Validation Recommendations", "preclinical_validation"),
        ("Data Sources & Limitations", "limitations"),
    ]

    parts = [REPORT_MARKER]
    for header, key in ordered_sections:
        content = report_sections.get(key)
        if content:
            parts.append(f"## {header}\n{content}")
    return "\n\n".join(parts)
