"""Compact tool schemas to reduce repeated Anthropic input tokens."""

TOOLS = [
    {
        "name": "resolve_target",
        "description": "Resolve a drug name or SMILES string to up to 3 targets ranked by binding affinity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Drug name or SMILES"
                },
                "query_type": {
                    "type": "string",
                    "enum": ["smiles", "name"],
                    "description": "Input type"
                }
            },
            "required": ["query", "query_type"]
        }
    },
    {
        "name": "get_brain_expression",
        "description": "Return regional AHBA mRNA expression for a gene plus a map_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_name": {
                    "type": "string",
                    "description": "HGNC gene symbol"
                }
            },
            "required": ["gene_name"]
        }
    },
    {
        "name": "get_cognitive_associations",
        "description": "Return top cognitive associations for a list of brain regions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "regions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Brain region names"
                },
                "top_n": {
                    "type": "integer",
                    "description": "Max associations to return. Default: 5",
                    "default": 5
                }
            },
            "required": ["regions"]
        }
    },
    {
        "name": "get_disease_map",
        "description": "Return a disease-associated brain map plus a map_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "indication": {
                    "type": "string",
                    "description": "Disease or condition"
                }
            },
            "required": ["indication"]
        }
    },
    {
        "name": "compute_overlap",
        "description": "Compute spatial overlap between two prior map_ids.",
        "input_schema": {
            "type": "object",
            "properties": {
                "map1_id": {
                    "type": "string",
                    "description": "First map_id"
                },
                "map2_id": {
                    "type": "string",
                    "description": "Second map_id"
                },
                "label": {
                    "type": "string",
                    "description": "Comparison label"
                }
            },
            "required": ["map1_id", "map2_id", "label"]
        }
    },
    {
        "name": "search_literature",
        "description": "Search the local literature store for relevant abstracts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Scientific search query"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Max abstracts to retrieve. Default: 3.",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
]
