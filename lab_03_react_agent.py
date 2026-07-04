"""
LAB 03 — ReAct Agent
====================
Goal: Implement the ReAct (Reason + Act) pattern.
      The agent thinks step-by-step, takes an action, observes the result,
      then thinks again — until it has a final answer.
Time: 15 minutes

ReAct paper: Yao et al. 2022 — "ReAct: Synergizing Reasoning and Acting in Language Models"

Each step the agent outputs:
    Thought:      [its current reasoning]
    Action:       [tool name]
    Action Input: [JSON arguments]

When done:
    Thought:      [final reasoning]
    Final Answer: [the answer to the user]

Requires:
    pip install requests
"""

import json
import datetime
import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"
MAX_STEPS = 6   # Safety cap: prevents infinite loops if the model misbehaves


# ── TOOLS ─────────────────────────────────────────────────────────────────────
def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    safe = {"__builtins__": {}, "abs": abs, "round": round, "pow": pow}
    try:
        return str(eval(expression, safe, {}))  # noqa: S307
    except Exception as exc:
        return f"Error: {exc}"


def search_memory(query: str) -> str:
    """
    A simple in-memory knowledge base.
    In production this would be a vector DB lookup or RAG call.
    """
    kb = {
        "harness":    "A harness is scaffolding that wraps an LLM — giving it tools, memory, and a control loop. It turns a stateless text predictor into an agent.",
        "react":      "ReAct stands for Reason and Act. The agent produces a Thought before each Action, making its decisions auditable and debuggable.",
        "ollama":     "Ollama is a local LLM runtime. It lets you run models like Llama, Mistral, and Qwen entirely on your own machine — no data leaves.",
        "local models": "Local models run on infrastructure you control. This can improve privacy and offline access, while hardware limits affect speed and model quality.",
        "agentic":    "Agentic AI refers to systems where an LLM takes a sequence of actions autonomously to complete a task, rather than just answering a single question.",
        "tool use":   "Tool use lets an agent call external functions — databases, APIs, calculators — to get information it cannot produce from its weights alone.",
        "memory":     "In a harness, memory is the messages list. It holds the full conversation. There is no implicit memory — everything must be in the list.",
    }
    query_lower = query.lower()
    for key, value in kb.items():
        if key in query_lower:
            return value
    # Partial match fallback
    for key, value in kb.items():
        if any(word in query_lower for word in key.split()):
            return value
    return "No matching information found in memory."


# ── TOOL REGISTRY ─────────────────────────────────────────────────────────────
TOOLS = {
    "get_current_time": {
        "fn":          get_current_time,
        "description": "Get the current date and time. Args: none — use {}.",
    },
    "calculate": {
        "fn":          calculate,
        "description": 'Evaluate a math expression. Args: {"expression": "2 ** 10"}.',
    },
    "search_memory": {
        "fn":          search_memory,
        "description": 'Search the knowledge base. Args: {"query": "what is harness engineering"}.',
    },
}


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
TOOL_DOCS = "\n".join(
    f"- {name}: {info['description']}" for name, info in TOOLS.items()
)

SYSTEM_PROMPT = f"""You are a ReAct agent. You solve tasks by alternating between reasoning and action.

                AVAILABLE TOOLS:
                {TOOL_DOCS}

                FORMAT — use this EXACTLY for each step:

                Thought: [your reasoning about what to do next]
                Action: [tool_name]
                Action Input: [JSON object with arguments, or {{}} if no arguments]

                When you have the final answer:

                Thought: [your final reasoning]
                Final Answer: [the answer to the user's task]

                RULES:
                - Always start with a Thought.
                - Always output EITHER (Thought + Action + Action Input) OR (Thought + Final Answer).
                - Never mix both in the same response.
                - Action Input must be valid JSON on a single line.
                - Do not make up tool results. Wait for the Observation.
                """


