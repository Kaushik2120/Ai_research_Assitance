from app.services.conversation_service import (
    create_conversation,
    save_message,
    get_conversation_history,
    list_conversations,
)

# Create conversation
conversation = create_conversation("MyFirst AI Chat")

conversation_id = conversation["conversation_id"]

print("Conversation created:")
print(conversation)

# Save user message
save_message(
    conversation_id,
    "user",
    "Explain machine learning."
)

# Save assistant response
save_message(
    conversation_id,
    "assistant",
    "Machine learning is a branch of AI..."
)

# Retrieve conversation
print("\nConversation history:")

history = get_conversation_history(conversation_id)

for message in history:
    print(message["role"], ":", message["content"])

# List conversations
print("\nAll conversations:")
print(list_conversations())