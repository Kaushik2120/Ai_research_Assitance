
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Load the .env file from the backend folder
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def generate_answer(question: str, passages: list[dict]) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from the backend .env file.")

    if not passages:
        return "I couldn't find relevant information in the uploaded documents."

    context_parts = []

    for passage in passages:
        context_parts.append(
            f"[Page {passage['page_number']}]\n{passage['text']}"
        )

    context = "\n\n".join(context_parts)

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI research assistant. Answer using only "
                    "the supplied document passages. If the passages do not "
                    "contain the answer, say so. Do not invent facts. "
                    "Cite supporting page numbers in your answer."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Document passages:\n{context}"
                ),
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
