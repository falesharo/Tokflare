import asyncio
import sys
import os
import json

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.core.smm.router import smm_router

async def export_everything():
    """
    Fetches the 100% complete catalog from the provider and saves it to a file.
    """
    print("🚀 Initiating FULL catalog extraction from SMM provider...")
    
    try:
        provider = smm_router.get_provider()
        # Fetching all services directly from the source API
        raw_services = await provider.get_all_services()
        
        if not isinstance(raw_services, list):
            print(f"❌ Error: Expected list but received {type(raw_services)}")
            print(f"Response snippet: {str(raw_services)[:200]}")
            return

        output_path = "full_provider_catalog.json"
        
        # Save to Project Root
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_services, f, indent=4, ensure_ascii=False)
        
        print(f"✅ SUCCESS! Total Services Extracted: {len(raw_services)}")
        print(f"📂 File saved at: {os.path.abspath(output_path)}")
        
        # Optional: Save as readable text summary too
        txt_path = "full_provider_catalog_summary.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"TOKFLARE PROVIDER EXPORT\n")
            f.write(f"Total Services: {len(raw_services)}\n")
            f.write("-" * 50 + "\n")
            for s in raw_services:
                f.write(f"ID: {s.get('service')} | Rate: ${s.get('rate')}/1k | [{s.get('category')}] {s.get('name')}\n")
        
        print(f"✅ Text summary saved at: {os.path.abspath(txt_path)}")

    except Exception as e:
        print(f"❌ Critical Error during extraction: {e}")

if __name__ == "__main__":
    asyncio.run(export_everything())
