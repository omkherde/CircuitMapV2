# CircuitMap — Product Requirements Document

**Version:** 1.0  
**Date:** April 11, 2026  
**Status:** Ready to Build  
**Hackathon:** Advanced AI Systems — Texas Momentum & Texas Genesis, UT Austin

---

## 1. Product Overview

### 1.1 One-Sentence Description
CircuitMap is an autonomous AI agent that validates CNS drug targets by tracing the path from a drug molecule to its brain circuit impact, producing a structured Target Validation Report in minutes rather than the 6 weeks and $200,000 a consultant team currently requires.

### 1.2 The Problem
95% of CNS drugs that enter clinical trials fail. The leading cause is not failed chemistry — it is failed target selection. Researchers identify a promising molecule, confirm it binds to a target in vitro, and commit $50–200 million to a clinical program before anyone has mapped that target to the brain circuits relevant to the disease they are trying to treat.

The tools that exist today operate in silos:
- **Schrödinger / AutoDock**: molecular docking, binding prediction — stops at the protein
- **BenevolentAI / Insilico Medicine**: target identification from literature — no circuit mapping
- **Manual consultant process**: 6 weeks, $150,000–$200,000, no standardized output

No software tool today bridges the gap between "this molecule binds this protein" and "this protein lives in the brain circuits that matter for this disease." That gap is CircuitMap.

### 1.3 The Solution
CircuitMap is a multi-tool autonomous reasoning agent built on Claude's tool_use API. Given a drug molecule (SMILES string or name) and a disease indication, the agent:

1. Resolves the molecular target from validated databases
2. Maps the target's anatomical distribution across the human brain
3. Infers which cognitive circuits that anatomy implicates
4. Quantifies spatial alignment between target anatomy and disease pathology
5. Searches primary literature to resolve uncertainties
6. Generates a structured Target Validation Report with confidence ratings

The agent reasons between each step — it is not a fixed pipeline. It can investigate multiple targets, flag contradictions, loop back to gather more evidence, and decide when it has sufficient confidence to write the report. This is what "Advanced AI Systems" means: the AI is making scientific decisions, not executing a script.

### 1.4 Scientific Positioning
CircuitMap provides **pre-clinical computational target contextualization** — the same category of evidence as gene expression studies and structural bioinformatics, not a replacement for clinical trials. All outputs are explicitly framed as pre-clinical signals analogous to in vitro screening: they reduce risk before committing to expensive human studies, but do not predict clinical outcomes.

All data sources used are peer-reviewed and widely cited:
- Allen Human Brain Atlas (Nature, Hawrylycz et al. 2012)
- abagen library (NeuroImage, Markello et al. 2021)
- Neurosynth (Nature Methods, Yarkoni et al. 2011)
- Spatial correlation method (Nature Neuroscience, Arnatkevičiūtė et al. 2021)
- ChEMBL (Nucleic Acids Research, Mendez et al. 2019)

---

## 2. Target Users

### 2.1 Primary User: Head of Research / VP R&D at CNS Biotech
**Profile:** Leads drug discovery at a Series A–C CNS biotech company. Has 3–8 active programs. Makes go/no-go decisions on which targets to advance to IND filing.

**Pain:** Currently pays consultants or internal neuroscientists 4–6 weeks per target assessment. Reports are inconsistent in quality and methodology. Has no standardized, reproducible way to compare target positioning across programs.

**Trigger to buy:** Upcoming IND filing within 6 months and needs to defend target selection rationale to FDA or investors.

**Willingness to pay:** $20,000 per validation report, or $75,000/year subscription for unlimited reports.

**Named examples:** Neumora Therapeutics (VP Translational Science), Alto Neuroscience (Head of R&D), Karuna Therapeutics/BMS CNS division, Cerevel Therapeutics, Sage Therapeutics, Compass Pathways, ATAI Life Sciences.

### 2.2 Secondary User: Academic PI with SBIR/STTR Grant
**Profile:** Neuroscience or pharmacology professor at an R1 university, commercializing a target discovery. Has limited budget, often working alone or with 1–2 postdocs.

**Pain:** No time or expertise to do a full manual target assessment. Needs the evidence for a grant renewal or a seed-stage investor pitch.

**Trigger to buy:** Grant renewal, investor pitch, or licensing discussion.

