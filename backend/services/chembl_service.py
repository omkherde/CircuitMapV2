"""
chembl_service.py — ChEMBL + PubChem drug target resolution.

Given a drug name or SMILES string, returns up to 3 CNS targets
ordered by binding affinity (lowest nM = first).
"""
import os
import requests

TARGET_RESOLUTION_TIMEOUT_SECONDS = float(os.getenv("TARGET_RESOLUTION_TIMEOUT_SECONDS", "6"))
CHEMBL_STATUS_URL = "https://www.ebi.ac.uk/chembl/api/data/status.json"
PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

LOCAL_TARGET_FALLBACKS = {
    "chaetocin": {
        "primary_target": "HIF1A",
        "protein_name": "Hypoxia-inducible factor 1-alpha",
        "target_class": "Transcription factor",
        "binding_affinity": 40.0,
        "affinity_type": "IC50",
        "chembl_id": "CHEMBL4261",
        "data_source": "Local fallback (offline)",
        "off_targets": [
            {
                "gene_name": "SUV39H1",
                "protein_name": "Histone-lysine N-methyltransferase SUV39H1",
                "target_class": "Histone methyltransferase",
                "binding_affinity": 800.0,
                "affinity_type": "IC50",
                "chembl_id": "CHEMBL1795118",
                "confidence": "fallback",
            },
            {
                "gene_name": "EHMT2",
                "protein_name": "Histone-lysine N-methyltransferase EHMT2",
                "target_class": "Histone methyltransferase",
                "binding_affinity": 2400.0,
                "affinity_type": "IC50",
                "chembl_id": "CHEMBL6032",
                "confidence": "fallback",
            },
        ],
        "confidence": "fallback",
        "drug_name": "Chaetocin",
        "molecule_chembl_id": "CHEMBL1089316",
    },
    "tolcapone": {
        "primary_target": "COMT",
        "protein_name": "Catechol O-methyltransferase",
        "target_class": "Catechol-O-methyltransferase",
        "binding_affinity": 5.0,
        "affinity_type": "Ki",
        "chembl_id": "CHEMBL1978",
        "data_source": "Local fallback (offline)",
        "off_targets": [],
        "confidence": "fallback",
        "drug_name": "Tolcapone",
    },
    "vorinostat": {
        "primary_target": "HDAC1",
        "protein_name": "Histone deacetylase 1",
        "target_class": "Histone deacetylase",
        "binding_affinity": 10.0,
        "affinity_type": "IC50",
        "chembl_id": "CHEMBL325",
        "data_source": "Local fallback (offline)",
        "off_targets": [
            {
                "gene_name": "HDAC2",
                "protein_name": "Histone deacetylase 2",
                "target_class": "Histone deacetylase",
                "binding_affinity": 48.0,
                "affinity_type": "IC50",
                "chembl_id": "CHEMBL1937",
                "confidence": "fallback",
            },
            {
                "gene_name": "HDAC3",
                "protein_name": "Histone deacetylase 3",
                "target_class": "Histone deacetylase",
                "binding_affinity": 20.0,
                "affinity_type": "IC50",
                "chembl_id": "CHEMBL1865",
                "confidence": "fallback",
            },
        ],
        "confidence": "fallback",
        "drug_name": "Vorinostat",
    },
    "donepezil": {
        "primary_target": "ACHE",
        "protein_name": "Acetylcholinesterase",
        "target_class": "Enzyme",
        "binding_affinity": 12.0,
        "affinity_type": "Ki",
        "chembl_id": "CHEMBL220",
        "data_source": "Local fallback (offline)",
        "off_targets": [],
        "confidence": "fallback",
        "drug_name": "Donepezil",
    },
}


