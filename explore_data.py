import json
import pandas as pd 

with open("results.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"Total records: {len(data)}")

for i, entry in enumerate(data[:3]):
    print (f"\nEntry {i+1}:")
    print(entry)