# ── HARNESS FUNCTIONS ─────────────────────────────────────────────────────────
def llm_call(messages: list[dict]) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def parse_react_step(text: str) -> dict:
    """
    Parse a ReAct-formatted LLM response into its components.
    Returns a dict with keys: thought, action, action_input, final_answer.
    """
    result = {"thought": None, "action": None, "action_input": None, "final_answer": None}
    current_key = None
    buffer = []

    for line in text.strip().split("\n"):
        if line.startswith("Thought:"):
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "thought"
            buffer = [line[8:].strip()]
        elif line.startswith("Action:") and "Action Input" not in line:
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "action"
            buffer = [line[7:].strip()]
        elif line.startswith("Action Input:"):
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "action_input"
            buffer = [line[13:].strip()]
        elif line.startswith("Final Answer:"):
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "final_answer"
            buffer = [line[13:].strip()]
        else:
            if current_key:
                buffer.append(line.strip())

    if current_key and buffer:
        result[current_key] = " ".join(buffer).strip()

    return result


def dispatch(tool_name: str, action_input_str: str) -> str:
    """Parse action input JSON and call the appropriate tool."""
    if tool_name not in TOOLS:
        return f"Unknown tool '{tool_name}'. Available: {list(TOOLS.keys())}"
    try:
        args = json.loads(action_input_str) if action_input_str and action_input_str.strip() not in ("{}", "") else {}
    except json.JSONDecodeError:
        args = {}
    try:
        return TOOLS[tool_name]["fn"](**args)
    except Exception as exc:
        return f"Tool error: {exc}"


# ── REACT AGENT ───────────────────────────────────────────────────────────────
def run_task(task: str) -> str:
    """
    Run one task through the ReAct loop.
    Returns the final answer string.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Task: {task}"},
    ]

    print(f"\n{'─'*60}")
    print(f"Task: {task}")
    print('─'*60)

    for step_num in range(1, MAX_STEPS + 1):
        response = llm_call(messages)
        parsed = parse_react_step(response)

        thought = parsed.get("thought") or "(no thought)"
        print(f"\nStep {step_num} | Thought: {thought}")

        # ── Final answer ───────────────────────────────────────────────
        if parsed.get("final_answer"):
            answer = parsed["final_answer"]
            print(f"\nFinal Answer: {answer}")
            return answer

        # ── Tool call ──────────────────────────────────────────────────
        action = parsed.get("action")
        action_input = parsed.get("action_input") or "{}"

        if action:
            print(f"         Action: {action}")
            print(f"         Input:  {action_input}")
            observation = dispatch(action, action_input)
            print(f"         Obs:    {observation}")

            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user",      "content": f"Observation: {observation}"})
        else:
            # No action and no final answer — model drifted from format
            print(f"  [HARNESS] No action or final answer found. Raw response:\n{response}")
            return f"(Agent did not produce a structured response: {response[:200]})"

    return "(Max steps reached without a final answer)"


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def run():
    print(f"\n=== ReAct Agent | model={MODEL} | MAX_STEPS={MAX_STEPS} | type 'quit' to exit ===")
    print("\nSuggested tasks:")
    print("  > What is 1764 / 4, and what time is it right now?")
    print("  > What is harness engineering?")
    print("  > What is 2 to the power of 8?")
    print("  > How many words in 'agentic systems build the future of AI'?\n")

    while True:
        task = input("Task: ").strip()
        if not task:
            continue
        if task.lower() in ("quit", "exit", "q"):
            print("Done.")
            break
        run_task(task)
        print()


# ── EXERCISES ─────────────────────────────────────────────────────────────────
# 1. Run: "What is harness engineering?" — watch it reason, then search_memory.
#
# 2. Run: "What is the square root of 1764?" — it should use calculate.
#    Hint: the LLM may write "1764 ** 0.5" — that's fine, eval handles it.
#
# 3. Run: "What time is it and what is 7 * 8?" — watch it take 2 action steps.
#
# 4. Add a new entry to the knowledge base (kb dict in search_memory).
#    Try a topic relevant to a project or subject you are studying.
#
# 5. Change MAX_STEPS to 1. What happens on a multi-step task?
#    This simulates a real risk: budget limits in production agents.

if __name__ == "__main__":
    run()
