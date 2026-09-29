from datasets import load_dataset


dataset = load_dataset(
    "json",
    data_files="dataset/processed/assessment_dataset.jsonl"
)

print(dataset)
print(dataset["train"][0])