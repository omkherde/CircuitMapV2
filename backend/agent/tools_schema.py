"""
agent/tools_schema.py — All 6 tool schemas for Claude tool_use (verbatim from PRD §6.3).
"""

TOOLS = [
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
    },
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
    },
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
    },
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
    },
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
    },
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
]