def _resolve_local_fallback(query: str, query_type: str) -> dict | None:
    """Return a deterministic local fallback for common demo molecules."""
    if query_type != "name":
        return None

    key = query.strip().lower()
    if key not in LOCAL_TARGET_FALLBACKS:
        return None

    result = dict(LOCAL_TARGET_FALLBACKS[key])
    result["query"] = query
    result["query_type"] = query_type
    result["note"] = "Resolved from bundled offline fallback data."
    return result


def _build_unresolved_result(
    query: str,
    query_type: str,
    note: str,
    *,
    data_source: str = "Unavailable",
    error: str | None = None,
    resolved_name: str | None = None,
    pubchem_cid: int | None = None,
) -> dict:
    result = {
        "query": query,
        "query_type": query_type,
        "primary_target": None,
        "protein_name": None,
        "target_class": "Unknown",
        "binding_affinity": None,
        "affinity_type": None,
        "chembl_id": None,
        "data_source": data_source,
        "off_targets": [],
        "confidence": "unresolved",
        "note": note,
    }
    if error:
        result["error"] = error
    if resolved_name:
        result["drug_name"] = resolved_name
        result["resolved_name"] = resolved_name
    if pubchem_cid is not None:
        result["pubchem_cid"] = pubchem_cid
    return result


def _short_error(exc: Exception | str) -> str:
    text = str(exc).strip()
    return text.splitlines()[0] if text else "unknown error"


def _service_available(url: str) -> bool:
    try:
        response = requests.get(url, timeout=TARGET_RESOLUTION_TIMEOUT_SECONDS)
        return response.ok
    except requests.RequestException:
        return False


def _pubchem_query_segment(query: str, query_type: str) -> str:
    encoded = requests.utils.quote(query, safe="")
    return f"name/{encoded}" if query_type == "name" else f"smiles/{encoded}"


def _lookup_pubchem_metadata(query: str, query_type: str) -> dict | None:
    """
    Retrieve basic PubChem metadata that can help canonicalize a name or SMILES.
    """
    query_segment = _pubchem_query_segment(query, query_type)
    cid_url = f"{PUBCHEM_BASE_URL}/compound/{query_segment}/cids/JSON"

    cid_response = requests.get(cid_url, timeout=TARGET_RESOLUTION_TIMEOUT_SECONDS)
    if cid_response.status_code != 200:
        return None

    cids = cid_response.json().get("IdentifierList", {}).get("CID", [])
    if not cids:
        return None

    cid = cids[0]
    metadata = {"pubchem_cid": cid}

    property_url = (
        f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/property/"
        "Title,IUPACName,CanonicalSMILES,IsomericSMILES/JSON"
    )
    try:
        property_response = requests.get(property_url, timeout=TARGET_RESOLUTION_TIMEOUT_SECONDS)
        if property_response.status_code == 200:
            props = property_response.json().get("PropertyTable", {}).get("Properties", [])
            if props:
                first = props[0]
                metadata["title"] = first.get("Title")
                metadata["iupac_name"] = first.get("IUPACName")
                metadata["canonical_smiles"] = first.get("CanonicalSMILES")
                metadata["isomeric_smiles"] = first.get("IsomericSMILES")
    except requests.RequestException:
        pass

    synonyms_url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/synonyms/JSON"
    try:
        synonyms_response = requests.get(synonyms_url, timeout=TARGET_RESOLUTION_TIMEOUT_SECONDS)
        if synonyms_response.status_code == 200:
            info = synonyms_response.json().get("InformationList", {}).get("Information", [])
            if info:
                metadata["synonyms"] = info[0].get("Synonym", [])
    except requests.RequestException:
        pass

    return metadata


def _extract_pubchem_candidate_names(metadata: dict) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    raw_names = [
        metadata.get("title"),
        metadata.get("iupac_name"),
        *(metadata.get("synonyms") or []),
    ]

    for value in raw_names:
        if not value:
            continue
        name = value.strip()
        key = name.lower()
        if key in seen:
            continue
        if len(name) < 2 or len(name) > 100:
            continue
        if name.upper().startswith("CID"):
            continue
        seen.add(key)
        candidates.append(name)
        if len(candidates) >= 12:
            break

    return candidates


