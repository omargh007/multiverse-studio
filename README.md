# Multiverse Studio

**Does your finding survive every reasonable way of analysing it? Find out without writing code.**

Multiverse Studio is a free, offline desktop app for **multiverse / specification-curve analysis** for researchers and students who don't program. You load a CSV or Excel file, pick your question (does X affect Y?), and tick the analysis choices you could reasonably make. The app runs every combination and shows whether your result is **consistent** or **fragile**.

What makes it different from existing tools such as specr, RobustiPy and Boba:

- 🖱️ **No code.** The whole workflow is point-and-click, and it exports a reproducible Python script.
- 🛡️ **Causal guardrails.** Plain-language questions flag *bad controls* (mediators and colliders) and exclude the invalid analyses.
- 🙈 **Blind mode.** You build and lock your analysis plan (with a SHA-256 hash) *before* the real results are revealed.
- 🎯 **Cherry-pick check.** Shows where a reported result sits among all valid analyses.

> Status: **in development** (v0.1.0.dev0). Screenshots will appear here.

## Install

```bash
pip install multiverse-studio        # after the first PyPI release
multiverse-studio                    # start the app
```

From source:

```bash
git clone https://github.com/omargh007/multiverse-studio.git
cd multiverse-studio
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
python -m multiverse_studio
```

Requires Python 3.10 or newer on Windows, Linux or macOS.

## Quick start (script, no GUI)

```python
from multiverse_studio.core import api
from multiverse_studio.io.loaders import load_table

df = load_table("survey.csv")
profile = api.profile_data(df)
family = api.suggest_family(profile, "grade")
decisions = api.suggest_decisions(profile, "grade", "sleep_hours")
specs = api.build_specs(decisions, max_specs=1000, seed=42)
results = api.run_multiverse(df, "grade", "sleep_hours", family, decisions, specs)
print(api.summarize(results).explanation)
```

## Development

```bash
pytest --cov            # tests + coverage
ruff check src tests    # lint
```

- Architecture and ownership: [docs/architecture.md](docs/architecture.md)
- Design decisions (verdict rule, seed, processing order): [docs/decisions.md](docs/decisions.md)
- Novelty search and feature plan: [docs/planning/](docs/planning/)

## Cite

See [CITATION.cff](CITATION.cff). A Zenodo DOI will be added with the first release.

## License

MIT. See [LICENSE](LICENSE).
