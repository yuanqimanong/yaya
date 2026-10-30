# Contributing to Yaya

Contributions to Yaya (牙牙学语) can improve an edit, add language guidance, or fix a local helper. Start with a concrete case and show how the change helps. Keep ordinary editing simple.

## Choose the right place

- `core/yaya/SKILL.md`: discovery, shared editing boundaries, and task selection.
- `core/yaya/catalog.json`: command contracts, options and domain inventory. Help and
  task planning use this same data through `scripts/yaya.py`.
- `core/yaya/references/`: guidance specific to text, comments, prompts, style learning, or language-pack use.
- `core/yaya/languages/`: the bundled `zh-Hans` and `en` packs.
- `language-packs/`: optional `zh-Hant`, `ja`, and `ko` packs.
- `core/yaya/scripts/`: local helpers, using the Python standard library without third-party runtime dependencies.

For a new command, define one bounded action, its permitted options and delivery;
test rejected combinations as well as successful routing. For a domain profile,
state concrete coverage, exclusions, protected relationships and source rationale.
Add editing, preservation and counterexample cases to `tests/evals/commands-domains.json`.
Keep profiles experimental until stronger evidence warrants a documented change.
A source citation, successful parser test or uncalibrated model judgment is not
professional certification. Update the release build and relocation checks when
adding runtime resources. Never replace actual execution evidence with intended checks.
- `tests/`: editing evaluations and helper tests. File-operation tests use temporary directories.

Language packs follow one current [specification](docs/language-pack-spec.md): `format_version: 1` with `core_major: 0` for the current core's major version. They may include `PATTERNS.md` for language-specific humanizing guidance. All five current packs are `experimental`.

For a new language, copy the pack files from the [French (`fr`) template](templates/language-pack/README.md) into a new directory. The template demonstrates authoring; French is not a released or validated pack. Leave the template's README out of the pack and ZIP.

## Before changing a rule

Record the request, source material, current failure and what a correct edit must preserve. Compare the current guidance against the same model with a simple editing request before adding more instructions.

Make the smallest correction that addresses the case. Use a clear principle and a representative example; a forbidden-word list rarely captures context. Put task-specific guidance in its reference file. Add an external service, extra model call or installation step only when the feature requires it.

For a humanizing rule, show when it applies, what it improves and a counterexample to preserve. Keep machine-detectable patterns in `core/yaya/scripts/tell_rules.json`; language packs cannot supply executable rules or scripts. Detection changes need false-positive cases and protected-content checks. Editing evaluations must also check conditions, attribution and relationships that token comparisons cannot establish.

Wording candidates do not identify an author, and a lack of findings does not establish that a text is human-written. The local detector currently accepts only `en` and `zh-Hans`; adding a language pack or `PATTERNS.md` does not extend it.

Write original instructions and examples. Check licensing and attribution before reusing another project's text or code. Keep personal data, private conversations and material that cannot be redistributed out of contributions.

## Language contributions

Include examples for the language's regional and register choices. Traditional Chinese needs more than script conversion; Japanese and Korean need attention to politeness levels. Preserve a requested locale even when a broader pack supplies guidance, and let domain and audience guide terminology.

Include both useful edits and passages to leave unchanged. Check meaning, natural expression and language-specific boundaries. Ground the output's facts in the input: inventing a metric to sound more concrete is a failure.

Use `quality: experimental` until a documented review justifies `reviewed`. For `reviewed`, add `REVIEW.md` recording actual human language review and evaluations, including scope, reviewer role, date, cases, model/settings where applicable, observed failures, and limitations. A schema check, model self-score, or lower word count is not an editorial evaluation.

The validator checks that the review file exists and has content. Contributors must verify the evidence inside it.

## Check the change

From the repository root:

```text
python -m unittest discover -s tests -v
python core/yaya/scripts/packs.py validate core/yaya/languages/zh-Hans
python core/yaya/scripts/packs.py validate language-packs/ja
```

Use the pack path relevant to your change. For helpers, test failures as well as success: unsupported input, incompatible metadata, archive boundaries, checksum mismatch and preservation of existing data where applicable. Test behavior, rather than a particular heading or the implementation's shape.

For editing guidance, use realistic requests in fresh model contexts. Retain the complete source, request and output, and assess:

1. **Meaning:** facts, conditions, uncertainty, attribution, and behavioral requirements are preserved.
2. **Task:** the requested object, language, scope, and output form are respected.
3. **Expression:** the change helps the intended reader and follows the requested style.

Include an already-clear input to detect unnecessary rewriting. For prompt changes, distinguish improved wording from evidence that the downstream model behaves better. For comments, a range check does not establish that the new explanation is correct.

Report the models and languages checked, along with anything left untested. A successful example in one language does not validate another.

## Submit a focused change

Open a pull request at [yuanqimanong/yaya](https://github.com/yuanqimanong/yaya). Describe the problem, the resulting behavior and how you checked it. Note compatibility changes and known limitations.

Keep generated build outputs, downloaded research repositories, credentials and locally installed packs out of the change. Original, non-sensitive evaluation transcripts may go under `tests/results/`, with their method and limitations.

For a pack release, validate the directory, create a standalone flat ZIP and compute its SHA-256. Inspect the archive, then publish it with its matching checksum in the same official versioned release directory. Successful packaging alone does not justify changing the `quality` label.
