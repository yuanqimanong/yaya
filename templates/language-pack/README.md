# Language-pack authoring template

Use this French (`fr`) example to create a language pack. It is experimental,
has not received native-editor review, and is not a released or validated pack.

1. Copy only `pack.json`, `GUIDE.md`, `examples.md`, and `LICENSE` into a directory
   named for the intended language ID, normally under `language-packs/`.
   Do not copy this README into the pack.
2. Set the real `id`, native display `name`, and `direction`. Follow Yaya's restricted
   BCP 47 profile, for example `fr`, `fr-CA`, `ar`, or `sr-Latn`.
3. Use `format_version: 1` and `core_major: 0`. The template's content version is `0.2.0`
   with `quality: experimental`; pack versions are independent of the core's patch/minor version.
4. Write original guidance and examples in the language you are contributing.
   Cover prose, comments, prompts, and sample-based style learning. State which
   locales the guidance covers and where conventions differ.
5. Include acceptable and unacceptable revisions, with reasons, plus an already-good
   passage that should remain unchanged. Mark fictional examples. Do not invent facts
   to make a revision sound concrete or natural.
   Optionally add `PATTERNS.md` for humanize and detect guidance: triggers, exceptions,
   revisions, and unchanged cases. It contains editorial text, not runnable detector rules.
6. Include the applicable full license text and satisfy attribution obligations.
   Run `python core/yaya/scripts/packs.py validate YOUR_PACK_DIRECTORY`.
7. Arrange human language review. To claim `reviewed`, record the evidence
   in `REVIEW.md` as required by the [specification](../../docs/language-pack-spec.md).
   If claiming reviewed humanize patterns, include `PATTERNS.md` and review evidence
   for those patterns. Without it, state which guide and example tasks were reviewed.

Keep `SKILL.md`, scripts, install commands, and dependencies outside the pack.
Guidance must follow the core and the user's task. Review wording in context;
a word or punctuation mark alone does not establish AI authorship.

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for evaluation and submission guidance.
