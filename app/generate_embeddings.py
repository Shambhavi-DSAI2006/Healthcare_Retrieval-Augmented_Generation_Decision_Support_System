from sentence_transformers import SentenceTransformer
import pandas as pd

# Load sentence-transformers model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Read chunk data
chunks = pd.read_csv('data/chunk.csv')

# Generate embeddings
embeddings = model.encode(chunks['chunk_text'].tolist())

embedding_rows = []

for i, emb in enumerate(embeddings):
    embedding_rows.append({
        "embedding_id": i + 1,
        "chunk_id": chunks.iloc[i]['chunk_id'],
        "vector": emb.tolist()
    })

# Create dataframe
embedding_df = pd.DataFrame(embedding_rows)

# Save embeddings
embedding_df.to_csv('data/embedding.csv', index=False)

print("Embeddings generated successfully.")