def _resolve_via_pubchem_aliases(query: str, query_type: str, new_client) -> tuple[dict | None, dict | None]:
    """
    Use PubChem to canonicalize a submitted name/SMILES, then retry ChEMBL by name.
    """
    metadata = _lookup_pubchem_metadata(query, query_type)
    if not metadata:
        return None, None

    for candidate_name in _extract_pubchem_candidate_names(metadata):
        result = _resolve_by_name(candidate_name, new_client)
        if result.get("primary_target"):
            result["note"] = (
                f"Resolved via PubChem canonicalization using '{candidate_name}' before ChEMBL target lookup."
            )
            result["pubchem_cid"] = metadata.get("pubchem_cid")
            result["resolved_name"] = candidate_name
            return result, metadata

    return None, metadata

def resolve_target(query: str, query_type: str) -> dict:
    """
    Resolve drug molecule to primary CNS target(s).

    Args:
        query: SMILES string or drug/compound name
        query_type: 'smiles' or 'name'

    Returns:
        dict with keys: primary_target, protein_name, target_class,
        binding_affinity, affinity_type, chembl_id, data_source, off_targets, confidence
        On failure: {"error": "...", "targets": []}
    """
    fallback = _resolve_local_fallback(query, query_type)
    normalized_query = query.strip()

    if fallback is not None:
        return fallback

    chembl_error = None
    try:
        if not _service_available(CHEMBL_STATUS_URL):
            raise RuntimeError("ChEMBL service unavailable")

        from chembl_webresource_client.new_client import new_client

        if query_type == "smiles":
            result = _resolve_by_smiles(normalized_query, new_client)
        else:
            result = _resolve_by_name(normalized_query, new_client)

        if result.get("primary_target"):
            result["query"] = normalized_query
            result["query_type"] = query_type
            return result

        alias_result, metadata = _resolve_via_pubchem_aliases(normalized_query, query_type, new_client)
        if alias_result and alias_result.get("primary_target"):
            alias_result["query"] = normalized_query
            alias_result["query_type"] = query_type
            return alias_result

        resolution_note = result.get("error", "No target found from ChEMBL.")
        if metadata:
            return _build_unresolved_result(
                normalized_query,
                query_type,
                note=(
                    f"{resolution_note} PubChem recognized the molecule"
                    + (f" as '{metadata.get('title')}'." if metadata.get("title") else ".")
                ),
                data_source="PubChem",
                error=resolution_note,
                resolved_name=metadata.get("title") or metadata.get("iupac_name"),
                pubchem_cid=metadata.get("pubchem_cid"),
            )
        return _build_unresolved_result(
            normalized_query,
            query_type,
            note=resolution_note,
            data_source="ChEMBL",
            error=resolution_note,
        )
    except Exception as e:
        chembl_error = _short_error(e)

    # Fall back to PubChem metadata if ChEMBL is unavailable or errored.
    try:
        pubchem_result = _resolve_via_pubchem(normalized_query, query_type)
        note = pubchem_result.get("note", "PubChem recognized the molecule but target resolution is unavailable.")
        if chembl_error:
            note = f"ChEMBL lookup failed: {chembl_error}. {note}"
        return _build_unresolved_result(
            normalized_query,
            query_type,
            note=note,
            data_source=pubchem_result.get("data_source", "PubChem"),
            error=chembl_error or pubchem_result.get("error"),
            resolved_name=pubchem_result.get("drug_name"),
            pubchem_cid=pubchem_result.get("pubchem_cid"),
        )
    except Exception as e2:
        combined_error = f"ChEMBL failed: {chembl_error or 'unknown error'}. PubChem failed: {_short_error(e2)}"
        return _build_unresolved_result(
            normalized_query,
            query_type,
            note=(
                "The submitted molecule could not be resolved to a primary target in the current environment. "
                "If you are running offline, reconnect to the internet and retry. "
                "Otherwise try a generic drug name or an alternative SMILES representation."
            ),
            data_source="Unavailable",
            error=combined_error,
        )


