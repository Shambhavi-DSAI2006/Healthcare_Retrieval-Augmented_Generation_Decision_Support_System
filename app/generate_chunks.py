import pandas as pd

# Read raw medical text
with open("raw_medical_text.txt", "r", encoding="utf-8") as file:
    text = file.read()

# Split text into sentences
sentences = text.split(".")

chunks = []

chunk_id = 1
section_id = 1

for sentence in sentences:
    sentence = sentence.strip()

    # Ignore very short text
    if len(sentence) > 20:
        chunks.append({
            "chunk_id": chunk_id,
            "chunk_text": sentence + ".",
            "chunk_index": chunk_id,
            "section_id": section_id
        })

        chunk_id += 1

# Convert to dataframe
chunk_df = pd.DataFrame(chunks)

# Save to chunk.csv
chunk_df.to_csv("data/chunk.csv", index=False)

print(f"{len(chunk_df)} chunks generated successfully.")