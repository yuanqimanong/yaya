# Install and update Yaya

Install the core Skill for Simplified Chinese and English, then add any other
languages you need. Yaya works through your existing AI host and needs no separate
account, model key or background process. The optional Python helpers require
Python 3.10+ and use only its standard library.

You can ask your AI:

> 阅读 https://github.com/yuanqimanong/yaya 的 INSTALL.md，安装默认中英核心。

In Codex installations that provide the bundled installer, you can ask:

```text
$skill-installer Install Yaya from https://github.com/yuanqimanong/yaya/tree/main/core/yaya.
```

If the destination already exists, preserve it and follow the staged update
procedure below; a fresh-install command is not an update command.

> 按 INSTALL.md 给已安装的 yaya 增加日语支持，先构建语言包并校验哈希。

## 1. Obtain the smallest artifact

**Core version 0.4.0 is available from source; there is no public Release download yet.**
Clone the [repository](https://github.com/yuanqimanong/yaya), then build from its root:

```text
git clone https://github.com/yuanqimanong/yaya.git
cd yaya
python scripts/build_release.py
```

The build writes `dist/yaya-core-0.4.0.zip`, three optional language archives,
`catalog.json` and `SHA256SUMS`. Install only the core unless you need another
language. Cloning downloads all language source files, but does not install them.

The three optional files are `yaya-lang-zh-Hant-VERSION.zip`,
`yaya-lang-ja-VERSION.zip`, and `yaya-lang-ko-VERSION.zip`. They are data archives,
installed with `packs.py`, rather than standalone Skills.

For a future published version, obtain `catalog.json` and the selected archives
from the same trusted, versioned Release. The catalog records relative filenames,
versions, SHA-256 hashes and sizes. A core-only installation needs just
`yaya-core-VERSION.zip` and the catalog.

## 2. Install the core

Check the core ZIP against the catalog SHA-256 before extracting. Inspect members:
they must be regular files under the single `yaya/` directory, with no absolute
paths, `..`, links, or executable install hooks. Extract into a temporary directory,
then copy that `yaya/` directory into the host's documented Skill directory.

For Codex, choose one location:

| Scope | Install directory |
| --- | --- |
| Personal | `HOME/.agents/skills/yaya/` |
| One project | `PROJECT_ROOT/.agents/skills/yaya/` |

These paths follow
[OpenAI's official skill documentation](https://learn.chatgpt.com/docs/build-skills)
(checked 2026-10-21). For another Agent Skills host, use its current documented
location for the same `yaya/` folder. Keep one installation per intended scope to
avoid duplicate discovery.

`HOME` means your user home directory and `PROJECT_ROOT` means the chosen project's
root; replace these placeholders with actual paths. Quote command arguments when
their paths contain spaces.

You can also copy `core/yaya/` directly from a source checkout, omitting
`__pycache__` and development files. Copy the complete runtime directory so that
relative references and helpers work. Use ordinary directories for language data:
the helper rejects links and Windows reparse points.

If Yaya is already installed, keep a complete backup **outside all host Skill
discovery directories**, prepare the replacement separately, and then swap it in.
Keep the replacement separate from the old tree and from unrelated files. Use the
host's normal permission flow for writing outside the current workspace.

Verify `yaya/SKILL.md`, `yaya/references/`, `yaya/scripts/`, and the bundled `en` and
`zh-Hans` directories. Ask the host to list or select Yaya and perform a short edit.
Versions 0.3 and later also require `catalog.json`, `scripts/yaya.py`, and the five
guides in `references/domains/`; 0.4 adds `references/check.md`. In chat, run
`$yaya --help` and `$yaya domains`. From the installed Skill directory, run
`python scripts/yaya.py --version --json` to verify the runtime version, then
`python scripts/yaya.py check --help` to inspect the comparison command.
Newer checkouts also include `scripts/doctor.py` and `references/scan.md`. Run
`python scripts/yaya.py doctor --json` from the installed directory: `ready` means
the local structure and Python syntax checks passed; `degraded` exits 1 and names
the failed checks. It does not repair files, certify editing quality or establish
host discovery. Replace a broken runtime from the staged verified copy, then rerun.

Task commands print help or a host task plan; `doctor` performs local diagnostics.
The helper does not call a model or edit user files,
and installing the Skill does not put a `yaya` executable on your shell's PATH.
If Yaya does not appear, follow the host's reload/restart procedure. Reading a
source file directly can test editing, but does not verify automatic discovery.
See [scoped workflows](docs/workflows.md) for reusable style cards, selected
verification sources, literal scans and executed preservation checks.

## 3. Add a requested language

Run from the **installed Yaya directory**. Replace the uppercase arguments below
with actual local paths and the digest from the trusted catalog:

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256
python scripts/packs.py resolve --language ja
python scripts/packs.py list
```

Packs are installed outside the core, in `HOME/.yaya/language-packs/ID` by default.
A verified compatible pack is used when its language is selected; no separate
enable setting is needed.

For a project-only installation:

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256 --project PROJECT_ROOT
python scripts/packs.py resolve --language ja --project PROJECT_ROOT
```

`--project` writes under `PROJECT_ROOT/.yaya/`. `--data-dir DATA_DIRECTORY` instead
selects another user data location, useful for isolated tests. Pass the same option
on subsequent resolutions and mutations. Mutation commands reject using both
options together. The helper never discovers a project root by scanning parents.

Before replacing installed content, the helper checks the digest, file layout,
size limits, UTF-8 encoding, metadata and core compatibility. Verify the source of
the catalog as well: a matching checksum confirms that the archive matches that
value, but cannot authenticate its publisher.

The resolver returns JSON:

| Status | Meaning |
| --- | --- |
| `ready` with `available: true` | The returned paths can be used. |
| `missing` | No matching installed candidate was found. |
| `invalid` or `incompatible` | The selected pack blocks resolution until repaired or replaced; a broken higher-priority override is not skipped. |

Resolution leaves installed files unchanged. The AI can still attempt an edit
while noting that dedicated guidance was unavailable. It does not download packs
automatically.

## 4. Update, remove, or roll back

For a language update, obtain the new archive and matching trusted hash:

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256 --replace
```

To remove Japanese or restore its latest backup, run the operation you need:

```text
python scripts/packs.py remove ja
python scripts/packs.py rollback ja
```

These are separate operations. Identical installs remain unchanged; replacing
different content requires `--replace`. Replacement and
removal retain the old pack under `DATA_DIRECTORY/backups/ID/`; rollback validates
and restores the latest backup and retains the displaced installed pack. An invalid
or incompatible latest backup causes an error; it does not select an older backup.
Use the same target option as the installation, and check the returned status and
backup path. Backups remain until you choose to remove them.

Run one install, remove or rollback operation at a time in a data directory. If a
filesystem error interrupts a swap and automatic restoration fails, keep the
reported backup. Resolve the filesystem error before restoring it.

To update the core, repeat the staged core replacement above, retaining its prior
directory outside discovery paths. Restore that backup to roll back. Packs and
saved styles remain in `.yaya/`, separate from core updates. A future incompatible
core major version requires compatible packs or a core rollback. Check how a
third-party installer handles updates before using it with Release ZIPs.

When uninstalling, remove the selected core directory. Keep `.yaya/` unless you
also intend to remove its packs, styles and recovery data; other host
installations may use them.

## Saved styles and troubleshooting

Style extraction applies to the current task by default. When asked to save,
Yaya writes a style file to your selected location, project `.yaya/styles/` for
project scope, or otherwise `HOME/.yaya/styles/`. Select the saved style explicitly
when you want to reuse it.

If Python is unavailable, the host can still read bundled editorial guidance.
Install Python through your normal environment process to use pack management and
local checks. Report checks that could not run, and resolve archive, checksum,
path or compatibility errors before proceeding.

The complete package contract and contributor commands are in
[language-pack-spec.md](docs/language-pack-spec.md).

## Current language-pack format

Core `0.2.x`, `0.3.x` and `0.4.x` use one current pack specification:
`format_version: 1` with `core_major: 0`, including optional `PATTERNS.md` for
humanizing guidance. Without that file, the host uses `GUIDE.md`. Packs are plain
text and contain no executable rules.
There is no migration between unpublished draft formats.

Content updates retain backups and support rollback as described above. After a
core rollback, use `resolve` to check pack compatibility with the restored core.
