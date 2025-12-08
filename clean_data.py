import os
import json

OUTPUT_DIR = "crawled_data"

# Loop through all JSON files in the folder
for filename in os.listdir(OUTPUT_DIR):
    if not filename.endswith(".json"):
        continue

    filepath = os.path.join(OUTPUT_DIR, filename)

    # Open the JSON file
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # --- Cleaning steps ---
    # 1. Strip leading/trailing whitespace
    content = data.get("full_content", "").strip()

    # 2. Normalize spaces and newlines
    content = " ".join(content.split())

    # Update the JSON data
    data["full_content"] = content

    # Save cleaned content back to the same file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"[CLEANED] {filename}")

print("All JSON files cleaned safely!")