# Yaya language-pack specification

Language packs provide local editorial guidance and examples for Yaya. They contain only data and must follow the user's request, the core editing contract, and tool permissions.

This specification defines the supported metadata, files and resolution rules. Validation checks a restricted subset of BCP 47 and SPDX syntax without consulting their registries.

The machine-readable [JSON Schema](../schemas/language-pack.schema.json) covers the metadata shape. The local validator additionally checks file contents, duplicate JSON keys and variant subtags, canonical casing, review evidence presence, and compatibility. References: [BCP 47 / RFC 5646](https://www.rfc-editor.org/rfc/rfc5646), [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html), [JSON Schema 2020-12](https://json-schema.org/draft/2020-12), and [SPDX identifiers](https://spdx.org/licenses/).

## Directory and archive layout

A pack contains these UTF-8 text files at its root:

```text
pack.json
GUIDE.md
examples.md
LICENSE
REVIEW.md    # optional for experimental; required for reviewed
PATTERNS.md  # optional guidance for reducing formulaic wording
```

Only the listed files are accepted. Do not include `SKILL.md`, scripts, or executable resources. Links may identify sources but do not authorize network access or execution.

A standalone pack ZIP has the same flat root layout, without an enclosing directory. Each file is limited to 512 KiB, total expanded content to 2 MiB, and the archive to 8 MiB. Use regular files and preserve the exact required filenames.

## Metadata

`pack.json` is a JSON object with exactly these required fields. Unknown fields are rejected.

```json
{
  "format_version": 1,
  "id": "ja",
  "version": "1.0.0",
  "core_major": 1,
  "name": "日本語",
  "license": "MIT",
  "quality": "experimental",
  "direction": "ltr"
}
```

| Field | Requirement |
| --- | --- |
| `format_version` | Integer `1`. |
| `id` | A canonical language tag in the restricted profile below. |
| `version` | Strict Semantic Versioning, such as `1.0.0` or `1.1.0-rc.1`; no `v` prefix. |
| `core_major` | Nonnegative integer matching the consuming core's major version. Yaya `1.0.0` has major `1`. |
| `name` | Nonempty display name, at most 100 characters, normally written in the pack's own language. |
| `license` | Syntax of a single SPDX identifier, such as `MIT` or `Apache-2.0`; no compound expression. Registry membership is not verified. |
| `quality` | `experimental` or `reviewed`. |
| `direction` | `ltr` or `rtl`. This declares writing direction; it does not ensure every host renders it correctly. |

Include the full applicable license text in `LICENSE` and satisfy its attribution requirements.

Pack versions are independent of the core's minor and patch versions. `core_major` declares compatibility; record the core versions actually tested in review evidence.

The data contract stays stable within a core major. An incompatible change must increment the pack format or the core major. Independent publishers may distribute a pack ZIP with a trusted checksum from any repository. There is no central language allowlist; the same validation, licensing and review rules apply.

### Compatibility

Core 1.x reads one format: `format_version: 1` with `core_major: 1`. `PATTERNS.md` is optional; a pack without it resolves with `patterns: null`, and its guide and examples remain usable.

Pack content can be updated independently. Use `--replace` and `rollback` so complete pack versions move together.

Unsupported format or core-major versions are reported as `incompatible`; invalid files and metadata are reported as `invalid`. Neither result silently selects a lower-priority pack.

### Restricted language-tag profile

The accepted structure is:

```text
language[-Script][-REGION][-variant...]
```

- `language`: two or three lowercase ASCII letters.
- Optional `Script`: four ASCII letters in title case, such as `Hans` or `Hant`.
- Optional `REGION`: two uppercase ASCII letters or three digits.
- Each optional variant: five to eight ASCII alphanumeric characters, or one digit followed by three ASCII alphanumeric characters.

Use canonical casing in pack metadata, including lowercase variant subtags. Examples within this profile include `en`, `en-GB`, `zh-Hans`, `zh-Hant-HK`, `pt-BR`, `es-419`, `sl-rozaj` and `de-1901`.

Extensions, private-use tags, grandfathered tags, and other BCP 47 forms are outside this profile. Validation checks the supported shape and casing; it does not look up whether every subtag is registered or semantically appropriate. The resolver can normalize request casing, but `pack.json` must already use a canonical ID.

## Editorial content and quality

`GUIDE.md` describes register, natural phrasing, punctuation, terminology, and language-specific distinctions that need protection. `examples.md` supplies input/output examples and passages that should stay unchanged. Focus on the language's needs without repeating the core skill, and state the locale each preference applies to.

Optional `PATTERNS.md` guides review and reduction of formulaic wording. Include a trigger, exceptions, a useful revision, and a case to preserve. Load it for relevant humanize or detect requests. Preserve local usage and author voice; a word or punctuation mark alone does not establish AI authorship.

Pattern guidance is UTF-8 Markdown data. It does not register executable detector rules, regular expressions, or scripts. Core tools only use their bundled rules; adding `PATTERNS.md` does not claim that the deterministic detector supports that language.

Use `experimental` until human review is complete. Claiming `reviewed` requires a nonempty `REVIEW.md` with the language/locale, task coverage, date, reviewer role, cases, relevant model settings, outcomes, and limitations. File validation checks that evidence is present; it cannot verify its truth or establish quality beyond its scope.

When review evidence claims humanize coverage, include `PATTERNS.md` and the cases and native-editor findings that support that claim. A reviewed pack without `PATTERNS.md` can cover its guide and examples; it does not imply reviewed humanize patterns.

All current packs are `experimental`: the bundled `zh-Hans` and `en`, and the optional `zh-Hant-TW`, `zh-Hant-HK`, `ja`, `ko`, `fr`, `es`, `pt-BR`, `ru` and `ar`. The [template](../templates/language-pack/README.md) uses the ID `und` and is never built or published.

## Resolution and fallback

The core bundles `zh-Hans` and `en`. Optional installed packs live under:

```text
PROJECT_ROOT/.yaya/language-packs/ID
HOME/.yaya/language-packs/ID
```

Location priority is **explicit project, user, bundled**. Within each location, try the most specific candidate before broader parent candidates. Location priority comes first: a project `fr` pack overrides a user `fr-CA` pack for an `fr-CA` request.

Use a project directory only when the user or calling host explicitly provides its root. Do not search parent directories. `--data-dir` replaces `HOME/.yaya`; it names the data directory itself, not its `language-packs` child.

Candidates come from removing subtags from the right, with these additions, while the requested locale is retained:

- `zh-CN` and `zh-SG`: insert the `Hans` script, for example `zh-CN`, `zh-Hans-CN`, `zh-Hans`, `zh`.
- `zh-TW`, `zh-HK` and `zh-MO`: insert the `Hant` script.
- `zh-Hant-MO`: try `zh-Hant-HK` next, following the CLDR parent locale.
- Bare `zh` does not guess a script, and `zh-Hant` does not guess a region: with only the regional packs installed, `zh-Hant` resolves as `missing`. The Taiwan and Hong Kong packs never stand in for each other.

So `es-MX` resolves to `es`, while `pt-PT` does not resolve to `pt-BR`.

A broader match supplies guidance without changing the user's requested output locale. A missing or incompatible pack allows a generic model attempt with a disclosed limitation; it must not be described as language-specific validation. Pack discovery and fallback do not download anything.

## Local helper interface

Run these commands from the installed Yaya directory. All paths are local.

```text
python scripts/packs.py validate PACK_DIRECTORY
python scripts/packs.py resolve --language ja
python scripts/packs.py resolve --language ja --project PROJECT_ROOT
python scripts/packs.py resolve --language ja --data-dir DATA_DIRECTORY
python scripts/packs.py list --project PROJECT_ROOT
python scripts/packs.py list --data-dir DATA_DIRECTORY
```

Read the JSON response to confirm the result. The resolver exposes `status`, `resolved`, `available`, `guide`, `examples`, and `patterns`; use the returned paths only for a usable pack. `patterns` is an absolute path or `null`. Ordinary editing uses the guide. Humanize or detect work uses patterns, adding the guide when locale or register needs clarification or patterns are absent. Load examples only when useful. A ready result also includes `format_version`.

Install, remove, and roll back use an explicit target in these examples:

```text
python scripts/packs.py install ARCHIVE --data-dir DATA_DIRECTORY --sha256 EXPECTED_SHA256
python scripts/packs.py install ARCHIVE --project PROJECT_ROOT --sha256 EXPECTED_SHA256 --replace
python scripts/packs.py remove ja --data-dir DATA_DIRECTORY
python scripts/packs.py rollback ja --data-dir DATA_DIRECTORY
```

Each mutation also accepts `--project PROJECT_ROOT` instead of `--data-dir`; those target options are mutually exclusive. `--replace` is the explicit choice to replace an existing installed pack.

Installation requires a SHA-256 digest. Obtain it with the archive from the publisher's trusted, versioned distribution. For a local build, use the generated checksum and record the source revision. Yaya has no public Release yet. A matching digest confirms the file against that value; it does not establish publisher trust or editorial quality.

A successful replacement or removal retains the previous pack as a backup. `rollback ID` validates and restores the latest backup in the selected target. If that backup is invalid or incompatible, rollback reports an error and leaves older backups untouched. Manage backup retention yourself; these files recover language packs only.
