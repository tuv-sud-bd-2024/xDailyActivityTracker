#!/usr/bin/env python3
"""Quick test of Gemini Flash client integration."""
import sys
sys.path.insert(0, "/workspaces/xDailyActivityTracker")

from backend.app.llm_client import get_llm_client
from backend.app.parse_pipeline import parse_whatsapp_block

# Test message
test_message = """[09:34, 12/10/2025] Staff-01: 1) Follow up savory site visit 2) attend meeting 3) work on solar project
[10:15, 12/10/2025] Staff-02: Called @~ClientA about PO"""

print("Testing parse_whatsapp_block with deterministic parser...")
result = parse_whatsapp_block(test_message)
print(f"✓ Parsed {len(result.parsed_items)} items (deterministic)")
for item in result.parsed_items:
    print(f"  - {item.item_id}: {item.description}")

print("\nTesting Gemini Flash client...")
try:
    llm = get_llm_client()
    print(f"✓ Initialized {llm.__class__.__name__}")
    
    # Try a Gemini parse if available
    if llm.__class__.__name__ == "GeminiFlashClient":
        print("  Calling Gemini Flash...")
        gemini_result = llm.parse_block(test_message)
        print(f"  ✓ Got response with {len(gemini_result.parsed_items)} items")
        for item in gemini_result.parsed_items:
            print(f"    - {item.item_id}: {item.description} (conf: {item.confidence})")
    else:
        print(f"  Fallback to {llm.__class__.__name__}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ Integration test complete!")
