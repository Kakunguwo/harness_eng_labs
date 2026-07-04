# Lab Guide

Complete the labs in numerical order. Each lab is a standalone command-line
program, while the concepts build on the previous lab.

## Lab 01: Basic agent loop

Run:

```bash
python lab_01_basic_agent.py
```

The model itself does not remember previous API calls. The `messages` list is
the memory supplied by the harness. On every turn, the program sends the full
list to Ollama and appends both the user message and the assistant reply.

Suggested sequence:

1. Tell the agent your name and ask it to recall it.
2. Ask a question outside the quantity-surveying system prompt.
3. Change the system prompt and compare the behaviour.
4. Remove one history append operation and observe what context is lost.

Checkpoint: you can explain why the model appears to remember even though the
Ollama chat endpoint is stateless between requests.

## Lab 02: Tool harness

Run:

```bash
python lab_02_tool_harness.py
```

Try these prompts:

```text
What time is it?
What is 47 * 89?
How many words are in "agent harnesses coordinate model and code"?
```

Follow the request through four stages:

1. `TOOL_SCHEMAS` tells the model which tools are available.
2. `parse_tool_call` detects a structured request in the model output.
3. `dispatch` maps the requested name to a Python function.
4. The harness adds the tool result to the messages and asks for a final answer.

Checkpoint: add the simulated weather tool described in the source exercises
and explain why the model cannot call the Python function directly.

## Lab 03: ReAct agent

Run:

```bash
python lab_03_react_agent.py
```

Try a task that requires one tool, then a task that requires two:

```text
What is harness engineering?
What time is it and what is 7 * 8?
```

The loop repeats until the model emits `Final Answer` or reaches `MAX_STEPS`.
Each successful action produces an observation, which is appended to the
message history before the next model call.

Checkpoint: set `MAX_STEPS` to `1`, run a two-tool task, and explain why bounded
loops are required even when they can stop a valid task early.

## Reflection questions

After all three labs, consider:

1. Which responsibilities belong to the model, and which belong to the harness?
2. What happens when a model produces invalid JSON or an unknown tool name?
3. Where would you add tool permissions, retries, logging, and persistent memory?
4. How would the message history affect latency and context-window usage over
   a long conversation?
5. Which parts must change before accepting input from untrusted users?
