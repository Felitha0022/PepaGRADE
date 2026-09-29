import json
from pathlib import Path

raw_file = Path("dataset/raw/assessment_data.jsonl")
processed_file = Path("dataset/processed/assessment_dataset.jsonl")

# Make sure the processed folder exists
processed_file.parent.mkdir(parents=True, exist_ok=True)

with open(raw_file, "r", encoding="utf-8") as infile, \
     open(processed_file, "w", encoding="utf-8") as outfile:

    for line in infile:
        record = json.loads(line)

        processed_record = {
            "assignment_text": record["assignment_text"],
            "criteria": record["criteria"],
            "score": record["score"],
            "max_score": record["max_score"],
            "feedback": record["feedback"]
        }

        outfile.write(json.dumps(processed_record) + "\n")

print("Processed dataset created successfully.")
print(f"File: {processed_file}")