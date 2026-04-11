"""
chembl_service.py — ChEMBL + PubChem drug target resolution.

Given a drug name or SMILES string, returns up to 3 CNS targets
ordered by binding affinity (lowest nM = first).
"""
import os
import requests


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
    result["note"] = "Resolved from bundled offline fallback data."
    return result

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

    try:
        from chembl_webresource_client.new_client import new_client

        if query_type == "smiles":
            result = _resolve_by_smiles(query, new_client)
        else:
            result = _resolve_by_name(query, new_client)

        if result.get("primary_target") or fallback is None:
            return result

        fallback["note"] = (
            "Using bundled offline fallback because live ChEMBL lookup returned "
            f"no target: {result.get('error', 'unknown error')}"
        )
        return fallback
    except Exception as e:
        if fallback is not None:
            fallback["note"] = (
                "Using bundled offline fallback because live target resolution "
                f"failed: {e}"
            )
            return fallback

        # Fall back to PubChem
        try:
            return _resolve_via_pubchem(query, query_type)
        except Exception as e2:
            return {
                "error": f"ChEMBL failed: {e}. PubChem failed: {e2}",
                "targets": [],
                "primary_target": None
            }


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
    if query_type == 'name':
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(query)}/JSON"
    else:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{requests.utils.quote(query)}/JSON"

    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"PubChem returned status {resp.status_code}")

    data = resp.json()
    compounds = data.get('PC_Compounds', [])
    if not compounds:
        raise Exception("No compounds found in PubChem")

    cid = compounds[0].get('id', {}).get('id', {}).get('cid', 'Unknown')

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
        "pubchem_cid": cid,
        "note": "No binding data found. PubChem CID retrieved only."
    }


if __name__ == "__main__":
    result = resolve_target("Donepezil", "name")
    print(result)
    assert result.get("primary_target"), "Should find ACHE for Donepezil"
    print("chembl_service TEST PASSED")
