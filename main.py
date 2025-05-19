import os
from dotenv import load_dotenv
from openai import OpenAI
from project_memory import init_db, save_message, get_messages

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)
MODEL = "gpt-4o"

# Initialize local memory DB
init_db()

def main():
    print("Welcome to your AI Assistant. Type 'exit' to quit.\n")

    # Start message history with system prompt
    message_history = [{"role": "system", "content": "You are a helpful developer assistant."}]

    # Load previous conversation (optional)
    previous = get_messages(limit=10)
    for role, content in previous:
        message_history.append({"role": role, "content": content})

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        # Add user message to history and save it
        message_history.append({"role": "user", "content": user_input})
        save_message("user", user_input)

        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model=MODEL,
                messages=message_history
            )

            assistant_message = response.choices[0].message.content
            print(f"\nAssistant: {assistant_message}\n")

            # Add assistant response to history and save it
            message_history.append({"role": "assistant", "content": assistant_message})
            save_message("assistant", assistant_message)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
