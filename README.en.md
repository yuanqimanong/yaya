# yaya · 牙牙学语

[简体中文](README.md) · [Installation](INSTALL.md) · [Contributing](CONTRIBUTING.md) · [Pack specification](docs/language-pack-spec.md)

Yaya is an editing Skill for your existing AI host. Use it to polish prose,
check engineering comments, improve prompts, or learn a sample's style.
Ask for a rewrite, a review, or a scoped file edit while preserving the meaning,
the author's voice and the task's constraints.

Simplified Chinese and English are included. Traditional Chinese, Japanese and
Korean are optional packs. Ordinary editing needs no extra service or model API.

## Install

### Ask your AI to install it

Send this to an AI coding tool that can access GitHub and local files:

```text
Read INSTALL.md at https://github.com/yuanqimanong/yaya and install Yaya using this tool's skill-directory rules.
Install the complete core/yaya directory for English and Simplified Chinese; skip optional language packs for now.
If Yaya is already installed, back it up outside skill discovery paths and preserve local customizations.
Report the actual path and version, then try a short edit to check that Yaya can be invoked.
```

In Codex installations that provide `$skill-installer`, you can also ask:

```text
$skill-installer Install Yaya from https://github.com/yuanqimanong/yaya/tree/main/core/yaya.
```

