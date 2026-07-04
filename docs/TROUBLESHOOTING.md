# Troubleshooting

## Verify the environment

Run these commands from the repository root:

```bash
python --version
python -m pip show requests
ollama --version
ollama list
```

Python should be version 3.10 or later, `requests` should be installed in the
active environment, and `qwen2.5:7b` should appear in the Ollama model list.

## Ollama is unreachable

Typical error:

```text
ConnectionError: Failed to establish a new connection
```

Start the server in another terminal:

```bash
ollama serve
```

Then verify the API:

```bash
curl http://localhost:11434/api/tags
```

If Ollama is configured on another host or port, update `OLLAMA_URL` near the
top of each lab.

## The model is missing

Typical response:

```text
model 'qwen2.5:7b' not found
```

Download it and verify the installed name:

```bash
ollama pull qwen2.5:7b
ollama list
```

## Responses time out

The first response may be slow while Ollama loads a model. Try the model
directly with `ollama run qwen2.5:7b`. If the machine has insufficient memory,
choose a smaller model and change the `MODEL` constant in every lab. You can
also increase the HTTP timeout while learning, but that will not solve a model
that does not fit in memory.

## Tool calls are not detected

Lab 02 expects one JSON object and Lab 03 expects exact line prefixes. Local
models sometimes add Markdown, explanations, or malformed JSON. Print the raw
model response, compare it with the prompt format, and then improve either the
prompt or parser. Structured-output reliability is part of the lesson.

## Windows command differences

Use `py` if `python` is not available. Activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, consult your organisation's execution-policy
rules rather than disabling security controls globally.
