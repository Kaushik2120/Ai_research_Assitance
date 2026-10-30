
from app.services.embedding_service import generate_embeddings

texts = [
    "Artificial intelligence helps computers perform tasks.",
    "Machine learning allows computers to learn from data.",
    "The Earth revolves around the Sun.",
]

vectors = generate_embeddings(texts)

print("Number of vectors:", len(vectors))
print("Dimensions:", len(vectors[0]))
print("First vector values:", vectors[0][:5])