**Willingness to pay:** $5,000–$10,000 per report (academic pricing tier).

### 2.3 Tertiary User: Neurotech VC Analyst
**Profile:** Analyst at a venture fund focused on biotech/neurotech. Evaluates 50+ CNS biotech decks per year.

**Pain:** Has to evaluate scientific validity of target claims without a neuroscience PhD on staff. Currently relies on external advisors.

**Trigger to buy:** Diligence on a new investment opportunity.

**Willingness to pay:** $2,000–$5,000 per on-demand report during diligence.

---

## 3. Success Metrics (Hackathon Demo)

| Metric | Target |
|--------|--------|
| End-to-end agent run time | < 90 seconds for demo scenario |
| Tool calls per session | 4–8 (demonstrates genuine multi-step reasoning) |
| Reasoning trace steps visible | ≥ 6 visible reasoning steps in UI |
| Report PDF generation | Working and downloadable |
| Demo stability | 3 pre-computed fallback scenarios if live run fails |
| Judges' Q&A survival | Every scientific claim backed by a citable source |

---

## 4. Demo Scenarios (Exact, Pre-Computed)

Three scenarios must be pre-run and cached before the hackathon. These are the only scenarios used in the live demo. Do not attempt novel compounds live.

### Scenario 1: SUV39H1 / Alzheimer's Disease (Primary Demo)
- **Input drug:** Chaetocin (SUV39H1 inhibitor) — SMILES: `C1CC2=C(C1)NC3=CC=CC=C3N2` (simplified; use actual chaetocin SMILES)
- **Input indication:** "Alzheimer's disease"
- **Expected target resolution:** SUV39H1, Ki ≈ 0.8 µM (ChEMBL)
- **Expected top expression regions:** Hippocampus, entorhinal cortex, prefrontal cortex
- **Expected overlap score:** r ≈ 0.55–0.65, 85th–92nd percentile
- **Expected confidence:** HIGH for hippocampal engagement, MODERATE for off-target cerebellar expression
- **Key demo moment:** Agent discovers moderate cerebellar expression, calls search_literature, finds no adverse cerebellar signals, adjusts confidence upward

### Scenario 2: COMT / Schizophrenia (Backup Demo)
- **Input drug:** Tolcapone (COMT inhibitor) — drug name input
- **Input indication:** "schizophrenia"
- **Expected target:** COMT, known inhibitor
- **Expected top regions:** Prefrontal cortex, striatum, limbic system
- **Expected overlap:** r ≈ 0.50–0.60, 80th–88th percentile
- **Key moment:** Agent notes Val158Met polymorphism relevance, searches literature, flags patient stratification as recommendation

### Scenario 3: HDAC2 / Major Depressive Disorder (Backup)
- **Input drug:** Vorinostat (HDAC inhibitor) — drug name input
- **Input indication:** "major depression"
- **Expected target:** HDAC2 (primary class II HDAC)
- **Expected top regions:** Hippocampus, amygdala, anterior cingulate
- **Key moment:** Agent identifies dual HDAC1/HDAC2 activity, searches for selectivity literature, flags as moderate confidence

---

## 5. Core Features

### 5.1 Feature: Molecule Input
**Description:** The entry point for the agent. Accepts either a SMILES string (for novel/experimental compounds) or a plain English drug/compound name (for known drugs).

**Requirements:**
- Text input field labeled "Drug molecule" with placeholder "Enter SMILES string or drug name (e.g., Donepezil)"
- Radio toggle: "SMILES" | "Drug name" — defaults to "Drug name"
- Dropdown: "Disease indication" — pre-populated with 12 options: Alzheimer's disease, Parkinson's disease, Schizophrenia, Major depressive disorder, Bipolar disorder, PTSD, Epilepsy, ALS, Huntington's disease, Treatment-resistant depression, Anxiety disorders, Frontotemporal dementia
- "Validate Target" primary button — disabled until both fields are filled
- "Load Demo" secondary button — loads Scenario 1 pre-filled values
- SMILES input: monospace font, no spell-check, max 500 characters
- Drug name input: autocomplete not required, max 100 characters
- On submit: disable form, show loading state, begin agent session

**Validation:**
- SMILES input: basic format validation (must start with a valid SMILES character, no empty string)
- Drug name: must be at least 3 characters
- Indication: must be selected from dropdown
- If validation fails: show inline error message in red below the field

