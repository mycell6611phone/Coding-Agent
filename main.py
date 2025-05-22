import os
from dotenv import load_dotenv
from openai import OpenAI
from project_memory import init_db, save_message_with_embedding, get_relevant_messages

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from spellchecker import SpellChecker

# GitHub integration
from git import Repo, exc

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)
MODEL = "gpt-4o"

# Initialize memory
init_db()

# Token control parameters
MAX_TOKENS = 8192
DESIRED_RESPONSE_TOKENS = 800

# Autocorrect
spell = SpellChecker()

# Key bindings
bindings = KeyBindings()

@bindings.add('c-q')
def _(event):
    print("\n[Ctrl+Q pressed] Exiting.")
    event.app.exit(result="__exit__")

session = PromptSession(key_bindings=bindings, multiline=True)

# --- Utility Functions ---

def correct_spelling(text):
    words = text.split()
    valid_words = [w for w in words if w.isalpha()]
    corrected = [spell.correction(w) if w in spell.unknown(valid_words) else w for w in valid_words]
    output = []
    vi = 0
    for w in words:
        if w.isalpha():
            output.append(corrected[vi])
            vi += 1
        else:
            output.append(w)
    return " ".join(output)

def num_tokens_from_messages(messages):
    return sum(len(m["content"].split()) for m in messages)

def trim_messages_to_fit(messages, max_tokens):
    current_token_count = num_tokens_from_messages(messages)
    while current_token_count > max_tokens and len(messages) > 1:
        messages.pop(1)
        current_token_count = num_tokens_from_messages(messages)
    return messages

def prepare_messages_within_token_limit(messages):
    available_tokens = MAX_TOKENS - DESIRED_RESPONSE_TOKENS
    if num_tokens_from_messages(messages) > available_tokens:
        messages = trim_messages_to_fit(messages, available_tokens)
    return messages

# --- File Upload Feature ---

def upload_file(filepath):
    if not os.path.isfile(filepath):
        print(f"[error] File not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    print(f"\n[uploaded] '{filepath}' ({len(content)} characters):\n")
    print(content[:1000])
    print("\n[...file preview truncated...]\n" if len(content) > 1000 else "")
    # Optional: Save to DB or embed here
    # save_message_with_embedding("file", f"Filename: {filepath}\n\n{content}")
    return content

# --- GitHub Integration ---

def clone_repo(repo_url, dest_folder):
    try:
        if os.path.exists(dest_folder):
            print(f"[info] Folder '{dest_folder}' already exists.")
            return
        Repo.clone_from(repo_url, dest_folder)
        print(f"[success] Repo cloned to '{dest_folder}'")
    except exc.GitCommandError as e:
        print(f"[error] Git error: {e}")

def pull_repo(dest_folder):
    try:
        repo = Repo(dest_folder)
        origin = repo.remotes.origin
        origin.pull()
        print(f"[success] Pulled updates in '{dest_folder}'")
    except Exception as e:
        print(f"[error] {e}")

def show_file(repo_folder, filename):
    filepath = os.path.join(repo_folder, filename)
    if not os.path.isfile(filepath):
        print(f"[error] File not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    print(f"\n[file: {filename}]\n")
    print(content[:1000])
    print("\n[...file preview truncated...]\n" if len(content) > 1000 else "")

def diff_file(repo_folder, commit1, commit2, filename):
    repo = Repo(repo_folder)
    try:
        diff = repo.git.diff(f"{commit1}", f"{commit2}", "--", filename)
        print(f"\n[diff {filename} between {commit1} and {commit2}]\n")
        print(diff[:2000])
        print("\n[...diff truncated...]\n" if len(diff) > 2000 else "")
    except Exception as e:
        print(f"[error] {e}")

# --- Main Loop ---

def main():
    print("Welcome to your AI Coding Agent.")
    print("Commands:")
    print("  /upload <filepath>")
    print("  /github clone <repo_url>")
    print("  /github pull <repo_folder>")
    print("  /github show <repo_folder> <filename>")
    print("  /github diff <repo_folder> <commit1> <commit2> <filename>")
    print("Use Enter for new lines. Press Ctrl+Q to quit.\n")

    while True:
        try:
            user_input = session.prompt("You: ")
            if user_input == "__exit__":
                break

            user_input = user_input.strip()
            if not user_input:
                continue

            # --- File Upload Command ---
            if user_input.startswith("/upload "):
                filepath = user_input.split(" ", 1)[1].strip()
                upload_file(filepath)
                continue

            # --- GitHub Clone ---
            if user_input.startswith("/github clone "):
                url = user_input.split(" ", 2)[2].strip()
                dest = os.path.basename(url.rstrip("/")).replace(".git", "")
                clone_repo(url, dest)
                continue

            # --- GitHub Pull ---
            if user_input.startswith("/github pull "):
                dest = user_input.split(" ", 2)[2].strip()
                pull_repo(dest)
                continue

            # --- GitHub Show ---
            if user_input.startswith("/github show "):
                try:
                    _, _, rest = user_input.partition(" ")
                    repo_folder, filename = rest.strip().split(" ", 1)
                    show_file(repo_folder, filename)
                except ValueError:
                    print("[error] Usage: /github show <repo_folder> <filename>")
                continue

            # --- GitHub Diff ---
            if user_input.startswith("/github diff "):
                try:
                    _, _, rest = user_input.partition(" ")
                    repo_folder, commit1, commit2, filename = rest.strip().split(" ", 3)
                    diff_file(repo_folder, commit1, commit2, filename)
                except ValueError:
                    print("[error] Usage: /github diff <repo_folder> <commit1> <commit2> <filename>")
                continue

            # --- Normal AI Chat ---
            corrected_input = correct_spelling(user_input)
            if corrected_input != user_input:
                print(f"[corrected] → {corrected_input}")

            save_message_with_embedding("user", corrected_input)
            relevant = get_relevant_messages(corrected_input, top_k=5)

            message_history = [{"role": "system", "content": "You are a helpful developer assistant."}]
            for item in relevant:
              role, content = None, None

              if isinstance(item, dict):
                role = item.get('role')
                content = item.get('content')
              elif isinstance(item, (list, tuple)) and len(item) == 2:
                role, content = item

            if isinstance(role, str) and isinstance(content, str):
                message_history.append({"role": role, "content": content})
            message_history.append({"role": "user", "content": corrected_input})

            message_history = prepare_messages_within_token_limit(message_history)

            print("[debug] Sending request to OpenAI...")
            response = client.chat.completions.create(
                model=MODEL,messages=message_history, max_tokens=DESIRED_RESPONSE_TOKENS,
                    timeout=30
            )

            assistant_message = response.choices[0].message.content
            print(f"\nAssistant: {assistant_message}\n")
            save_message_with_embedding("assistant", assistant_message)

        except KeyboardInterrupt:
            print("\n[Session interrupted] Exiting.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
