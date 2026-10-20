# yaya · 牙牙学语

[简体中文](README.md) · [Installation](INSTALL.md) · [Contributing](CONTRIBUTING.md) · [Pack specification](docs/language-pack-spec.md)

Yaya is an editing Skill for your existing AI host. Use it to remove padding,
clarify prose, improve code comments and prompts, or learn a sample's style.
Ask for a rewrite or a review; edits should preserve the meaning, the author's
voice and the task's requirements.

Simplified Chinese and English are included. Traditional Chinese, Japanese and
Korean are optional packs. Ordinary editing needs no extra service or model API.

## Use it directly

- “Humanize this article. Keep the writer's voice and all substantive detail.”
- “Point out awkward or inflated passages first. Don't rewrite yet.”
- “Polish this financial report in plain English.”
- “Improve only the ordinary comments in this Python file.”
- “Remove inflated wording from this prompt; preserve every constraint.”
- “Make this prompt ask for answers that beginners can understand.”
- “Learn this sample's style and give me reusable instructions plus an example.”
- “Polish this note in Hong Kong Traditional Chinese; keep its regional wording.”

| Task | What Yaya does |
| --- | --- |
| Humanizing and review | Finds empty framing, promotional language, translation artifacts and repetitive wording, then judges them in context. |
| Prose and file editing | Adapts writing to its purpose, audience and style while preserving facts, quantities and uncertainty. |
| Code comments | Uses the code to clarify comments while preserving the program and tooling directives. |
| Prompt editing | Organizes wording and structure while preserving variables, output formats and execution requirements. Specify when you also want to change the downstream answer style. |
| Learning a style | Produces reusable style instructions and an example. Ask explicitly if you want them saved. |

Ask for a rewrite to receive revised text, a review to receive findings, or a file
edit to change the specified scope. Clear text may stay unchanged; a request to
change tone or structure still calls for that change. Learning a sample's style
does not transfer its author's identity, experiences or opinions, and does not
train a model.

## Try and develop

Get the source from [GitHub](https://github.com/yuanqimanong/yaya):

```text
git clone https://github.com/yuanqimanong/yaya.git
cd yaya
```

For a direct trial, ask your AI host to read [SKILL.md](core/yaya/SKILL.md), then
give it an editing request. For automatic discovery, install the complete
`core/yaya/` directory in your host's Skill location; see [INSTALL.md](INSTALL.md).

The current version is **0.2.0**. There is no public Release download yet. Test
and build from the repository root:

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
| Simplified Chinese `zh-Hans`, English `en` | Yes | `yaya-core-0.2.0.zip` |
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
```

| Tool | What it checks |
| --- | --- |
| `detect_tells.py` | A small set of wording candidates in `en` and `zh-Hans`, with locations and reasons. Findings need contextual review; no AI probability is produced. |
| `check_rewrite.py` | Supported Markdown fragments, link destinations, placeholders, numbers and recognized units. Use `--protect-quotes` for supported paired quotations and `--protect-literal` for other exact text. |
| `check_comments.py` | Changes to ordinary Python `.py` / `.pyi` `#` comments, protecting code, strings, line structure and recognized directives. Adding, deleting or moving comment lines is unsupported. |

All helpers are read-only. The first two accept UTF-8 inputs of up to 2 MiB each.
After a passing check, review the meaning: quantities can still refer to different
objects, and conditions, negation or attribution can change. The number check
compares numbers and recognized units in unprotected prose, including their
occurrence counts. It cannot establish ownership and may miss changes to unlisted
units.

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
