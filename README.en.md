# Yaya · 牙牙学语

[简体中文](README.md) · [Detailed usage (Chinese)](docs/usage.md) · [Install and update](INSTALL.md)

Yaya is a writing Skill for AI assistants. It humanizes and polishes prose, checks claims against supplied evidence, edits code comments and prompts, learns writing styles, and assesses AI-writing signals.

Your current AI assistant does the editing. Local Python tools only plan commands, scan wording and check protected content, so you need no extra model account, API key or background service. The current version is **1.0.0**, available from `main`; no GitHub Release has been published yet.

## Start

Ask a host that supports Skill installation:

> Read https://github.com/yuanqimanong/yaya/blob/main/INSTALL.md and install the default Chinese/English core from main.

Then use these commands in chat:

```text
$yaya --help
$yaya human --domain tech --file README.md
$yaya origin -- Paste the text to assess here.
```

The second command returns a revised draft. Add `--write` to edit the file instead. Plain requests work too: “Use Yaya to humanize this README for software developers and edit the file.”

`$yaya` and `yaya` work in chat only; installation adds no shell command. For help in a terminal, run:

```text
python core/yaya/scripts/yaya.py --help
```

Run this from the repository root. From an installed `yaya/` directory, drop `core/yaya/`. Input files must be readable by the host. The helper prints Chinese help or a JSON task plan, `doctor` runs local diagnostics itself, and the host carries out every other task. See [invocation and file rules](docs/usage.md#start).

## Capabilities

| Need | Command | Result and detailed usage |
| --- | --- | --- |
| Humanize writing | `human` | Rewrite formulaic, repetitive or needlessly defensive passages; [usage](docs/usage.md#human) |
| Polish prose | `polish` | Improve expression and structure for the reader; [usage](docs/usage.md#polish) |
| Review without editing | `review` | Quote issues, explain them and suggest changes; [usage](docs/usage.md#review) |
| Verify claims | `verify` | Report evidence and unresolved claims; [usage](docs/usage.md#verify) |
| Edit code comments | `comment` | Ground ordinary comments in nearby code; select docstrings explicitly; [usage](docs/usage.md#comment) |
| Edit prompts | `prompt` | Revise wording or downstream answer style; [usage](docs/usage.md#prompt) |
| Learn a style | `style` | Extract a reusable style card and optionally save it; [usage](docs/usage.md#style) |
| Assess AI-writing signals | `origin` | Give a tentative origin assessment and supporting passages; [usage](docs/usage.md#origin) |
| Scan wording locally | `scan` | Locate candidates using finite English/Chinese literal rules; [usage](docs/usage.md#scan) |
| Compare drafts | `check` | Check protected content or Python ordinary-comment boundaries; [usage](docs/usage.md#check) |
| Diagnose installation | `doctor` | Check local runtime files, syntax and resources; [usage](docs/usage.md#doctor) |

Each command performs one task. Natural language can combine tasks: “Check the deployment guide against these sources, then polish the confirmed passages.” The [usage manual](docs/usage.md) lists every option, default, input and result, with examples. It is in Chinese; the [host command reference](core/yaya/references/commands.md) is in English.

## Is this text AI-written?

```text
$yaya origin --file article.md
$yaya origin --file article.md --file revision-history.md
$yaya help origin
```

The result is an **AI-generated leaning**, a **human-written leaning** or **indeterminate**, with quoted passages and reasons. The source stays unchanged. Drafts, revision history and generation records can add provenance evidence. Text alone usually cannot establish authorship, so Yaya gives no AI percentage. See [authorship assessment](core/yaya/references/authorship.md).

## Remove unnecessary defensive wording

```text
$yaya human --focus direct --domain tech --file draft.md
$yaya review --focus direct --file draft.md
```

`direct` handles only irrelevant contrasts, imagined objections and repeated qualifications. For example:

> Before: This isn't about redefining collaboration. The directory adds department filtering.
>
> After: The directory adds department filtering.

Conditions that affect use stay, such as “Retry only after a connection timeout, at most twice.” The guidance works from context and applies equally to text from GPT, Opus, DeepSeek, Doubao or any other source; there are no model-brand presets. See [humanizing guidance](core/yaya/references/humanize.md).

## Domains and languages

| Domain ID | Suitable material | Relationships to preserve |
| --- | --- | --- |
| `tech` | READMEs, APIs, operations, incidents, comments | Interfaces, prerequisites, defaults, effective settings and completion state |
| `finance` | Financial results, metrics, investor communication | Currency, period, metric basis, comparisons, forecasts and risk |
| `data` | Experiments, surveys, dashboards, analysis | Samples, denominators, windows, missing values, association and causation |
| `academic` | Abstracts, methods, results, discussion, reviews | Study design, attribution, evidence strength and limitations |
| `business` | Emails, updates, proposals, customer notices | Owners, dates, prices, approvals, delivery conditions and commitments |

```text
$yaya domains
$yaya domains finance
$yaya polish --domain finance --audience "general readers" --tone concise --file report.md
```

Domain, audience, tone and language are chosen separately. All five profiles are `experimental`; the [domain guidance](core/yaya/references/domains.md) explains their coverage and evidence limits.

The core bundles **Simplified Chinese `zh-Hans`** and **English `en`**. Install other languages as needed:

| Language | ID | Language | ID |
| --- | --- | --- | --- |
| Traditional Chinese (Taiwan) | `zh-Hant-TW` | Spanish | `es` |
| Traditional Chinese (Hong Kong) | `zh-Hant-HK` | Brazilian Portuguese | `pt-BR` |
| Japanese | `ja` | Russian | `ru` |
| Korean | `ko` | Arabic (right to left) | `ar` |
| French | `fr` | | |

Taiwan and Hong Kong differ in vocabulary, character forms and register, so each has its own pack and neither stands in for the other; `zh-MO` uses the Hong Kong pack. Every pack is experimental editorial guidance. The local `scan` rules cover only Simplified Chinese and English. See [language-pack installation](INSTALL.md#3-add-a-requested-language).

## Documentation

| Document | Contents |
| --- | --- |
| [Usage manual](docs/usage.md) | Every command and option, defaults, inputs, outputs and common errors (Chinese) |
| [Workflows](docs/workflows.md) | Technical verification, financial editing and style reuse (Chinese) |
| [Local tools](docs/local-tools.md) | Scans, checks, docstring grants, batch evidence and exit codes (Chinese) |
| [Install and update](INSTALL.md) | Core and pack installation, checks, updates, removal and rollback |
| [Design](docs/design.md) / [Contributing](CONTRIBUTING.md) | Architecture, extension and development checks |
| [Tests](tests/README.md) | Unit tests for the local scripts and release build (Chinese) |
| [Language-pack specification](docs/language-pack-spec.md) | Format, resolution and language contributions |

Run development checks from the repository root with Python 3.10+:

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
```

Builds go to `dist/`. Local tools use only the Python standard library. File edits keep a recoverable original or diff. A passing mechanical check does not settle meaning or readability; read the result as well.

[MIT License](LICENSE)