### 5.2 Feature: Live Reasoning Trace Panel
**Description:** The hero UI component. Streams the agent's internal reasoning and tool calls in real time as the agent works. This is what makes the demo unforgettable.

**Requirements:**
- Panel appears immediately when agent session starts
- Auto-scrolls to latest entry
- Four distinct event types with visual differentiation:

| Event Type | Color | Prefix | Example |
|------------|-------|--------|---------|
| `agent_thought` | Default text, slightly muted | — (no prefix) | "I've identified two possible targets. Let me evaluate binding affinity..." |
| `tool_call` | Blue/info text | `→ calling` | `→ calling get_brain_expression("SUV39H1")` |
| `tool_result` | Green/success text | `←` | `← Hippocampus: 98th percentile expression` |
| `confidence_flag` | Amber for MODERATE, green for HIGH, red for LOW | `[CONFIDENCE]` | `[CONFIDENCE: MODERATE] Cerebellar expression warrants literature review` |

- Monospace font for tool_call and tool_result lines
- Regular (sans) font for agent_thought lines
- Each entry appears with a subtle fade-in animation (opacity 0 → 1, 150ms)
- Panel height: fixed at 320px with vertical scroll
- Do NOT show raw JSON — extract human-readable summaries from tool results
- Show a pulsing dot indicator while agent is actively thinking (between tool results and next thought)

**Streaming:** Uses Server-Sent Events (SSE). Each event is a JSON object with `{type, content, timestamp}`.

### 5.3 Feature: Brain Map Display
**Description:** Renders the brain expression heatmap and disease anatomy map side by side as pre-rendered PNG images (generated by Nilearn on the backend).

**Requirements:**
- Two panels side by side: "Target expression" (left) | "Disease anatomy" (right)
- Each panel: 320px wide × 200px tall
- Images appear when the corresponding tool call completes (not before)
- Before image loads: gray placeholder with text "Awaiting [expression/disease] map..."
- After image loads: smooth fade-in (opacity 0 → 1, 300ms)
- Below the images: overlap score bar
  - Label: "Target-Pathology Overlap Score"
  - Show: r value (e.g., r = 0.61) + percentile badge (e.g., "89th percentile")
  - Color coding: ≥75th percentile = green, 50–74th = amber, <50th = red
  - Animated bar fill from 0% to percentile value when score appears
- Maps generated by Nilearn using `plot_stat_map()` with `display_mode='z'`, 4 axial cuts, `cmap='RdBu_r'` for expression, `cmap='viridis'` for disease map
- Map images saved as PNG at 150 DPI, 640×400px

### 5.4 Feature: Confidence Assessment Display
**Description:** A structured confidence panel that shows the agent's self-assessed confidence across three dimensions, updated dynamically as the agent works.

**Requirements:**
- Three rows, each with label + confidence badge + one-line rationale
- Rows: "Target resolution" | "Circuit alignment" | "Literature support"
- Each badge: HIGH (green) | MODERATE (amber) | LOW (red) | PENDING (gray)
- Badges start as PENDING and update when agent assigns them
- Each row has a 1-sentence rationale that appears when the badge is set
- Panel appears collapsed initially, expands when first confidence update arrives

### 5.5 Feature: Target Validation Report
**Description:** The structured final output that the agent produces. Appears in a scrollable panel on the right side of the screen after the agent completes.

**Required report sections (must all appear, in this order):**

