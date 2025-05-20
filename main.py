import os
from dotenv import load_dotenv
from openai import OpenAI
from project_memory import init_db, save_message_with_embedding, get_relevant_messages

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client using API key
client = OpenAI(api_key=api_key)
MODEL = "gpt-4o"

# Initialize local memory database
init_db()

def main():
    print("Welcome to your AI Assistant. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        # Save user message to vector memory
        save_message_with_embedding("user", user_input)

        # Retrieve relevant context
        relevant = get_relevant_messages(user_input, top_k=5)

        # Build message history
        message_history = [{"role": "system", "content": "You are a helpful developer assistant."}]
        for role, content in relevant:
            message_history.append({"role": role, "content": content})
        message_history.append({"role": "user", "content": user_input})

        try:
            # Send to GPT model (correct 1.x+ format)
            response = client.chat.completions.create(
                model=MODEL,
                messages=message_history
            )

            assistant_message = response.choices[0].message.content
            print(f"\nAssistant: {assistant_message}\n")

            # Save assistant reply to memory
            save_message_with_embedding("assistant", assistant_message)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
