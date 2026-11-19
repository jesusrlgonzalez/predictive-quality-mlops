# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security
- Browser demo (Hugging Face Space): the Python requirements are pinned (`plotly==7.1.0`, `scikit-learn==1.7.0`, `pyyaml==6.0.2`, `scipy==1.14.1`, `openpyxl==3.1.5`, `et-xmlfile==2.0.0`), so the code that runs next to an uploaded file no longer changes between visits.
- The demo page sets a Content-Security-Policy whose `connect-src` only allows the page itself, jsDelivr and PyPI; it also applies to the Pyodide worker.
- The upload screen shows a data-use notice naming the third parties that receive the visitor's IP address (jsDelivr, PyPI, Google Fonts).

## [1.2.0] - 2026-10-17

### Added
- MVP «Dictamen de viabilidad de un modelo de calidad» (demo mode «Evalúa tu proceso», `make dictamen`): lot template and row-level validation in Spanish; chronological protocol with model and cost threshold chosen on expanding windows of the past; PR-AUC against chance, saving against the best simple alternative with bootstrap interval, sample size needed to prove it, leakage, drift and cost-sensitivity checks; one-page verdict in audit language. Pilot protocol in `docs/MVP_PILOTO.md`.
- «Señal de campo» theme and copyright footer in the demo.

## [1.1.0] - 2026-10-16

### Added
- MIT license, Model Card and English README with the Spanish version kept as `README.es.md`.
- Project page on GitHub Pages and a live demo on Hugging Face Spaces, published automatically from `main`.
- Release workflow: notes from this changelog and an evidence bundle attached to every tag.

### Removed
- C-MAPSS module, data and reports: the work lives in predictive-maintenance-survival-cmapss.

## [1.0.0] - 2026-10-05

### Added
- SECOM lot-risk model with chronological validation, cost-based threshold and release / monitor / hold taxonomy.
- Holdout evaluated once: PR-AUC 0.089 against a 0.054 failure rate; the saving is not statistically demonstrated and is reported as such.
- Drift monitoring, FastAPI service, Streamlit dashboard, prediction log, Docker and CI.
