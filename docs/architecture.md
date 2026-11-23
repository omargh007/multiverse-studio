# Architecture

## Principles
1. **Core never imports the GUI.** `core/`, `io/` and `plots/` work in scripts and tests with no display. A test (`tests/core/test_no_gui_imports.py`) enforces this.
2. **One shared state.** The `Session` dataclass (`core/types.py`) holds everything about an analysis. Every GUI page reads and writes it, and every export starts from it.
3. **The GUI only calls `core.api`.** The GUI contains no analysis logic.
4. **Long work runs off the main thread.** The core runner reports through callbacks, and the GUI forwards them to a queue that it polls with `after()`.
5. **One seed, one purpose per random step** (`core/seed.py`, decision D-3).

## Layers

```mermaid
flowchart TB
    subgraph GUI["gui/ (CustomTkinter) - Owner B"]
        APP[app.py<br/>window + sidebar wizard]
        PAGES[pages/<br/>data, question, choices,<br/>guardrails, run, results, export]
        WORKER[worker.py<br/>thread + queue + after()]
        THEME[theme.py<br/>design tokens]
    end

    subgraph PLOTS["plots/ (Matplotlib Figures) - Owner B"]
        SC[spec_curve.py]
        IMP[importance.py]
    end

    subgraph CORE["core/ (no GUI) - Owner A"]
        API[api.py - public facade]
        TYPES[types.py - Session and contract]
        PROF[profiling.py]
        CH[choices.py]
        SPECS[specs.py]
        MOD[models.py - statsmodels]
        RUN[runner.py]
        INF[inference.py - verdict + permutation]
        GR[guardrails.py *novel*]
        BL[blind.py *novel*]
        CP[cherry.py *novel*]
        IM[importance.py]
        SIM[simulate.py]
        NAR[narrative.py]
        SEED[seed.py]
    end

    subgraph IO["io/ - Owners A and C"]
        LOAD[loaders.py]
        SCRIPT[export_script.py]
        JSON[export_json.py]
        PDF[export_pdf.py]
        STORE[session_store.py]
    end

    PAGES --> API
    PAGES --> WORKER
    PAGES --> SC & IMP
    PAGES --> LOAD & SCRIPT & JSON & PDF & STORE
    WORKER --> API
    API --> PROF & CH & SPECS & RUN & INF & GR & BL & CP & IM & SIM & NAR
    RUN --> MOD
    INF --> RUN
    SPECS & INF & BL & SIM --> SEED
    SCRIPT & JSON & PDF & STORE --> TYPES
    PDF --> SC & IMP
```

## User workflow (wizard steps)

| Step | Page | Core calls | Writes to `Session` |
|---|---|---|---|
| 1. Data | `pages/data.py` | `load_table`, `profile_data` | `data_path`, `profile` |
| 2. Question | `pages/question.py` | `suggest_family` | `y`, `x`, `family` |
| 3. Choices | `pages/choices.py` | `suggest_decisions`, `count_specs` | `decisions`, `max_specs` |
| 4. Guardrails | `pages/guardrails.py` | `assess_controls` | `guardrails`, `assessments` |
| 5. Run | `pages/run.py` | (blind) `blind_view`, `lock_plan` → `build_specs`, `iter_multiverse`, `mark_validity`, `permutation_test`, `summarize` | `blind`, `specs`, `results`, `verdict` |
| 6. Results | `pages/results.py` | `decision_importance`, `cherry_pick_check`, plots | `reported_estimate`, `cherry_pick` |
| 7. Export | `pages/export.py` | `export_script`, `export_json`, `export_pdf`, `methods_paragraph`, `results_paragraph`, `save_session` | none |

**Teaching mode** (sidebar button) calls `simulate(scenario)` and opens the result at step 2, so students can watch a known truth appear or disappear.

## Threading (step 5)

```mermaid
sequenceDiagram
    participant UI as Run page (main thread)
    participant W as Worker thread
    participant C as core.runner
    UI->>W: start(iter_multiverse, cancel_event)
    loop each universe
        W->>C: fit_one(...)
        C-->>W: SpecResult
        W->>UI: queue.put(("result", r))
    end
    UI->>UI: after(50ms) poll queue → update progress bar + live curve
    UI-->>W: cancel_event.set() (Cancel button)
    W->>UI: queue.put(("done", None))
```

## Ownership (folder = owner, so agents don't collide)

| Owner | Edits only | Must not edit |
|---|---|---|
| **A: Core** | `src/multiverse_studio/core/`, `io/loaders.py`, `io/export_script.py`, `tests/core/` | `gui/` |
| **B: GUI** | `src/multiverse_studio/gui/`, `src/multiverse_studio/plots/`, `tests/plots/` | `core/` (ask A) |
| **C: Release & evidence** | `io/export_json.py`, `io/export_pdf.py`, `io/session_store.py`, `tests/io/`, `.github/`, `pyproject.toml`, `docs/`, `examples/`, `paper/`, `README.md`, `CITATION.cff`, `CHANGELOG.md` | `core/`, `gui/` |

## Changing the contract
`core/types.py` and the function signatures in `core/api.py` are shared. To change them:
1. Open a small PR that touches **only** the contract.
2. Tag both teammates and merge once they've approved.
3. Then each person updates their own side.

## Git workflow
- `main` is protected. Work on branches named `a/...`, `b/...` or `c/...`, and merge via pull request once CI is green.
- Pull before every agent session and commit small changes often **from your own account**, because Git history is graded.
- Start each agent session with: *"Read docs/architecture.md and docs/decisions.md. I am owner X. Only edit my folders."*
