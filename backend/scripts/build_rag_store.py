"""
scripts/build_rag_store.py — Fetch PubMed abstracts and build ChromaDB vector store.

Requires internet. Takes ~30 minutes.
Run BEFORE the hackathon:
    cd backend
    python scripts/build_rag_store.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from Bio import Entrez
import chromadb
from chromadb.utils import embedding_functions

Entrez.email = "circuitmap@hackathon.ai"

DATA_DIR = os.getenv("CHROMA_DB_DIR", "./cache/chroma_db")
os.makedirs(DATA_DIR, exist_ok=True)

GENES = ['SUV39H1', 'COMT', 'HDAC2', 'HDAC1', 'EHMT2', 'BDNF',
         'MAOA', 'SLC6A4', 'DRD2', 'DNMT3A']
DISEASES = ['alzheimer', 'schizophrenia', 'depression', 'parkinson']


def fetch_abstracts(query: str, max_results: int = 30) -> list:
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        ids = record.get("IdList", [])
        if not ids:
            return []

        time.sleep(0.4)  # Respect NCBI rate limit (3 req/sec)

        handle = Entrez.efetch(db="pubmed", id=",".join(ids),
                               rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        abstracts = []
        for article in records.get("PubmedArticle", []):
            try:
                ml = article["MedlineCitation"]
                art = ml["Article"]
                abstract = str(art.get("Abstract", {}).get("AbstractText", ""))
                title = str(art.get("ArticleTitle", ""))
                pmid = str(ml["PMID"])
                year = str(ml.get("DateCompleted", {}).get("Year", "2020"))
                journal = str(art.get("Journal", {}).get("Title", ""))

                if abstract and len(abstract) > 80:
                    abstracts.append({
                        "text": f"{title}\n{abstract}",
                        "pmid": pmid,
                        "title": title,
                        "year": year,
                        "journal": journal
                    })
            except Exception:
                continue
        return abstracts
    except Exception as e:
        print(f"  PubMed fetch error: {e}")
        return []


# Initialize ChromaDB
print(f"Initializing ChromaDB at: {os.path.abspath(DATA_DIR)}")
client = chromadb.PersistentClient(path=DATA_DIR)

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    device="cpu"  # Force CPU — no GPU assumption
)

# Delete existing collection if present
try:
    client.delete_collection("pubmed_abstracts")
    print("Deleted existing collection.")
except Exception:
    pass

collection = client.create_collection(
    name="pubmed_abstracts",
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"}
)

print(f"\nFetching abstracts for {len(GENES)} genes × {len(DISEASES)} diseases...")
total = 0
errors = 0

for gene in GENES:
    for disease in DISEASES:
        query = f"{gene} {disease} brain neuroscience"
        abstracts = fetch_abstracts(query, max_results=20)

        for ab in abstracts:
            doc_id = f"{gene}_{disease}_{ab['pmid']}"
            try:
                collection.add(
                    documents=[ab["text"]],
                    ids=[doc_id],
                    metadatas=[{
                        "gene": gene,
                        "disease": disease,
                        "pmid": ab["pmid"],
                        "title": ab["title"][:200],
                        "year": ab["year"],
                        "journal": ab["journal"][:100]
                    }]
                )
                total += 1
            except Exception:
                errors += 1  # Skip duplicates silently

        print(f"  {gene} + {disease}: {len(abstracts)} abstracts → total {total}")
        time.sleep(0.3)

print(f"\nChromaDB build COMPLETE.")
print(f"Total documents: {collection.count()}")
print(f"Errors (duplicates/skipped): {errors}")