1. **Executive Summary** — 3 sentences maximum. What the target is, what the evidence shows, and the overall recommendation (advance / advance with caution / deprioritize).
2. **Molecular Target Profile** — target gene name, protein class, binding affinity (Ki/IC50), data source (ChEMBL accession number), and whether any off-targets were identified.
3. **Brain Expression Analysis** — table of top 8 brain regions by expression percentile. Columns: Region | Expression percentile | Circuit role.
4. **Functional Circuit Context** — the cognitive and behavioral functions Neurosynth associates with the high-expression regions. Written as prose, not a list.
5. **Target-Pathology Overlap** — the spatial correlation coefficient, percentile rank, and interpretation ("This score indicates that the target's anatomical distribution shows [strong/moderate/weak] alignment with the neuroanatomical signature of [indication]").
6. **Off-Target Risk Assessment** — any brain regions with high expression that are not part of the therapeutic target circuits. Each flagged region includes: region name, expression percentile, associated function, and risk level (HIGH/MODERATE/LOW).
7. **Literature Evidence Summary** — 3–5 bullet points summarizing what the RAG search returned, with citations in the format [Author et al., Year, Journal].
8. **Recommended Clinical Endpoints** — 3–5 specific cognitive or neuroimaging endpoints appropriate for the indication and circuit context (e.g., "CANTAB paired-associate learning task: sensitive to hippocampal-dependent memory, directly relevant to the SUV39H1 → BDNF → LTP pathway").
9. **Confidence Assessment** — final table: Dimension | Rating | Rationale.
10. **Pre-Clinical Validation Recommendations** — 3 specific next steps the research team should take before committing to IND (e.g., "Measure H3K9me3 levels in post-mortem Alzheimer's hippocampal tissue to confirm target engagement pathway").
11. **Data Sources & Limitations** — list all data sources used with version/access date. One paragraph of honest limitations.

### 5.6 Feature: PDF Export
**Description:** A one-click export of the full report as a professionally formatted PDF.

**Requirements:**
- "Export Report PDF" button appears when report is complete
- PDF filename format: `CircuitMap_[TargetGene]_[Indication]_[YYYY-MM-DD].pdf`
- PDF includes: CircuitMap logo/header, all 11 report sections, both brain map images embedded, confidence assessment table, footer with "Generated by CircuitMap — Pre-clinical computational evidence only. Not for clinical use."
- PDF page size: A4
- PDF fonts: Helvetica for body, Helvetica-Bold for headers
- PDF generation: backend via ReportLab; PDF is streamed directly to browser as download
- Target: < 5 seconds from button click to download start

### 5.7 Feature: Demo Mode
**Description:** Loads pre-computed results instantly for hackathon demo stability.

