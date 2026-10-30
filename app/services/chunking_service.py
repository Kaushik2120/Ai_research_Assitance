def chunk_pages(
    pages: list[dict],
    chunk_size: int =1000,
    overlap: int =150,
)-> list[dict]:
    """
    splits the extracted pdf into no of chunks based in the chunk size and overlap
    """
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be btw 0 and chunk size")
    
    chunks =[]
    
    step= chunk_size - overlap
    
    for page in pages:
        text = page.get("text","").strip()
        page_number = page.get("page_number")
        
        if not text:
            continue
        
        for start in range(0,len(text),step):
            chunk_text = text[start:start+chunk_size].strip()
            
            if not chunk_text:
                continue
            
            chunks.append({
                "text":chunk_text,
                "page_number":page_number,
            })
    return chunks
    