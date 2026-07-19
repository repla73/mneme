# Contributing

1. Preserve the immutable-ledger and deterministic-reducer invariants.
2. Add tests for every schema or authority change.
3. Platform capability claims require a current primary-source URL.
4. Do not create platform forks; add or revise an adapter manifest and implementation package.
5. Regenerate schemas and the platform matrix after contract changes.
6. Run `pytest`, `ruff check .`, and `python -m compileall -q src` before opening a pull request.