def _resolve_by_name(drug_name: str, new_client) -> dict:
    molecule = new_client.molecule
    activity = new_client.activity
    target = new_client.target

    # Try exact preferred name first
    mols = list(molecule.filter(pref_name__iexact=drug_name).only(
        ['molecule_chembl_id', 'pref_name']))

    # Fall back to synonym search
    if not mols:
        mols = list(molecule.filter(
            molecule_synonyms__synonym__iexact=drug_name
        ).only(['molecule_chembl_id', 'pref_name']))

    if not mols:
        return {
            "error": f"No molecule found in ChEMBL for '{drug_name}'. Try the generic name.",
            "targets": [],
            "primary_target": None
        }

    chembl_id = mols[0]['molecule_chembl_id']
    pref_name = mols[0].get('pref_name', drug_name)

    return _get_targets_for_chembl_id(chembl_id, pref_name, activity, target, "ChEMBL")


def _resolve_by_smiles(smiles: str, new_client) -> dict:
    molecule = new_client.molecule
    activity = new_client.activity
    target = new_client.target

    # Flexible SMILES match
    mols = list(molecule.filter(smiles__flexmatch=smiles).only(
        ['molecule_chembl_id', 'pref_name']))

    if not mols:
        return {
            "error": f"No molecule found in ChEMBL for SMILES. Try the drug name instead.",
            "targets": [],
            "primary_target": None
        }

    chembl_id = mols[0]['molecule_chembl_id']
    pref_name = mols[0].get('pref_name', 'Unknown')

    return _get_targets_for_chembl_id(chembl_id, pref_name, activity, target, "ChEMBL")


def _get_targets_for_chembl_id(chembl_id: str, pref_name: str, activity, target, source: str) -> dict:
    # Get bioactivities for this molecule
    activities = list(activity.filter(
        molecule_chembl_id=chembl_id,
        standard_type__in=['Ki', 'IC50', 'Kd'],
        target_organism='Homo sapiens',
        assay_type='B'  # Binding assays
    ).only([
        'target_chembl_id', 'standard_value', 'standard_type',
        'standard_units', 'assay_description', 'pchembl_value'
    ]))

    if not activities:
        # Relax filter — try without assay_type restriction
        activities = list(activity.filter(
            molecule_chembl_id=chembl_id,
            standard_type__in=['Ki', 'IC50', 'Kd'],
            target_organism='Homo sapiens'
        ).only([
            'target_chembl_id', 'standard_value', 'standard_type',
            'standard_units', 'pchembl_value'
        ]))

    if not activities:
        return {
            "error": f"No binding activity data found for {pref_name} (ChEMBL: {chembl_id})",
            "targets": [],
            "primary_target": None,
            "chembl_id": chembl_id
        }

    # Filter to single-protein targets only
    valid_acts = []
    for act in activities:
        if act.get('standard_value') and act.get('target_chembl_id'):
            try:
                val = float(act['standard_value'])
                if val > 0:
                    valid_acts.append(act)
            except (ValueError, TypeError):
                continue

    # Sort by standard_value ascending (lower nM = tighter binding)
    valid_acts.sort(key=lambda x: float(x.get('standard_value', 9999999)))

    # Build target list, up to 3
    seen_targets = set()
    result_targets = []

    for act in valid_acts:
        tgt_id = act.get('target_chembl_id')
        if tgt_id in seen_targets or len(result_targets) >= 3:
            continue

        # Fetch target details
        tgt_details = list(target.filter(
            target_chembl_id=tgt_id,
            target_type='SINGLE PROTEIN'
        ).only(['target_chembl_id', 'pref_name', 'target_type',
                'target_components']))

        if not tgt_details:
            continue  # Skip non-single-protein targets

        tgt_info = tgt_details[0]
        gene_name = _extract_gene_name(tgt_info)

        seen_targets.add(tgt_id)
        result_targets.append({
            "gene_name": gene_name,
            "protein_name": tgt_info.get('pref_name', 'Unknown'),
            "target_class": _infer_target_class(tgt_info.get('pref_name', '')),
            "binding_affinity": round(float(act['standard_value']), 2),
            "affinity_type": act.get('standard_type', 'Ki'),
            "chembl_id": tgt_id,
            "confidence": "confirmed"
        })

    if not result_targets:
        return {
            "error": f"Found activities but no single-protein targets for {pref_name}",
            "targets": [],
            "primary_target": None,
            "chembl_id": chembl_id
        }

    primary = result_targets[0]
    return {
        "primary_target": primary["gene_name"],
        "protein_name": primary["protein_name"],
        "target_class": primary["target_class"],
        "binding_affinity": primary["binding_affinity"],
        "affinity_type": primary["affinity_type"],
        "chembl_id": primary["chembl_id"],
        "data_source": source,
        "off_targets": result_targets[1:],
        "confidence": primary["confidence"],
        "drug_name": pref_name,
        "molecule_chembl_id": chembl_id
    }


