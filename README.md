# Local AI Agent Harness Labs

A small, practical course for learning how an AI agent harness works with a
locally hosted large language model. The labs use Python and Ollama, so no
cloud API key is required and prompts remain on your machine.

The course builds one idea at a time:

1. Maintain conversation history around a stateless model.
2. Give the model access to Python tools through a controlled harness.
3. Build a multi-step ReAct loop that reasons, acts, and observes.

## Learning outcomes

After completing the labs, you should be able to:

- explain the difference between an LLM and an agent harness;
- manage multi-turn conversation state;
- define, detect, and dispatch tool calls;
- feed tool results back to a model;
- implement a bounded ReAct control loop; and
- identify common reliability and safety limits in simple agents.

## Prerequisites

You need:

- Python 3.10 or later;
- `pip` and Python virtual environments;
- [Ollama](https://ollama.com/) installed and running locally;
- at least 8 GB of system memory for the default 7B model, with more memory
  recommended; and
- basic familiarity with Python functions, dictionaries, loops, and JSON.

Git is only required if you want to clone or contribute to the repository.

## Quick start

### 1. Create a virtual environment

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install the Python dependency

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Install and prepare Ollama

Install Ollama using the instructions for your operating system, then download
the model used by the labs:

```bash
ollama pull qwen2.5:7b
```

Ollama normally starts automatically. If it is not running, start it in a
separate terminal:

```bash
ollama serve
```

Confirm that the model is available:

```bash
ollama list
ollama run qwen2.5:7b "Reply with: Ollama is ready"
```

The examples expect Ollama at `http://localhost:11434`.

### 4. Run the labs in order

```bash
python lab_01_basic_agent.py
python lab_02_tool_harness.py
python lab_03_react_agent.py
```

Type `quit`, `exit`, or `q` to stop any lab.

## Course structure

| Lab | File | Main idea | Suggested time |
| --- | --- | --- | --- |
| 01 | `lab_01_basic_agent.py` | Conversation history and system prompts | 5–10 minutes |
| 02 | `lab_02_tool_harness.py` | Tool schemas, parsing, dispatch, and feedback | 15–20 minutes |
| 03 | `lab_03_react_agent.py` | A bounded Reason-and-Act loop | 15–25 minutes |

Each file contains exercises at the bottom. Run the program once unchanged,
then complete the exercises and deliberately break the indicated parts. The
failure modes are an important part of the course.

## Engineering notes

The documentation is arranged so learners can move from usage into system
design without having to infer the architecture from the source code.

| Note | Purpose |
| --- | --- |
| [Lab guide](docs/LABS.md) | Run order, exercises, and learning checkpoints |
| [Concepts and architecture](docs/CONCEPTS.md) | Core terminology and the overall harness model |
| [Engineering notes](docs/ENGINEERING_NOTES.md) | Components, interfaces, data contracts, failure modes, testing, and production concerns |
| [Lab 01 notes](docs/LAB_01_BASIC_AGENT.md) | Conversation state and the basic agent loop |
| [Lab 02 notes](docs/LAB_02_TOOL_HARNESS.md) | Structured tool requests and dispatch flow |
| [Lab 03 notes](docs/LAB_03_REACT_AGENT.md) | ReAct state machine and bounded execution |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Environment and runtime diagnostics |

The engineering notes contain Mermaid diagrams that render directly on GitHub.

## Using another local model

The labs use `qwen2.5:7b` because it is small enough for many development
machines and generally follows structured output instructions well. You may
replace the `MODEL` constant near the top of each lab with another Ollama model.

For example:

```bash
ollama pull llama3.1:8b
```

Then change:

```python
MODEL = "llama3.1:8b"
```

Tool-use exercises depend on exact JSON or ReAct formatting. Smaller models
may drift from the requested format more often. That is useful to observe, but
it can make Labs 02 and 03 less predictable.

## Troubleshooting

- `Connection refused`: start Ollama with `ollama serve` and retry.
- `model not found`: run `ollama pull qwen2.5:7b`.
- `ModuleNotFoundError: requests`: activate the virtual environment and run
  `python -m pip install -r requirements.txt`.
- Slow responses or timeouts: close memory-heavy applications or choose a
  smaller Ollama model and update `MODEL` in all three files.
- Unexpected tool output: local models do not always follow a format exactly.
  Inspect the raw response and strengthen the prompt or parser.

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for diagnostic commands
and additional fixes.

## Safety and scope

This project is intentionally minimal and intended for education. It is not a
production agent framework.

- Lab 02 and Lab 03 evaluate model-generated mathematical expressions with a
  restricted `eval`. Do not expose these examples as a public service or use
  them with untrusted input.
- Conversation history is held only in memory and is lost when the process
  exits.
- Tools have no authentication, permission model, sandbox, or audit store.
- ReAct `Thought` output is included to teach the control loop. Production
  systems should use concise, structured decision records rather than depend
  on hidden model reasoning.

## Contributing

Corrections and additional educational exercises are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a change.

## License

No license has been selected yet. Until the repository owner adds one, normal
copyright restrictions apply.
