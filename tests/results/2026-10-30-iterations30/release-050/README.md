# Yaya 0.5.0 delivery validation

This report records the 0.5.0 candidate's validation at the time of execution.
It covers local tests, package reproducibility, installation and recovery. No
GitHub Release had been published at that point. Check the repository and installed
runtime separately for their current state.

## Executed validation

- Windows / Python 3.13: 350 unittest methods ran, with no failures/errors and
  8 environment-dependent skips (template strings need Python 3.14; the remaining
  skips concern unavailable symlink/junction creation privileges).
- The final main-help correction was followed by all 28 command tests passing.
  The Skill validator passed. The remote workflow tests Ubuntu/Windows with
  Python 3.10, 3.13 and 3.14. Remote results are tied to their recorded commits;
  later changes require checks on their own commit.
- Two complete builds produced byte-identical assets. Core archive SHA-256:
  `60d85c05ae9870e8cd2b65f6f5f184037df3e2ae646c1d9c88f016fe6ee01e37`.
- Both the relocated archive and personal installation passed ten smoke checks:
  version, doctor, help, style/source plans, rejected read-only write request,
  preservation pass/failure, and a selected-rule scan with stable-file evidence.
- The prior installation exactly matched the 0.4.0 receipt (42 files), with no
  unknown additions or customizations. A separate backup was taken; the final
  0.5.0 installation matches all 44 runtime file hashes.
- Isolated rollback restored all 42 original files, removed the two new runtime
  files, rejected later user changes, stayed read-only in dry-run mode, and was
  idempotent. The actual installation remained 0.5.0 throughout the rehearsal.

[validation.json](validation.json) records artifact/runtime hashes and outcomes
without publishing local account paths. Full local logs, backup, installation
receipt and guarded rollback helper remain under
`.yaya/iterations30/final-install/` in the working checkout (ignored by Git).
`restore.py` defaults to a dry run; `--apply` restores only receipt-matching files
and refuses later modifications. Back up any later user changes before recovery.

## What the evidence supports

The helpers and package support the documented boundaries and tested workflows.
The behavioral evidence comprises [five-domain relationships](../domain-relationships/README.md),
[style reuse](../style-use/README.md), [selected sources](../verify-sources/README.md),
and [concise verification](../verify-concise/README.md), with raw requests and outputs.
These directed, uncalibrated observations do not establish cross-model superiority
or certify domain accuracy. The scanner remains a finite literal detector and the
prose checker a Markdown subset; semantic review is still needed.

Running installed helpers does not verify automatic host Skill discovery or a
host reload. Optional language packs were not modified by the core upgrade.
