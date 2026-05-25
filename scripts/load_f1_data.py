import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from knowledge_base.f1_loader import F1KnowledgeBase

if __name__ == "__main__":
    print("Loading F1 data from FastF1 cache...")
    kb = F1KnowledgeBase(cache_dir="./data/fastf1_cache")
    texts = kb.create_knowledge_texts()
    print(f"Loaded {len(texts)} race documents")
    
    # Save to file for later use
    import json
    with open("./data/f1_knowledge.json", "w") as f:
        json.dump(texts, f)
    print("✅ Saved to data/f1_knowledge.json")