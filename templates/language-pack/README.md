# Language-pack template

This directory is a skeleton for a new language pack. Its ID is `und`, the BCP 47
tag for an undetermined language, and it is never built or published.

1. Copy `pack.json`, `GUIDE.md`, `examples.md` and `LICENSE` into a new directory
   under `language-packs/`, named after the language ID. Leave this README out.
2. In `pack.json`, set the real `id`, the language's own display `name` and the
   writing `direction`. Use Yaya's restricted BCP 47 profile, for example `de`,
   `fr-CA`, `sr-Latn` or `es-419`. Keep `format_version: 1`, `core_major: 1`,
   `version: 1.0.0` for a first release and `quality: experimental`.
3. Replace every bracketed instruction in `GUIDE.md` and `examples.md` with
   original text written in the language you are adding. State which locales the
   guidance covers and where conventions differ.
4. Include acceptable and unacceptable revisions with reasons, plus a passage that
   should stay unchanged. Mark the examples as fictional. Do not invent facts to
   make a revision sound concrete.
5. Optionally add `PATTERNS.md` for removing formulaic wording: when a habit
   applies, exceptions, a revision and a case to keep. It is editorial text, not
   detector rules.
6. Include the full license text and meet its attribution terms. Then run
   `python core/yaya/scripts/packs.py validate language-packs/YOUR_ID`.
7. Arrange a review by a native editor. To claim `reviewed`, record the evidence in
   `REVIEW.md` as described in the [specification](../../docs/language-pack-spec.md).

Packs contain no `SKILL.md`, scripts, install commands or dependencies. A word or
punctuation mark alone does not show that a text was AI-written.

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for checks and submission.
