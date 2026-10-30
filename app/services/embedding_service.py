from sentence_transformers import SentenceTransformer

_model = None

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_model():
    global _model
    
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    
    return _model

def generate_embeddings(texts:list[str]) -> list[list[float]]:
    """
    convert text chunks into embedding vectors.
    """
    
    if not texts:
        return []
    
    model = get_model()
    
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar = False,
    )
    
    return embeddings.tolist()