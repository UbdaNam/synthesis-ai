# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a small Python application.
- `main.py`: entry point for local execution.
- `pyproject.toml`: project metadata and Python version requirement (`>=3.14`).
- `README.md`: short project description.
- `.specify/`: planning/templates/scripts for spec-driven workflows (not runtime app code).
- `.codex/`: local agent prompts/configuration.

Keep new runtime code under a dedicated package directory (for example, `src/synthesis_ai/`) and place tests in `tests/`.

## Build, Test, and Development Commands
Use these commands from the repository root:
- `python main.py` - run the current app entrypoint.
- `python -m py_compile main.py` - quick syntax check.
- `python -m pytest` - run test suite (after adding tests and `pytest`).

If you add dependencies, update `pyproject.toml` and keep commands reproducible from a clean environment.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Prefer small, single-purpose functions and explicit return values.
- Add type hints to new/changed Python code where practical.

Example naming:
- `process_document()` (function)
- `DocumentPipeline` (class)
- `DEFAULT_TIMEOUT_SECONDS` (constant)

## Testing Guidelines
- Use `pytest` for unit and integration tests.
- Name files `test_*.py` and tests `test_<behavior>()`.
- Co-locate fixtures in `tests/conftest.py` when shared.
- Add or update tests for every behavioral change; include at least one regression test for bug fixes.

## Commit & Pull Request Guidelines
Current history uses short, imperative commit subjects (for example, `setup python project`).
- Keep commit subject lines concise and action-oriented.
- One logical change per commit.
- Reference issue IDs in the body when applicable.

For pull requests:
- Explain what changed and why.
- List test evidence (commands + results).
- Include screenshots/log snippets for UI or workflow-visible changes.
- Call out follow-up work or known limitations explicitly.
