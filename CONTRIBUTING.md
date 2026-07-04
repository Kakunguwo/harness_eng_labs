# Contributing

Contributions should keep the repository approachable for learners.

## Before submitting a change

1. Create and activate a virtual environment.
2. Install `requirements.txt`.
3. Ensure Ollama is running with the documented model.
4. Run all three labs and exercise the path affected by your change.
5. Compile-check the source files:

```bash
python -m py_compile lab_01_basic_agent.py lab_02_tool_harness.py lab_03_react_agent.py
```

## Style guidelines

- Prefer standard-library Python unless a dependency clearly improves the
  lesson.
- Keep each lab runnable as a standalone script.
- Explain new concepts close to the code that demonstrates them.
- Add an exercise when introducing a meaningful concept.
- Do not commit virtual environments, model files, credentials, or generated
  caches.
- Keep examples generic and remove private organisation or customer data.

## Commit guidance

Use a short, descriptive commit subject, for example:

```text
docs: clarify Ollama model setup
feat: add validated weather tool exercise
fix: handle malformed ReAct action input
```
