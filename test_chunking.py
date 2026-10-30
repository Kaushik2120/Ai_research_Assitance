from app.services.chunking_service import chunk_pages

sample_pages = [
    {
        "page_number":1,
        "text":(
            "AI helps perform computer tasks and is a subset of machine learning."
            *100
        ),
    },
    {
        "page_number":2,
        "text":"machine learning is a field of ai"
    },
]
chunks = chunk_pages(sample_pages)

print("total chunks:", len(chunks))
print("first chunk:",chunks[0]["text"])
print("source page:",chunks[0]["page_number"])