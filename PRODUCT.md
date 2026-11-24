# Product

## Register

product

## Users
Professionals and learners who make or check claims of the form "X affects Y" from tabular data, but who don't write code:

- **Researchers and graduate students** in psychology, economics, public health, education and the social sciences. They test whether their own finding survives every defensible analysis before they submit a paper or thesis.
- **Analysts** in business, NGOs and government. They check whether a reported effect (a campaign, a policy, a diet) is real or an artefact of one analysis path.
- **Reviewers, supervisors and journal editors.** They audit someone else's claim: they load the shared data, re-run the reasonable alternatives, and check whether a reported number was cherry-picked.
- **Instructors.** They teach research methods and the replication crisis with the built-in simulator, often projected in a classroom.

**Context:** offline at a desk, on a laptop or office monitor in daylight, often with sensitive data (patients, employees, survey respondents) that must not be uploaded to web services. Sessions are focused, 10 to 30 minutes, and end with an artefact they hand to someone else: a report, a script or a locked plan.

## Product Purpose
Multiverse Studio answers one question with evidence: does this finding hold up under every reasonable way of analysing it?

It runs every defensible combination of analytic choices, excludes causally invalid ones (guardrails), prevents plan-tweaking after peeking (blind mode with a hashed plan), and shows whether a reported result is typical or cherry-picked.

Success means the user can defend their conclusion to a sceptical expert, with a reproducible script and report to back it, without having written a line of code.

## Brand Personality
**Trustworthy, calm, honest.**

The voice is that of a careful senior colleague: plain words first, the technical term in small text next to them, and numbers always explained in one sentence. It never hypes a result. A fragile finding is reported as clearly as a robust one. The aim is for users to feel confident and in control, never judged for not knowing statistics.

## Anti-references
- **SPSS and other legacy statistics packages:** grey dialog stacks, walls of unexplained numbers, output viewers nobody can read.
- **Flashy AI-startup dashboards:** gradients, glowing cards, glassmorphism, big vanity metrics, decorative motion.
- **Jargon-first interfaces** that make a beginner feel stupid, such as "specify the estimand" with no explanation.
- **Toy-like "friendly" apps** with emoji everywhere, bubbly shapes or cartoon tone. Reviewers and editors must take it seriously.

## Design Principles
1. **Evidence before verdict.** Show what was run and why before showing the conclusion. The verdict is a summary of visible numbers, never a black box.
2. **Plain words, precise terms.** Every concept gets a plain-language label first and the standard statistical term second, so experts and beginners both trust it.
3. **Honest by construction.** The interface makes the honest path the easy path: blind mode, guardrails, and showing left-out analyses rather than hiding them.
4. **One task per screen.** The wizard keeps each step focused. Nothing appears before the user needs it, and every step can be revisited.
5. **Professional calm.** Restrained colour, familiar controls, no decoration. Colour only ever means something (significance, state, selection).

## Accessibility & Inclusion
- WCAG 2.2 AA contrast for all text and UI components, in light and dark mode.
- Colour-blind safe: meaning is never carried by colour alone. Significance also appears in legends and text, and left-out analyses use hollow markers.
- Full keyboard operation: Tab order follows the wizard, Enter activates the primary action, Ctrl+1 to Ctrl+7 jump between steps.
- Projector and large-text mode: a text-size setting (100 / 115 / 130%) for classrooms and low vision.
- Minimal motion: only state changes (progress, step change). No decorative animation.
