# Contributing

Thanks for your interest in contributing to claude-workspace!

## Getting started

1. Fork and clone the repo
2. Install system dependencies: `sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91`
3. Run directly: `PYTHONPATH=. python3 -m claude_workspace`

## Code style

- PEP 8, max line length 100
- No comments — code should be self-explanatory
- Functions should be short and focused
- Run `make lint` before submitting

## Submitting changes

1. Create a branch from `main`
2. Make your changes
3. Run `make lint`
4. Open a pull request with a clear description

## Reporting bugs

Open an issue with:
- What you expected
- What happened
- Your OS and Python version
