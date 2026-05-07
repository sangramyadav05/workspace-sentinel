# Workspace Sentinel

Workspace Sentinel is a small, security-focused CLI agent that keeps AI interaction read-only, restricts file access to a local workspace, and requires explicit approval before sensitive actions.

## Features

- Read-only AI interaction through OpenRouter
- Workspace-only file reads and writes
- Explicit human approval for sensitive operations
- Session timeout and command rate limiting
- Local short-term and long-term memory
- Unit tests for command flow, storage, and safety checks

## Project Layout

- `main.py`: CLI entry point and runtime bootstrap
- `agent/`: AI provider integration
- `core/`: command processing, safety checks, file access, and audit helpers
- `interface/`: terminal input boundary
- `memory/`: short-term and long-term memory logic
- `tests/`: regression and unit tests
- `workspace/`: runtime-only sandbox directory

## Setup

1. Install Python 3.11 or newer.
2. Create a virtual environment outside this repository, or use your own Python environment.
3. Install dependencies:

```bash
pip install -e .
```

4. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`.

## Run

```bash
python main.py
```

## Test

```bash
python -m unittest discover -v
```

## Notes

- `.env`, logs, caches, memory data, and workspace contents are intentionally ignored by Git.
- The `workspace/` directory is kept empty in the repo except for `.gitkeep`.
