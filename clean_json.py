import json
import pandas as pd

# Load the JSON file
with open("results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Check the DataFrame
print(df.info())  # shows columns and non-null counts
print(df.head()) 

import re

# Function to clean text
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<.*?>", "", text)    # remove HTML tags
    text = re.sub(r"\s+", " ", text)     # normalize whitespace
    return text.strip()

# Apply cleaning to title and content
df["title"] = df["title"].apply(clean_text)
df["content"] = df["content"].apply(clean_text)

df = df.drop_duplicates(subset=["content"])
df = df[df["content"] != ""]

df.to_csv("cleaned_results.csv", index=False)
print("Cleaned data saved to 'cleaned_results.csv'")
