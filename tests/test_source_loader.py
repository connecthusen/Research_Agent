import sys
import os

# Add the project root to Python's path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.source_loader import SourceLoader

def test_source_loader():
    """
    Test the SourceLoader by fetching all sources from sources.json.
    """
    print("[INFO] Testing SourceLoader...")
    loader = SourceLoader()
    sources, failures = loader.fetch_all()

    if not sources:
        print("[FAIL] No sources were fetched. Check sources.json and file paths/URLs.")
        assert False, "No sources were fetched"

    print(f"\n[PASS] Successfully fetched {len(sources)} sources:")
    for source in sources:
        print(f"  - {source['id']} ({source['type']}): {len(source['text'])} characters")

    assert len(sources) > 0, "No sources fetched"

if __name__ == "__main__":
    test_source_loader()
    print("\n[PASS] SourceLoader test passed!")