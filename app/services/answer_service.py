
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Load the .env file from the backend folder
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def generate_answer(
    question: str,
    passages: list[dict],
    history: list[dict] | None = None,
) -> str:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing from the backend .env file."
        )

    if not passages:
        return (
            "I couldn't find relevant information in the uploaded "
            "documents to answer that question."
        )

    # 1. Prepare document context
    context_parts = []

    for passage in passages:
        context_parts.append(
            f"[Page {passage['page_number']}]\n{passage['text']}"
        )

    context = "\n\n".join(context_parts)

    # 2. Build system instructions
    system_prompt = """
    You are an intelligent AI research assistant.

    Your responsibilities:

    1. Answer questions using the supplied document passages.
    2. Use previous conversation messages to understand follow-up questions.
    3. Resolve references such as "it", "that project",
       "the first one", and "explain more" using conversation history.
    4. Never invent facts that are not supported by the documents.
    5. If the documents do not contain the requested information,
       clearly say so.
    6. Cite supporting page numbers in your answers.
    7. Give clear, friendly and well-structured explanations.
    8. Treat conversation history as context, not as evidence
       overriding the uploaded documents.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # 3. Add recent conversation history
    if history:
        for previous_message in history[-10:]:
            role = previous_message.get("role")
            content = previous_message.get("content", "")

            if role in ("user", "assistant") and content.strip():
                messages.append({
                    "role": role,
                    "content": content,
                })

    # 4. Add current question and retrieved document passages
    messages.append({
        "role": "user",
        "content": (
            f"Current question: {question}\n\n"
            f"Relevant document passages:\n{context}\n\n"
            "Answer the current question using these passages "
            "and the conversation history."
        ),
    })

    # 5. Generate response using Groq
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
