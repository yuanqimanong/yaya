# Changelog

## 0.2.0 — Unreleased

- Add humanizing guidance with original editing and preservation examples
  for English, Simplified Chinese, Traditional Chinese, Japanese and Korean.
- Support review-only, rewrite and scoped file-edit requests.
- Add optional, read-only English/Chinese wording candidates and mechanical rewrite checks.
- Use one language-pack format with optional `PATTERNS.md`, update backups and rollback.
- Expand evaluation materials to 112 cases, independent CLI generation, anonymous
  review and fixed-source competitor comparisons. Complete the initial 112-case
  comparison, 60-case competitor comparison, targeted retests and four downstream
  prompt checks; preserve failures and conflicting model judgments in the
  [evaluation report](tests/results/2026-10-20-upgrade/README.md).
- Remove whole sentences of empty praise where appropriate, preserve substantive
  opinions, and check for padding left after editing an opening.
- Preserve the existing prompt, comment and style-learning tasks and the small,
  standard-library-only runtime.

## 0.1.0 — Unreleased prototype

- Introduce prose, comment and prompt editing, plus sample-based style guidance.
- Bundle Simplified Chinese and English; package other languages independently.
- Add Python comment-boundary checks, pack validation and reproducible builds.
- Record initial tests and limited model comparisons under `tests/results/`.
