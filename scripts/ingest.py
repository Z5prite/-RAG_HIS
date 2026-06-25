import sys
import os
import time
from pathlib import Path

# Add backend directory to path to allow importing app modules
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.append(str(backend_dir))

from app.core.config import SETTINGS
from app.services.chunker import chunk_markdown
from app.services.vector_store import vector_store

def process_directory(directory: Path, collection_name: str):
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return
        
    print(f"\nProcessing {directory.name} -> {collection_name}")
    md_files = list(directory.glob("*.md"))
    
    total_docs = 0
    total_chunks = 0
    
    all_texts = []
    all_metadatas = []
    
    for file_path in md_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            chunks = chunk_markdown(content, filename=file_path.name)
            
            for chunk in chunks:
                all_texts.append(chunk["text"])
                all_metadatas.append(chunk["metadata"])
                
            total_docs += 1
            total_chunks += len(chunks)
            print(f"  Processed {file_path.name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            
    if all_texts:
        print(f"  Inserting {len(all_texts)} chunks into {collection_name}...")
        vector_store.add_documents(
            collection_name=collection_name,
            documents=all_texts,
            metadatas=all_metadatas
        )
        print("  Insert complete.")
        
    return total_docs, total_chunks

def main():
    start_time = time.time()
    print("Starting data ingestion...")
    
    # 1. Process medical knowledge base
    kb_dir = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"
    docs1, chunks1 = process_directory(kb_dir, "medical_kb")
    
    # 2. Process triage knowledge base
    triage_dir = Path(__file__).resolve().parents[1] / "data" / "medical-triage-kb" / "departments"
    docs2, chunks2 = process_directory(triage_dir, "triage_kb")
    
    # Print stats
    elapsed = time.time() - start_time
    stats = vector_store.stats()
    
    print("\n" + "="*40)
    print("Ingestion Summary")
    print("="*40)
    print(f"Total documents processed: {docs1 + docs2}")
    print(f"Total chunks created: {chunks1 + chunks2}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print("\nVector Store Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
