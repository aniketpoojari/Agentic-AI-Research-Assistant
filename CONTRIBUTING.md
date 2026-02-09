# Contributing

Thanks for your interest in contributing! Here's how to get started.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/aniketpoojari/Agentic-AI-Research-Assistant.git
cd Agentic-AI-Research-Assistant
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with your API keys:

```ini
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
```

## Making Changes

1. Fork the repo and create a branch from `main`:
   ```bash
   git checkout -b feature/your-feature
   ```
2. Make your changes.
3. Run the evaluation to verify nothing is broken:
   ```bash
   python evaluation/run_evaluation.py
   ```
4. Commit and push:
   ```bash
   git commit -m "Add your feature"
   git push origin feature/your-feature
   ```
5. Open a Pull Request against `main`.

## Code Style

- Format with [Black](https://github.com/psf/black): `black .`
- Lint with [flake8](https://flake8.pycqa.org/): `flake8 .`
- Sort imports with [isort](https://pycqa.github.io/isort/): `isort .`

## Reporting Bugs

Use the [bug report template](https://github.com/aniketpoojari/Agentic-AI-Research-Assistant/issues/new?template=bug_report.md). Include:

- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## Suggesting Features

Use the [feature request template](https://github.com/aniketpoojari/Agentic-AI-Research-Assistant/issues/new?template=feature_request.md). Explain the problem and your proposed solution.
