"""
LAB 01 — Basic Agent Loop
=========================
Goal: Build a multi-turn conversational agent with persistent message history.
Time: 5 minutes

Requires:
    pip install requests
"""

import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"

# ── CORE FUNCTION ─────────────────────────────────────────────────────────────
def chat(messages: list[dict]) -> str:
    """Send the full conversation history to Ollama and return the reply."""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False
            },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    message = data.get("message", {})

    if not message:
        raise ValueError(f"No message in response: {data}")

    content = message.get("content", "")

    if not content:
        raise ValueError(f"No content in message: {message}")

    return content


# ── AGENT LOOP ────────────────────────────────────────────────────────────────
def run():
    # The system prompt defines the agent's persona and behaviour.
    # This is the first message every request will include.
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Quantity Surveyor Expert and you only answer questions related to construction cost estimation, project management, and construction related queries. Do not answer questions outside your expertise. "
            ),
        }
    ]

    print(f"\n=== Basic Agent | model={MODEL} | type 'quit' to exit ===\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Done.")
            break

        # Append the user turn to history
        messages.append({"role": "user", "content": user_input})

        # Call the LLM with the FULL history every time
        reply = chat(messages)

        # Append the assistant reply to history so the next call has context
        messages.append({"role": "assistant", "content": reply})

        print(f"\nAgent: {reply}\n")


# ── EXERCISES ─────────────────────────────────────────────────────────────────
# 1. Run the agent. Ask it: "My name is [your name]. Remember it."
#    Then ask: "What is my name?" — it should remember.
#
# 2. Change the system prompt to: "You are a senior radiologist.
#    Answer medical imaging questions only."
#    Watch it refuse off-topic questions.
#
# 3. BREAK IT: comment out the line that appends the assistant reply
#    to messages. Ask a follow-up. Watch context disappear.
#
# 4. Count how many messages are in the list after 3 turns.
#    (add: print(f"  [DEBUG] messages in context: {len(messages)}") )

if __name__ == "__main__":
    run()
