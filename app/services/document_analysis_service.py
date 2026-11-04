
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Load backend .env
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def generate_document_overview(
    filename: str,
    pages: list[dict],
) -> str:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing from the backend .env file."
        )

    if not pages:
        raise ValueError("No document content available.")

    # Prepare document text with page references
    context_parts = []

    for page in pages:
        text = page.get("text", "").strip()

        if text:
            page_number = page.get("page_number")
            context_parts.append(
                f"[Page {page_number}]\n{text}"
            )

    context = "\n\n".join(context_parts)

    if not context.strip():
        raise ValueError("The document contains no readable text.")

    # Limit input size for the initial implementation
    max_characters = 30000
    context = context[:max_characters]
    
    print("Starting document analysis...")
    print("Filename:", filename)
    print("Characters sent to Groq:", len(context))

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent AI research assistant. "
                    "A user has just uploaded a document. Analyse it "
                    "and respond naturally as a helpful conversational "
                    "assistant, just like ChatGPT.\n\n"
                    "Your response must include:\n"
                    "1. A friendly introduction.\n"
                    "2. What the document is about.\n"
                    "3. A concise summary.\n"
                    "4. Important topics covered.\n"
                    "5. Important findings or conclusions, if present.\n"
                    "6. Five useful suggested questions.\n\n"
                    "Use clear headings and bullet points.\n"
                    "Keep the explanation easy to understand.\n"
                    "Only use information present in the document.\n"
                    "Do not invent findings or conclusions.\n"
                    "If information is unavailable, say so.\n"
                    "Do not generate a separate report or file."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Document filename: {filename}\n\n"
                    f"Document content:\n{context}"
                ),
            },
        ],
        temperature=0.3,
    )
    
    print("groq document analysis completed !!")

    return response.choices[0].message.content or (
        "I've received your document, but couldn't generate "
        "its overview. You can ask me questions about it."
    )
