# Yaya · 牙牙学语

[简体中文](README.md) · [Detailed usage (Chinese)](docs/usage.md) · [Install and update](INSTALL.md)

Yaya is a writing Skill for AI assistants. It humanizes and polishes prose, checks claims against supplied evidence, edits code comments and prompts, learns writing styles, and assesses AI-writing signals.

Your current AI assistant does the editing. Local Python tools handle command planning, scans and preservation checks. No additional model account, API key or background service is required. Core **0.5.0** is available from `main`; no GitHub Release has been published yet.

## Start

Ask a host that supports Skill installation:

> Read https://github.com/yuanqimanong/yaya/blob/main/INSTALL.md and install the default Chinese/English core from main.

Then use these commands in chat:

```text
$yaya --help
$yaya human --domain tech --file README.md
$yaya origin -- Paste the text to assess here.
```

The second command returns a candidate. Add `--write` to edit the file. Natural-language requests work too: “Use Yaya to humanize this README for software developers and edit the file.”

`$yaya` and `yaya` select tasks in chat. Installation does not add a global shell command. For terminal help, run:

```text
python core/yaya/scripts/yaya.py --help
```

This path assumes the repository root. From an installed `yaya/` directory, omit `core/yaya/`. Input files must be accessible to the host. The helper prints Chinese help or a JSON task plan; `doctor` executes local diagnostics directly. The host executes the other tasks. See [invocation and file rules](docs/usage.md#start).

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

Each explicit command selects one task. Natural language can combine tasks: “Check the deployment guide against these sources, then polish the confirmed passages.” The [usage manual](docs/usage.md) lists every option, default, input and result, with examples. It is currently in Chinese; the [host command reference](core/yaya/references/commands.md) is in English.

## Is this text AI-written?

Use `origin`:

```text
$yaya origin --file article.md
$yaya origin --file article.md --file revision-history.md
$yaya help origin
```

The result gives an **AI-generated leaning**, **human-written leaning**, or **indeterminate** assessment, with quoted passages and reasons. It leaves the source unchanged. Drafts, revision history and generation records can help establish provenance. Text alone usually cannot establish authorship; Yaya does not invent an AI percentage. See [authorship assessment](core/yaya/references/authorship.md).

## Remove unnecessary defensive wording

```text
$yaya human --focus direct --domain tech --file draft.md
$yaya review --focus direct --file draft.md
```

`direct` focuses on irrelevant contrasts, imagined objections and repeated qualifications. For example:

> Before: This isn't about redefining collaboration. The directory adds department filtering.
>
> After: The directory adds department filtering.

Keep conditions that affect use, such as “Retry only after a connection timeout, at most twice.” The guidance uses context and applies to text from GPT, Opus, DeepSeek, Doubao and other sources. There are no model-brand presets. See [humanizing guidance](core/yaya/references/humanize.md).

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

Choose domain, audience, tone and language separately. All five profiles are `experimental`; [domain guidance](core/yaya/references/domains.md) explains coverage and evidence limits.

The core bundles **Simplified Chinese `zh-Hans` and English `en`**. Install **Traditional Chinese `zh-Hant`, Japanese `ja` and Korean `ko`** as needed. All five packs are experimental. The local `scan` rules currently cover only Simplified Chinese and English. See [language-pack installation](INSTALL.md#3-add-a-requested-language).

## Documentation

| Document | Contents |
| --- | --- |
| [Usage manual](docs/usage.md) | Every command and option, defaults, inputs, outputs and common errors (Chinese) |
| [Workflows](docs/workflows.md) | Technical verification, financial editing and style reuse (Chinese) |
| [Local tools](docs/local-tools.md) | Scans, checks, docstring grants, batch evidence and exit codes (Chinese) |
| [Install and update](INSTALL.md) | Core and pack installation, checks, updates, removal and rollback |
| [0.5 upgrade](docs/upgrade-0.5.md) | Current changes and compatibility (Chinese) |
| [Design](docs/design.md) / [Contributing](CONTRIBUTING.md) | Architecture, extension and development checks |
| [Tests and evaluations](tests/README.md) | Regression tests, writing evaluations and execution evidence |
| [Language-pack specification](docs/language-pack-spec.md) | Format, resolution and language contributions |

Run development checks from the repository root with Python 3.10+:

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
```

Builds go to `dist/`. Local tools use only the Python standard library. File edits retain a recoverable original or diff; review their meaning and usefulness alongside mechanical checks.

[MIT License](LICENSE)
