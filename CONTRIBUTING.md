# Contributing to Yaya

Start from a concrete editing failure, language need or helper bug, and show how your change fixes it. Keep ordinary editing simple.

## Choose the right place

- `core/yaya/SKILL.md`: discovery, shared editing boundaries and task selection.
- `core/yaya/catalog.json`: command contracts, options and the domain inventory. Help and
  task planning read the same data through `scripts/yaya.py`.
- `core/yaya/references/`: guidance for text, comments, prompts, style learning and language packs.
- `core/yaya/languages/`: the bundled `zh-Hans` and `en` packs.
- `language-packs/`: the optional `zh-Hant-TW`, `zh-Hant-HK`, `ja`, `ko`, `fr`, `es`, `pt-BR`, `ru` and `ar` packs.
- `core/yaya/scripts/`: local helpers, using only the Python standard library.
- `tests/`: unit tests for the helpers and the release build. File operations run in temporary directories.

Keep the [usage manual](docs/usage.md) and both READMEs consistent with the catalog.
A new command needs one bounded action, its permitted options and its delivery;
test rejected combinations as well as successful routing. A domain profile needs
concrete coverage, exclusions, protected relationships and the reasons behind its
sources. Keep profiles experimental until stronger evidence justifies a documented
change. A source citation, a passing parser test or an uncalibrated model judgment
is not professional certification. Update the release build and relocation checks
when adding runtime resources. Report the checks you ran and their results
separately from checks you only plan.

Language packs follow one [specification](docs/language-pack-spec.md): `format_version: 1` with `core_major: 1`, matching the core's major version. They may include `PATTERNS.md` for language-specific humanizing guidance. Every current pack is `experimental`.

For a new language, copy the files from the [language-pack template](templates/language-pack/README.md) into a new directory and replace its bracketed instructions. The template's README stays out of the pack and its ZIP.

## Before changing a rule

Record the request, the source material, the current failure and what a correct edit must preserve. Before adding instructions, compare the current guidance with a plain editing request on the same model.

Make the smallest correction that fixes the case. Use a clear principle and a representative example; a list of forbidden words rarely captures context. Put task-specific guidance in its reference file. Add an external service, extra model call or installation step only when the feature needs it.

For a humanizing rule, show when it applies, what it improves and a counterexample to leave alone. Machine-detectable patterns belong in `core/yaya/scripts/tell_rules.json`; language packs cannot supply executable rules or scripts. Detection changes need false-positive cases and protected-content checks. Editing evaluations must also check conditions, attribution and relationships that token comparisons cannot establish.

Wording candidates do not identify an author, and finding none does not show that a text is human-written. The local detector accepts only `en` and `zh-Hans`; adding a language pack or `PATTERNS.md` does not extend it.

Write original instructions and examples. Check the license and attribution before reusing another project's text or code. Keep personal data, private conversations and material that cannot be redistributed out of contributions.

## Language contributions

Include examples of the language's regional and register choices. Traditional Chinese needs more than script conversion: Taiwan and Hong Kong differ in vocabulary, character forms and written Cantonese, so they have separate packs. Japanese and Korean need attention to politeness levels; right-to-left languages need care with embedded code and numbers. Keep a requested locale even when a broader pack supplies the guidance, and let domain and audience guide terminology.

Include both useful edits and passages to leave unchanged. Check meaning, natural expression and language-specific boundaries. Every fact in the output must come from the input: inventing a metric to sound concrete is a failure.

Use `quality: experimental` until a documented review justifies `reviewed`. For `reviewed`, add `REVIEW.md` recording an actual human language review and evaluation: scope, reviewer role, date, cases, model and settings where applicable, observed failures and limitations. A schema check, a model's self-score or a lower word count is not an editorial evaluation.

The validator only checks that the review file exists and is not empty. Contributors must verify the evidence inside it.

## Check the change

From the repository root:

```text
python -m unittest discover -s tests -v
python core/yaya/scripts/packs.py validate core/yaya/languages/zh-Hans
python core/yaya/scripts/packs.py validate language-packs/ja
```

Validate the pack your change touches. For helpers, test failures as well as success: unsupported input, incompatible metadata, archive boundaries, checksum mismatches and preservation of existing data where they apply. Test behavior, not a particular heading or the shape of the implementation.

For editing guidance, use realistic requests in fresh model contexts. Keep the complete source, request and output, and assess:

1. **Meaning:** facts, conditions, uncertainty, attribution and behavioral requirements are preserved.
2. **Task:** the requested object, language, scope and output form are respected.
3. **Expression:** the change helps the intended reader and follows the requested style.

Include an input that is already clear, to catch unnecessary rewriting. For prompt changes, distinguish better wording from evidence that the downstream model behaves better. For comments, a range check does not show that the new explanation is correct.

Report the models and languages you checked and anything left untested. A good result in one language does not validate another.

## Submit a focused change

Open a pull request at [yuanqimanong/yaya](https://github.com/yuanqimanong/yaya). Describe the problem, the resulting behavior and how you checked it. Note compatibility changes and known limitations.

Keep build outputs, downloaded repositories, credentials, locally installed packs and model transcripts out of the change. Summarize evaluation results in the pull request instead.

For a pack release, validate the directory, build a standalone flat ZIP and compute its SHA-256. Inspect the archive, then publish it with its checksum in the same official versioned release directory. Packaging alone does not justify changing the `quality` label.