If the installer reports an existing directory, follow [update and rollback](INSTALL.md#4-update-remove-or-roll-back). The AI needs access to the repository and permission to write the target directory. Reading `SKILL.md` can test the guidance; it does not verify installation or automatic discovery.

### Install from source

The current core is **0.2.1**, with no public Release download yet. Clone the source:

```text
git clone https://github.com/yuanqimanong/yaya.git
cd yaya
```

Copy the complete `core/yaya/` folder into your host's Skill directory. Common Codex locations are:

| Scope | Destination |
| --- | --- |
| Current user | `~/.agents/skills/yaya/`, or `%USERPROFILE%\.agents\skills\yaya\` on Windows |
| One project | `PROJECT_ROOT/.agents/skills/yaya/` |

These paths follow the [official OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills), checked on 2026-10-21. Other compatible hosts use their own directory rules.

For a first Windows user installation, run from the repository root:

```powershell
$skillTarget = Join-Path $env:USERPROFILE '.agents\skills\yaya'
if (Test-Path -LiteralPath $skillTarget) { throw 'Yaya already exists; back it up and follow INSTALL.md to update.' }
New-Item -ItemType Directory -Path (Split-Path $skillTarget -Parent) -Force | Out-Null
Copy-Item -LiteralPath '.\core\yaya' -Destination $skillTarget -Recurse
```

The destination should contain `yaya/SKILL.md`, `references/`, `scripts/` and `languages/`. Optional packs are installed separately below. Codex normally discovers new skills automatically; restart if Yaya does not appear.

## Use it directly

Make a request by name, use `$yaya` explicitly, or type `$` and select Yaya in Codex.

- “$yaya Humanize this article. Keep the writer's voice and all substantive detail.”
- “Use Yaya to review this passage. Explain the issues without rewriting.”
- “Use Yaya to polish this financial report in plain English. Keep its figures and risk qualifications.”
- “Use Yaya to improve only the ordinary comments in this Python file. Preserve code, docstrings and directives.”
- “Use Yaya to check this technical explanation against the supplied configuration and API samples.”
- “Use Yaya to simplify this prompt; preserve variables, output formats and every constraint.”
- “Use Yaya to make this prompt ask for answers that beginners can understand.”
- “Use Yaya to learn this sample's style. Give me reusable instructions and an example.”
- “Use Yaya to polish this note in Hong Kong Traditional Chinese; keep its regional wording.”
- “Use Yaya to assess whether this is AI-written. Give evidence and uncertainty without rewriting.”

| Task | What Yaya does |
| --- | --- |
| Humanizing and review | Finds empty framing, promotional language, translation artifacts and repetitive wording, then judges them in context. |
| Prose and file editing | Adapts writing to its purpose, audience and style while preserving facts, quantities and uncertainty. |
| Code comments | Uses the code to clarify comments while preserving the program and tooling directives. |
| Engineering fact checking | Traces relevant configuration, environment and API evidence; preserves relationships and uncertainty without silently fixing business code. |
| Is this AI? | Assesses provenance and writing signals with a tentative AI/human leaning or an indeterminate result; text signals do not authenticate origin. |
| Prompt editing | Organizes wording and structure while preserving variables, output formats and execution requirements. Specify when you also want to change the downstream answer style. |
| Learning a style | Produces reusable style instructions and an example. Ask explicitly if you want them saved. |

Ask for a rewrite to receive revised text, a review to receive findings, or a file edit to change the specified scope. Clear, accurate text may stay unchanged. Specify the audience and purpose when changing tone or structure; name docstrings, runtime messages or schema metadata explicitly when those are included.

Learning a sample's style does not transfer its author's identity, experiences or opinions, and does not train a model. “Is this AI?” assesses writing signals and provenance material. Text alone cannot reliably distinguish human, generated and mixed-origin writing, and no calibrated accuracy or probability is claimed. See [authorship assessment](core/yaya/references/authorship.md).

## Try and develop

For a trial without installation, ask your AI host to read the local [SKILL.md](core/yaya/SKILL.md), then give it an editing request. See [INSTALL.md](INSTALL.md) for full installation, updates and rollback.

Test and build from the repository root:

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
python core/yaya/scripts/packs.py resolve --language zh-Hans
```

The build produces a core ZIP, three language ZIPs, `catalog.json` and
`SHA256SUMS` under `dist/`. Cloning obtains all language source files; installation
copies only the core and selected packs.

## Rewrite examples

Before:

> In today's fast-paced world, our groundbreaking update empowers teams to export shared notes as CSV. The feature is currently limited to trial accounts.

After:

> Teams can now export shared notes as CSV. The feature is currently limited to trial accounts.

Chinese before:

> 在不断变化的行业环境中，新版本以创新为驱动，为用户开启全新篇章。它支持导出 CSV，目前仅向试用账户开放。

After:

> 新版本支持导出 CSV，目前仅向试用账户开放。

These are original examples. Actual edits also need a check of claims,
attribution, conditions and uncertainty, such as “unverified,” “expected” and
“may.” Humanizing is an editing task, not a test of whether a person or AI wrote
the input.

## Small core, optional language data

| Language | Included by default | Build artifact |
| --- | --- | --- |
| Simplified Chinese `zh-Hans`, English `en` | Yes | `yaya-core-0.2.1.zip` |
| Traditional Chinese `zh-Hant` | No | `yaya-lang-zh-Hant-0.2.0.zip` |
| Japanese `ja` | No | `yaya-lang-ja-0.2.0.zip` |
| Korean `ko` | No | `yaya-lang-ko-0.2.0.zip` |

Packs contain guides and examples, loaded for the task's language once installed.
No separate enable setting is needed. Optional packs live outside the core, so a
core update does not overwrite them. If a pack is missing, the AI may attempt an
edit while noting that dedicated guidance was unavailable; it will not download
anything automatically.

Specify a locale when it matters; otherwise, Yaya keeps the input's conventions.
All five packs are **experimental**, pending a full quality review by native
editors.

Optional `PATTERNS.md` supplies language-specific humanizing examples. Packs are
text data and follow one current specification: `format_version: 1` with
`core_major: 0`. Adding a language needs no routing change; the local detector's
language support is defined separately.

## Optional local checks

From an installed `yaya/` directory:

```text
python scripts/detect_tells.py draft.md --language en
python scripts/check_rewrite.py before.md after.md
python scripts/check_comments.py before.py after.py
python scripts/check_docstrings.py before.py after.py --allow approved-docstrings.json
```

| Tool | What it checks |
| --- | --- |
| `detect_tells.py` | A small set of wording candidates in `en` and `zh-Hans`, with locations and reasons. Findings need contextual review; no AI probability is produced. |
| `check_rewrite.py` | Supported Markdown fragments, link destinations, placeholders, numbers and recognized units. Use `--protect-quotes` for supported paired quotations and `--protect-literal` for other exact text. |
| `check_comments.py` | Changes to ordinary Python `.py` / `.pyi` `#` comments, protecting code, strings, line structure and recognized directives. Adding, deleting or moving comment lines is unsupported. |
| `check_docstrings.py` | Exact grants for existing Python docstring nodes, preserving other code, strings and recognized examples. |
| `edit_evidence.py` | Task-start working-tree snapshots, a separate Git baseline, content-bound check records and explicit status accounting. |

Checkers do not write source files; the evidence helper writes snapshots and reports only to the selected directory. The first two accept UTF-8 inputs of up to 2 MiB each.
After a passing check, review the meaning: quantities can still refer to different
objects, and conditions, negation or attribution can change. The number check
compares numbers and recognized units in unprotected prose, including their
occurrence counts. It cannot establish ownership and may miss changes to unlisted
units.

Since 0.2.1, `--allow` takes an exact file/difference-bound JSON grant; broad category bypasses are rejected. Docstring edits change `__doc__`; AST checks establish mechanical scope only. See [validation](core/yaya/references/validation.md) for grants, Windows encoding boundaries and batch evidence. Ordinary polishing still returns the result directly.

“Is this AI?” uses the existing host model; `detect_tells.py` only scans wording candidates. Their results are not interchangeable.

The Markdown scanner covers a limited subset. It reports recognized unsupported
constructs such as indented blocks, fences inside lists, footnotes, multiline
links and raw HTML blocks. It is not a complete parser and cannot identify every
out-of-scope structure. Read the JSON `limitations` alongside the result. Python
source must parse with the current interpreter; other programming languages need a
suitable host parser or manual review.

Helpers require **Python 3.10+** and use only its standard library. Binary document
reading and layout handling use the host's existing tools.

## Contribute your language

Start from the [template](templates/language-pack/README.md) with `pack.json`,
`GUIDE.md`, `examples.md` and `LICENSE`; add `PATTERNS.md` when useful. Include
examples to improve and examples to preserve, validate the pack, then submit it.
New languages use the same loading and installation flow.

See the [pack specification](docs/language-pack-spec.md) for identifiers, versions,
file formats and review requirements. The `fr` template is a French authoring
example, not a released supported pack.

See [installation](INSTALL.md) for updates and rollback,
[the 0.2 upgrade](docs/upgrade-0.2.md) for version changes,
[design](docs/design.md) for the architecture, and
[validation](tests/README.md) for evidence and limits.

[MIT License](LICENSE)
