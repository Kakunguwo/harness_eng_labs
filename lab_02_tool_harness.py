"""
LAB 02 — Tool Harness
=====================
Goal: Extend Lab 01 with tool use. The agent can call Python functions
      when it needs to look something up or compute something.
Time: 15 minutes

Architecture:
    1. DEFINE  — describe tools as JSON schemas in the system prompt
    2. DETECT  — parse the LLM's structured response to find tool calls
    3. DISPATCH — route to the right Python function and run it
    4. FEED BACK — return the result as context for the final answer

Requires:
    pip install requests
"""

import json
import datetime
import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"

# ── TOOL IMPLEMENTATIONS ─────────────────────────────────────────────────────
# These are plain Python functions. The LLM never calls them directly.
# The HARNESS calls them after parsing what the LLM requested.

def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    """Safely evaluates a mathematical expression."""
    # Whitelist only safe built-ins to prevent code injection
    safe_names = {
        "__builtins__": {},
        "abs": abs, "round": round, "min": min, "max": max,
        "pow": pow, "sum": sum,
    }
    try:
        # eval(expression, globals, locals) with restricted globals
        result = eval(expression, safe_names, {})
        return str(result)
    except Exception as exc:
        return f"Error evaluating '{expression}': {exc}"


def word_count(text: str) -> str:
    """Returns the word count of a given string."""
    count = len(text.split())
    return f"{count} words"


# ── TOOL REGISTRY ─────────────────────────────────────────────────────────────
# The dispatch map: tool name → Python function.
# Adding a new tool = one function + one entry here.
TOOL_MAP = {
    "get_current_time": get_current_time,
    "calculate":        calculate,
    "word_count":       word_count,
}

# ── TOOL SCHEMAS (for the system prompt) ─────────────────────────────────────
TOOL_SCHEMAS = [
    {
        "name": "get_current_time",
        "description": "Returns the current date and time. Use when the user asks what time or date it is.",
        "parameters": {},
    },
    {
        "name": "calculate",
        "description": "Evaluates a mathematical expression and returns the result. Use for any arithmetic.",
        "parameters": {
            "expression": "A valid Python math expression, e.g. '144 * 7' or '2 ** 10'"
        },
    },
    {
        "name": "word_count",
        "description": "Counts the number of words in a text string.",
        "parameters": {
            "text": "The string to count words in."
        },
    },
]


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    tool_docs = json.dumps(TOOL_SCHEMAS, indent=2)
    return f"""You are a helpful AI assistant with access to tools.

    AVAILABLE TOOLS:
    {tool_docs}

    HOW TO USE A TOOL:
    If you need to use a tool, respond with ONLY a JSON object in this exact format:
    {{"tool_call": {{"name": "tool_name", "arguments": {{"param": "value"}}}}}}

    IMPORTANT RULES:
    - If using a tool: output ONLY the JSON. No extra text before or after.
    - If not using a tool: respond normally in plain text.
    - Never guess answers that require a tool. Call the tool instead.
    - For get_current_time which takes no arguments, use: {{"arguments": {{}}}}
    """


# ── HARNESS FUNCTIONS ─────────────────────────────────────────────────────────
def llm_call(messages: list[dict]) -> str:
    """Send messages to Ollama, return the text response."""
    r = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def parse_tool_call(response: str) -> tuple[str | None, dict]:
    """
    Try to extract a tool call from the LLM's response.
    Returns (tool_name, arguments) or (None, {}) if no tool call found.
    """
    text = response.strip()
    # Strip markdown code fences if the model wraps the JSON
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        data = json.loads(text)
        if "tool_call" in data:
            tc = data["tool_call"]
            return tc.get("name"), tc.get("arguments", {})
    except json.JSONDecodeError:
        pass
    return None, {}


def dispatch(tool_name: str, arguments: dict) -> str:
    """Look up the tool function and call it with the given arguments."""
    if tool_name not in TOOL_MAP:
        return f"[Harness error] Unknown tool: '{tool_name}'. Available: {list(TOOL_MAP.keys())}"
    fn = TOOL_MAP[tool_name]
    try:
        return fn(**arguments)
    except TypeError as exc:
        return f"[Harness error] Bad arguments for '{tool_name}': {exc}"


# ── AGENT LOOP ────────────────────────────────────────────────────────────────
def run():
    messages = [{"role": "system", "content": build_system_prompt()}]

    print(f"\n=== Tool Agent | model={MODEL} | type 'quit' to exit ===")
    print("Try: 'What time is it?'  |  'What is 47 * 89?'  |  'How many words in hello world foo bar?'\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Done.")
            break

        messages.append({"role": "user", "content": user_input})

        # ── First LLM call: may return a tool call or a direct answer ──
        first_response = llm_call(messages)
        tool_name, tool_args = parse_tool_call(first_response)

        if tool_name:
            # ── Tool path ──────────────────────────────────────────────
            print(f"\n  [HARNESS] Tool requested: {tool_name}({tool_args})")
            result = dispatch(tool_name, tool_args)
            print(f"  [HARNESS] Tool result:    {result}\n")

            # Record the assistant's tool-call response
            messages.append({"role": "assistant", "content": first_response})
            # Feed the result back as a user message
            messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}: {result}\n\nNow give your final answer to the user."
            })

            # ── Second LLM call: produce the final answer ──────────────
            final = llm_call(messages)
            messages.append({"role": "assistant", "content": final})
            print(f"Agent: {final}\n")

        else:
            # ── Direct answer (no tool needed) ─────────────────────────
            messages.append({"role": "assistant", "content": first_response})
            print(f"\nAgent: {first_response}\n")


# ── EXERCISES ─────────────────────────────────────────────────────────────────
# 1. Run: try "What time is it?", "What is 144 * 7?", "Word count: the quick brown fox"
#
# 2. Watch the [HARNESS] log lines — that's the harness in action.
#
# 3. Add a NEW TOOL: a get_weather stub
#    def get_weather(city: str) -> str:
#        return f"Sunny, 24°C in {city} (simulated)"
#    Add it to TOOL_MAP and TOOL_SCHEMAS. Test: "What's the weather in Harare?"
#
# 4. Break it on purpose: in dispatch(), change the fn(**arguments) line
#    to raise an exception. See how the error propagates. Then add a try/except.

if __name__ == "__main__":
    run()