def _extract_gene_name(tgt_info: dict) -> str:
    """Extract gene symbol from target component data."""
    components = tgt_info.get('target_components', [])
    if components:
        for comp in components:
            synonyms = comp.get('target_component_synonyms', [])
            for syn in synonyms:
                if syn.get('syn_type') == 'GENE_SYMBOL':
                    return syn.get('component_synonym', 'Unknown')
    # Fall back: parse from protein name
    name = tgt_info.get('pref_name', 'Unknown')
    return name.split()[0] if name else 'Unknown'


def _infer_target_class(protein_name: str) -> str:
    """Infer target class from protein name keywords."""
    name_lower = protein_name.lower()
    if 'kinase' in name_lower:
        return 'Kinase'
    elif 'histone' in name_lower and 'methyltransferase' in name_lower:
        return 'Histone methyltransferase'
    elif 'deacetylase' in name_lower or 'hdac' in name_lower:
        return 'Histone deacetylase'
    elif 'receptor' in name_lower:
        return 'Receptor'
    elif 'transporter' in name_lower:
        return 'Transporter'
    elif 'transferase' in name_lower:
        return 'Transferase'
    elif 'oxidase' in name_lower:
        return 'Oxidase'
    elif 'reductase' in name_lower:
        return 'Reductase'
    elif 'comt' in name_lower or 'catechol' in name_lower:
        return 'Catechol-O-methyltransferase'
    else:
        return 'Enzyme'


def _resolve_via_pubchem(query: str, query_type: str) -> dict:
    """PubChem fallback lookup."""
    metadata = _lookup_pubchem_metadata(query, query_type)
    if not metadata:
        raise Exception("No compounds found in PubChem")

    return {
        "primary_target": "Unknown",
        "protein_name": "Unknown — PubChem fallback",
        "target_class": "Unknown",
        "binding_affinity": None,
        "affinity_type": None,
        "chembl_id": None,
        "data_source": "PubChem",
        "off_targets": [],
        "confidence": "inferred",
        "pubchem_cid": metadata.get("pubchem_cid"),
        "drug_name": metadata.get("title") or metadata.get("iupac_name"),
        "canonical_smiles": metadata.get("canonical_smiles"),
        "note": "No target-level binding data found. PubChem recognized the submitted molecule."
    }


if __name__ == "__main__":
    result = resolve_target("Donepezil", "name")
    print(result)
    assert result.get("primary_target"), "Should find ACHE for Donepezil"
    print("chembl_service TEST PASSED")
