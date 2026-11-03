# Install and update Yaya

Install the core Skill for Simplified Chinese and English, then add any other
languages you need. Yaya runs inside your existing AI host and needs no separate
account, model key or background process. The optional Python helpers need
Python 3.10+ and use only its standard library.

You can ask your AI:

> 阅读 https://github.com/yuanqimanong/yaya/blob/main/INSTALL.md，从 main 分支安装默认中英核心。

In Codex installations that provide the bundled installer, you can ask:

```text
$skill-installer Install Yaya from https://github.com/yuanqimanong/yaya/tree/main/core/yaya.
```

If the destination already exists, keep it and follow the staged update
procedure below; a fresh-install command does not update an installation.

> 按 INSTALL.md 给已安装的 yaya 增加日语支持，先构建语言包并校验哈希。

## 1. Obtain the smallest artifact

**Core 1.0.0 is available from `main`; there is no public Release download yet.**
Check `core/yaya/version.json` in the checkout you install.
Clone the [repository](https://github.com/yuanqimanong/yaya), then build from its root:

```text
git clone --branch main --single-branch https://github.com/yuanqimanong/yaya.git
cd yaya
python scripts/build_release.py
```

The build writes `dist/yaya-core-1.0.0.zip`, nine optional language archives,
`catalog.json` and `SHA256SUMS`. Install only the core unless you need another
language. Cloning downloads every language's source files but installs none of them.

The optional archives are named `yaya-lang-ID-VERSION.zip`, one for each of
`zh-Hant-TW`, `zh-Hant-HK`, `ja`, `ko`, `fr`, `es`, `pt-BR`, `ru` and `ar`.
Install these data archives with `packs.py`.

Once a version is published, take `catalog.json` and the archives you need from the
same trusted, versioned Release. The catalog records each file's relative name,
version, SHA-256 hash and size. A core-only installation needs just
`yaya-core-VERSION.zip` and the catalog.

## 2. Install the core

Check the core ZIP against the catalog SHA-256 before extracting it. Inspect its
members: they must be regular files under a single `yaya/` directory, with no
absolute paths, `..`, links or executable install hooks. Extract into a temporary
directory, then copy that `yaya/` directory into the host's documented Skill directory.

For Codex, choose one location:

| Scope | Install directory |
| --- | --- |
| Personal | `HOME/.agents/skills/yaya/` |
| One project | `PROJECT_ROOT/.agents/skills/yaya/` |

These paths follow
[OpenAI's official skill documentation](https://learn.chatgpt.com/docs/build-skills)
(checked 2026-10-21). For another Agent Skills host, use its documented location
for the same `yaya/` folder. Keep one installation per scope so the host does not
discover Yaya twice.

`HOME` is your user home directory and `PROJECT_ROOT` is the chosen project's root;
replace both with actual paths. Quote arguments whose paths contain spaces.

You can also copy `core/yaya/` straight from a source checkout, leaving out
`__pycache__` and development files. Copy the whole runtime directory so relative
references and helpers keep working. Use ordinary directories for language data:
the helper rejects links and Windows reparse points.

If Yaya is already installed, back up the complete directory **outside every host
Skill discovery directory**, prepare the replacement separately, then swap it in.
Keep the replacement apart from the old tree and from unrelated files. Use the
host's normal permission flow for writing outside the current workspace.

Check that `yaya/SKILL.md`, `yaya/catalog.json`, `yaya/references/` (including the
five guides in `references/domains/`), `yaya/scripts/` and the bundled `en` and
`zh-Hans` directories are present. Ask the host to list or select Yaya and make a
short edit. In chat, run `$yaya --help` and `$yaya domains`. From the installed
Skill directory, run `python scripts/yaya.py --version --json` to confirm the
runtime version and `python scripts/yaya.py check --help` to inspect the comparison
command, then `python scripts/yaya.py doctor --json`: `ready` means the
local structure and Python syntax checks passed; `degraded` exits 1 and names the
failed checks. `doctor` does not repair files, certify editing quality or confirm
that the host discovers the Skill. Replace a broken runtime from the staged,
verified copy and run it again.

Task commands print help or a host task plan; `doctor` runs local diagnostics.
The helper does not call a model or edit user files, and installing the Skill puts
no `yaya` executable on your shell's PATH. If Yaya does not appear, follow the
host's reload or restart procedure. Reading a source file directly can test
editing but does not test automatic discovery.
See the [usage manual](docs/usage.md) for every command and option,
[workflows](docs/workflows.md) for combined tasks, and
[local tools](docs/local-tools.md) for scans, checks and exit codes (Chinese).

## 3. Add a requested language

Run these from the **installed Yaya directory**, replacing the uppercase arguments
with actual local paths and the digest from the trusted catalog:

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256
python scripts/packs.py resolve --language ja
python scripts/packs.py list
```

Packs install outside the core, by default in `HOME/.yaya/language-packs/ID`.
A verified, compatible pack is used whenever its language is selected; there is no
separate setting to enable it.

Regional tags resolve to the closest pack: `zh-TW` uses `zh-Hant-TW`, `zh-HK` and
`zh-MO` use `zh-Hant-HK`, and `es-MX` uses `es` while keeping Mexican conventions.
The Taiwan and Hong Kong packs never substitute for each other, and `pt-PT` does
not resolve to `pt-BR`.

For a project-only installation:

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256 --project PROJECT_ROOT
python scripts/packs.py resolve --language ja --project PROJECT_ROOT
```

`--project` writes under `PROJECT_ROOT/.yaya/`. `--data-dir DATA_DIRECTORY` selects
another user data location instead, which is useful for isolated tests. Pass the
same option to later resolutions and changes. Commands that change packs reject
both options together. The helper never looks for a project root by scanning
parent directories.

Before replacing installed content, the helper checks the digest, file layout,
size limits, UTF-8 encoding, metadata and core compatibility. Verify where the
catalog came from as well: a matching checksum shows that the archive matches that
value, not who published it.

The resolver returns JSON:

| Status | Meaning |
| --- | --- |
| `ready` with `available: true` | The returned paths can be used. |
| `missing` | No matching installed candidate was found. |
| `invalid` or `incompatible` | The selected pack blocks resolution until it is repaired or replaced; a broken higher-priority override is not skipped. |

Resolution leaves installed files unchanged and never downloads a pack. Without a
pack, the AI can still edit and will note that dedicated guidance was unavailable.

## 4. Update, remove, or roll back

To update a language, get the new archive and its trusted hash:

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256 --replace
```

To remove Japanese, or to restore its latest backup, run the matching command:

```text
python scripts/packs.py remove ja
python scripts/packs.py rollback ja
```

Installing identical content changes nothing; replacing different content requires
`--replace`. Replacement and removal keep the old pack under
`DATA_DIRECTORY/backups/ID/`. Rollback validates and restores the latest backup and
keeps the pack it displaces. If the latest backup is invalid or incompatible,
rollback fails; it does not fall back to an older backup. Use the same target
option as the installation, and check the returned status and backup path. Backups
stay until you remove them.

Run one install, remove or rollback at a time per data directory. If a filesystem
error interrupts a swap and automatic restoration also fails, keep the reported
backup and fix the filesystem error before restoring it.

To update the core, repeat the staged replacement above and keep the previous
directory outside discovery paths; restoring it rolls the core back. Packs and
saved styles stay in `.yaya/`, separate from the core. A core with a different
major version needs packs built for that major version, or a core rollback. Check
how a third-party installer handles updates before using it with Release ZIPs.

To uninstall, remove the selected core directory. Keep `.yaya/` unless you also
want to remove its packs, styles and recovery data; other host installations may
use them.

## Saved styles and troubleshooting

An extracted style applies to the current task by default. When asked to save it,
Yaya writes a style file to the location you choose: project `.yaya/styles/` for
project scope, otherwise `HOME/.yaya/styles/`. Select the saved style explicitly to
reuse it.

Without Python, the host can still read the bundled editorial guidance. Install
Python through your usual process to use pack management and local checks. Report
checks that could not run, and resolve archive, checksum, path or compatibility
errors before continuing.

## Language-pack format

This core reads pack format 1 for core major 1 (`format_version: 1`,
`core_major: 1`). A pack may include `PATTERNS.md` for humanizing guidance;
without it, the host uses `GUIDE.md`. Packs are plain text and contain no
executable rules. After a core rollback, run `resolve` to check that installed
packs still match the restored core.

The complete package contract and contributor commands are in
[language-pack-spec.md](docs/language-pack-spec.md).