**Requirements:**
- "Load Demo" button on the input form
- Loads Scenario 1 (SUV39H1 / Alzheimer's) with pre-filled form values
- On "Validate Target" click in demo mode: plays back pre-recorded reasoning trace at 800ms intervals per entry (simulating live streaming but using cached data)
- Brain maps load from pre-computed PNG cache
- Report loads from pre-computed JSON
- Demo mode indicator: subtle badge "Demo mode" visible in top-right corner
- Demo mode should be INDISTINGUISHABLE from a live run in appearance

---

## 6. Agent System Specification

### 6.1 Agent Architecture
The agent is a multi-turn Claude conversation with tool_use enabled. The backend maintains conversation state in memory for the duration of a session. There is no persistent database for conversation history — sessions are ephemeral.

**Model:** `claude-opus-4-6` (highest reasoning capability)  
**Max tokens:** 4096 per turn  
**Max tool calls per session:** 20 (hard limit to prevent runaway loops)  
**Session timeout:** 5 minutes from last activity  
**Streaming:** Yes — use `stream=True` with SSE

### 6.2 System Prompt (Complete)

```
You are CircuitMap, an autonomous CNS drug target validation agent built to help biotech researchers assess whether a drug molecule's target is anatomically, functionally, and scientifically positioned to treat a neurological or psychiatric indication.

You have access to six tools. You are NOT following a fixed pipeline — you are doing science. Call tools in whatever order makes scientific sense based on what you discover. You may call the same tool multiple times with different inputs.

## Your Scientific Reasoning Framework

1. ALWAYS begin by resolving the molecular target with high confidence before any other step
2. Assess brain-wide expression to understand the anatomical context — this tells you WHERE the drug acts
3. Map functional implications from the anatomy — this tells you WHAT those regions do
4. Quantify spatial alignment between target anatomy and disease pathology — this tells you HOW WELL POSITIONED the target is
5. Search literature to resolve specific uncertainties — do this proactively, not just when stuck
6. Assign confidence levels honestly based on convergent evidence

## Decision Rules

When you encounter multiple possible targets: evaluate all, weight by binding affinity, explicitly note off-targets in your reasoning
When brain expression is unexpectedly low: flag this as a concern, consider searching for downstream pathway members
When you see high expression in cerebellum or brainstem: ALWAYS search literature for adverse effect signals before writing the report
When the overlap score is below the 50th percentile: explicitly flag as potential target-indication mismatch
When literature evidence contradicts anatomical evidence: note the conflict explicitly and explain how it affects your confidence

## Scientific Standards You Must Uphold

- NEVER claim the drug will work — you are assessing target positioning, not predicting efficacy
- ALWAYS distinguish mRNA expression (what abagen provides) from protein density or functional activity
- ALWAYS frame all outputs as pre-clinical computational evidence
- ALWAYS cite the data source for every specific claim
- Binding affinity data from ChEMBL reflects in vitro conditions and may not translate to in vivo
- Gene expression from AHBA reflects post-mortem tissue from healthy adults, not disease brain

## Confidence Rating Definitions

HIGH: Multiple convergent data sources support the claim (expression + functional association + literature)
MODERATE: Good anatomical evidence but limited literature support, or minor contradictions present
LOW: Weak anatomical alignment, contradictory literature, or significant methodological limitations

## Output Format for Final Report

When you have sufficient evidence, produce your report using the following exact section headers:
## Executive Summary
## Molecular Target Profile
## Brain Expression Analysis
## Functional Circuit Context
## Target-Pathology Overlap
## Off-Target Risk Assessment
## Literature Evidence Summary
## Recommended Clinical Endpoints
## Confidence Assessment
## Pre-Clinical Validation Recommendations
## Data Sources & Limitations

Begin each report with "TARGET VALIDATION REPORT COMPLETE" on its own line so the system knows to render the report panel.
```

### 6.3 Tool Schemas (Exact Definitions)

**Tool 1: resolve_target**
```json
{
  "name": "resolve_target",
  "description": "Given a SMILES string or drug name, query ChEMBL and PubChem to identify the primary CNS target gene/protein and retrieve binding affinity data. Returns up to 3 targets ordered by binding affinity.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "SMILES string or drug/compound name to look up"
      },
      "query_type": {
        "type": "string",
        "enum": ["smiles", "name"],
        "description": "Whether the query is a SMILES string or a drug name"
      }
    },
    "required": ["query", "query_type"]
  }
}
```

**Tool 2: get_brain_expression**
```json
{
  "name": "get_brain_expression",
  "description": "Query the Allen Human Brain Atlas via abagen to retrieve regional mRNA expression data for a specific gene across brain regions. Returns the top 10 regions by expression percentile and a map_id for use in compute_overlap.",
  "input_schema": {
    "type": "object",
    "properties": {
      "gene_name": {
        "type": "string",
        "description": "Official HGNC gene symbol in uppercase (e.g., SUV39H1, COMT, HDAC2, BDNF)"
      }
    },
    "required": ["gene_name"]
  }
}
```

**Tool 3: get_cognitive_associations**
```json
{
  "name": "get_cognitive_associations",
  "description": "Query Neurosynth reverse inference to return cognitive and behavioral functions most strongly associated with a list of brain regions. Use after get_brain_expression to understand what the high-expression regions do functionally.",
  "input_schema": {
    "type": "object",
    "properties": {
      "regions": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of brain region names from get_brain_expression results (e.g., ['hippocampus', 'entorhinal cortex', 'prefrontal cortex'])"
      },
      "top_n": {
        "type": "integer",
        "description": "Number of top cognitive associations to return. Default: 8",
        "default": 8
      }
    },
    "required": ["regions"]
  }
}
```

**Tool 4: get_disease_map**
```json
{
  "name": "get_disease_map",
  "description": "Query Neurosynth for a meta-analytic brain activation map associated with a disease or clinical condition. Returns the top implicated regions and a map_id for use in compute_overlap.",
  "input_schema": {
    "type": "object",
    "properties": {
      "indication": {
        "type": "string",
        "description": "Disease or clinical condition in Neurosynth-compatible format (e.g., 'alzheimer', 'schizophrenia', 'depression', 'parkinson'). Use lowercase single words when possible."
      }
    },
    "required": ["indication"]
  }
}
```

**Tool 5: compute_overlap**
```json
{
  "name": "compute_overlap",
  "description": "Compute the spatial Pearson correlation between two brain maps using parcellated regional vectors. Returns correlation coefficient r and percentile rank vs. 1000 null permutations. Both maps must be from previous tool calls in this session.",
  "input_schema": {
    "type": "object",
    "properties": {
      "map1_id": {
        "type": "string",
        "description": "The map_id returned by get_brain_expression (expression map)"
      },
      "map2_id": {
        "type": "string",
        "description": "The map_id returned by get_disease_map (disease map)"
      },
      "label": {
        "type": "string",
        "description": "Human-readable label for this comparison (e.g., 'SUV39H1 expression vs Alzheimer disease anatomy')"
      }
    },
    "required": ["map1_id", "map2_id", "label"]
  }
}
```

**Tool 6: search_literature**
```json
{
  "name": "search_literature",
  "description": "Query the pre-embedded PubMed RAG vector store to retrieve relevant abstracts about a target-disease relationship or specific scientific question. Use to resolve uncertainties, check safety signals, or gather mechanism evidence.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Scientific question or search query (e.g., 'SUV39H1 inhibition hippocampus memory Alzheimer', 'COMT Val158Met schizophrenia prefrontal')"
      },
      "top_k": {
        "type": "integer",
        "description": "Number of abstracts to retrieve. Default: 5. Max: 10.",
        "default": 5
      }
    },
    "required": ["query"]
  }
}
```

### 6.4 Agentic Loop Behavior
The backend runs the following loop until the agent produces a final report or hits the 20-tool-call limit:

```
1. Send user task + system prompt to Claude with all 6 tools defined
2. Stream Claude's response
3. For each text chunk: emit SSE event {type: "agent_thought", content: chunk}
4. When stop_reason == "tool_use":
   a. For each tool_use block in response:
      - Emit SSE event {type: "tool_call", tool: name, input: input}
      - Execute the tool
      - Emit SSE event {type: "tool_result", tool: name, result: summary}
      - If tool returned a brain map: emit {type: "brain_map", ...}
   b. Append assistant message + tool results to conversation
   c. Call Claude again (loop)
5. When stop_reason == "end_turn":
   - Parse the final text for "TARGET VALIDATION REPORT COMPLETE"
   - Extract report sections
   - Emit SSE event {type: "report_ready", report_data: parsed_report}
   - Generate PDF
   - Emit SSE event {type: "pdf_ready", pdf_url: url}
   - Close SSE stream
```

---

## 7. API Specification

### POST /api/validate
Starts an agent session.

**Request body:**
```json
{
  "drug_query": "Chaetocin",
  "query_type": "name",
  "indication": "Alzheimer's disease"
}
```

**Response:**
```json
{
  "session_id": "uuid-v4",
  "stream_url": "/api/stream/uuid-v4",
  "mode": "live"
}
```

### GET /api/stream/{session_id}
SSE stream. Content-Type: `text/event-stream`

**Event types:**
```
event: agent_thought
data: {"content": "I've identified two possible targets...", "timestamp": 1234567890}

event: tool_call
data: {"tool": "get_brain_expression", "input": {"gene_name": "SUV39H1"}, "timestamp": 1234567890}

event: tool_result
data: {"tool": "get_brain_expression", "summary": "Peak expression: hippocampus (98th pct), entorhinal cortex (94th pct)", "timestamp": 1234567890}

event: brain_map
data: {"map_type": "expression", "gene": "SUV39H1", "image_url": "/api/maps/session-id/expression.png", "top_regions": [...], "timestamp": 1234567890}

event: brain_map
data: {"map_type": "disease", "indication": "Alzheimer's disease", "image_url": "/api/maps/session-id/disease.png", "top_regions": [...], "timestamp": 1234567890}

event: overlap_score
data: {"r": 0.61, "percentile": 89, "label": "SUV39H1 vs Alzheimer anatomy", "timestamp": 1234567890}

event: confidence_update
data: {"dimension": "target_resolution", "level": "HIGH", "rationale": "SUV39H1 confirmed with Ki=0.8µM from ChEMBL CHEMBL123456", "timestamp": 1234567890}

event: report_ready
data: {"report_sections": {...}, "timestamp": 1234567890}

event: pdf_ready
data: {"pdf_url": "/api/report/session-id/download", "filename": "CircuitMap_SUV39H1_Alzheimers_2026-04-11.pdf", "timestamp": 1234567890}

event: error
data: {"message": "ChEMBL returned no results for query. Try a different name.", "recoverable": true, "timestamp": 1234567890}
```

### GET /api/report/{session_id}/download
Returns PDF as `application/pdf` with Content-Disposition: attachment.

### GET /api/demo/{scenario}
Returns pre-computed session data. Scenario values: `alzheimers` | `schizophrenia` | `depression`

**Response:** Same structure as a completed session — pre-recorded trace events, pre-computed brain maps, pre-generated report. The frontend replays this data at 800ms intervals.

### GET /api/maps/{session_id}/{map_type}.png
Serves brain map PNG. Map type: `expression` | `disease`

### GET /api/health
Returns `{"status": "ok", "ahba_loaded": bool, "chroma_loaded": bool}`

---

## 8. UI Layout Specification

### 8.1 Overall Layout
Three-panel layout on a single page. No tabs, no navigation. Everything visible simultaneously once a session starts.

```
┌─────────────────────────────────────────────────────────────────┐
│  CircuitMap                                          [Demo]      │
├──────────────┬──────────────────────────┬────────────────────────┤
│              │                          │                        │
│  Input Form  │   Reasoning Trace        │  Brain Maps            │
│              │   (streaming)            │  + Overlap Score       │
│  [Drug name] │                          │                        │
│  [Indication]│                          │  [Confidence Panel]    │
│              │                          │                        │
│  [Validate]  ├──────────────────────────┤                        │
│  [Load Demo] │   Target Report          │                        │
│              │   (appears when done)    │                        │
│              │   [Export PDF button]    │                        │
└──────────────┴──────────────────────────┴────────────────────────┘
```

**Column widths:** Left: 280px fixed | Center: flex (grows) | Right: 340px fixed  
**Background:** Light gray (`#F8F8F7`) — panels are white cards on gray background  
**Font:** System sans-serif stack  
**No dark mode required for hackathon MVP**

### 8.2 Header
- Left: "CircuitMap" wordmark, 20px, weight 600
- Right: "Demo" badge (amber) if in demo mode; nothing otherwise
- Height: 52px, white background, 1px bottom border

### 8.3 Error States
- ChEMBL no results: "No target found for '[query]'. Try the generic drug name instead." — shown as amber banner in trace panel
- abagen gene not found: "Gene '[gene]' not found in Allen Brain Atlas. Agent will attempt downstream targets." — agent continues automatically
- Neurosynth no results: "No Neurosynth map for '[indication]'. Using closest match: '[alternative]'." — agent continues with alternative
- Session timeout: "Session expired. Please start a new validation." — full page reload button
- API error: "Something went wrong. Your demo scenarios are still available." — show Load Demo button

---

## 9. Data Models

### 9.1 Session
```python
class Session:
    session_id: str          # UUID v4
    drug_query: str          # Raw user input
    query_type: str          # "smiles" | "name"
    indication: str          # Disease indication
    mode: str                # "live" | "demo"
    status: str              # "pending" | "running" | "complete" | "error"
    created_at: datetime
    messages: list           # Full Claude conversation history
    tool_results: dict       # session_id -> {map_ids, scores, etc.}
    brain_maps: dict         # {"expression": PIL.Image, "disease": PIL.Image}
    report: dict | None      # Parsed report sections
    pdf_path: str | None     # Path to generated PDF
```

### 9.2 Tool Result: resolve_target
```python
class TargetResult:
    primary_target: str          # Gene name (e.g., "SUV39H1")
    protein_name: str            # Full protein name
    target_class: str            # e.g., "Histone methyltransferase"
    binding_affinity: float      # Ki or IC50 in nM
    affinity_type: str           # "Ki" | "IC50" | "Kd"
    chembl_id: str               # e.g., "CHEMBL2364681"
    data_source: str             # "ChEMBL" | "PubChem"
    off_targets: list            # List of TargetResult for secondary targets
    confidence: str              # "confirmed" | "predicted" | "inferred"
```

### 9.3 Tool Result: get_brain_expression
```python
class ExpressionResult:
    gene_name: str
    map_id: str                  # Session-scoped ID for use in compute_overlap
    top_regions: list            # List of {region: str, percentile: float, raw_expression: float}
    atlas: str                   # "Desikan-Killiany 68-region"
    n_samples: int               # Number of AHBA tissue samples used
    image_path: str              # Path to Nilearn PNG
    parcellated_values: dict     # {region_name: expression_value} — 68 values
```

### 9.4 Tool Result: compute_overlap
```python
class OverlapResult:
    r: float                     # Pearson correlation coefficient
    p_value: float               # Parametric p-value (note: non-independent)
    percentile: int              # Percentile vs 1000-permutation null
    label: str                   # Human-readable label
    null_mean: float             # Mean of null distribution
    null_std: float              # SD of null distribution
    interpretation: str          # "strong" | "moderate" | "weak" alignment
```

---

## 10. Out of Scope (Hackathon MVP)

- User authentication and accounts
- Persistent storage of sessions across server restarts
- Batch processing of multiple compounds
- Real-time collaboration / shared sessions
- SMILES structure visualization (2D depiction)
- Custom atlas selection (DK-68 only)
- Novel compound synthesis route planning
- Clinical trial matching
- Mobile responsive design
- International language support
- Any form of FDA submission integration

---

## 11. Known Limitations (Must Disclose in Report and Pitch)

1. **mRNA ≠ protein**: AHBA measures mRNA expression in post-mortem tissue. Protein density, membrane trafficking, and functional receptor availability are not captured.
2. **Healthy brain atlas**: AHBA data is from neurologically healthy adult donors. Disease-altered expression patterns may differ substantially.
3. **Neurosynth maps**: These are meta-analytic maps from diverse task designs and populations. They represent broad associations, not circuit-specific functional specialization.
4. **Spatial correlation scope**: The correlation is computed across 68 parcels. This is a gross-scale measure — it does not capture laminar or cell-type-specific expression.
5. **RAG store is static**: The embedded PubMed abstracts are pre-downloaded before the hackathon. The agent cannot access real-time literature.
6. **No pharmacokinetics**: CircuitMap does not model blood-brain barrier penetration, drug metabolism, or CNS bioavailability.

---

## 12. Presentation Requirements

### 12.1 Slide Deck (6 slides maximum)
1. **Problem** — 95% CNS trial failure rate. One statistic. One human story (e.g., Alzheimer's patient waiting for a drug that never arrives).
2. **Insight** — The gap between molecule and brain circuit. Visual: a broken bridge between "drug binds protein" and "patient improves."
3. **Product** — Screenshot of the live demo UI with the reasoning trace active.
4. **Market** — TAM: 500+ CNS biotech companies × $20k/report. Three named target customers.
5. **Competitive** — 2×2 matrix: X-axis = molecular detail, Y-axis = systems/circuit scope. CircuitMap is the only one in the top-right quadrant.
6. **Team** — Om: Mayo Clinic drug discovery, UTSW BCI lab, neuroscience domain expert. CS: AI systems architect. Business: GTM and market. Photo or initials for each.

### 12.2 The 60-Second Opening (Scripted)
> "Ninety-five percent of CNS drugs that enter clinical trials fail. Not because the chemistry is wrong — because nobody mapped the drug's target to the full brain circuit before committing $50 million to a program. Right now, that mapping requires a team of consultants, six weeks, and $200,000. We built an AI agent that does it in four minutes. Watch."
> [Start live demo]

### 12.3 Q&A Answers

**"How do you know the agent's reasoning is scientifically valid?"**
> "Every data source the agent calls is peer-reviewed and published in Nature or Nature Methods. The expression data is from the Allen Human Brain Atlas — the same resource used by the NIH's BRAIN Initiative. The disease maps are from Neurosynth — 14,000 published fMRI studies. The spatial correlation method is published in Nature Neuroscience. We framed the output as pre-clinical evidence, not clinical prediction, which is the same positioning as any structural bioinformatics tool."

**"Why won't researchers just use ChatGPT for this?"**
> "ChatGPT has no access to ChEMBL. It cannot query the Allen Brain Atlas. It will hallucinate gene expression values. It cannot run a spatial correlation between two brain maps. CircuitMap is not a language model wrapped in a nice UI — it is an agent that actually executes scientific analysis on validated databases. The reasoning trace you just watched is real computation, not generated text."

**"What's your GTM — pharma sales cycles are 12 months."**
> "We're not starting with Pfizer. Our first 10 customers are Series A-C CNS biotechs and SBIR-funded academic spinouts. These companies make go/no-go decisions in weeks, not years. Our warm path is Dr. Lega's network at UT Southwestern — there are three spinout companies in his clinical research orbit with active CNS programs. First sale target: 60 days post-hackathon."
