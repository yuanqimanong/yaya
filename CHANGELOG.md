# Changelog

This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
Yaya uses [Semantic Versioning](https://semver.org/).

## [1.0.0] — Unreleased

First stable release.

- Ten task commands (`human`, `polish`, `review`, `verify`, `comment`, `prompt`,
  `style`, `origin`, `scan`, `check`) plus `help`, `domains` and `doctor`. One
  catalog defines each command's scope, options and help; unknown commands,
  domains or incompatible options fail instead of widening the task.
- Five experimental domain profiles: `tech`, `finance`, `data`, `academic` and
  `business`.
- Bundled Simplified Chinese (`zh-Hans`) and English (`en`) packs. Optional
  packs for Traditional Chinese in Taiwan (`zh-Hant-TW`) and Hong Kong
  (`zh-Hant-HK`), Japanese, Korean, French, Spanish, Brazilian Portuguese,
  Russian and Arabic. Every pack is experimental.
- Language-pack format 1 for core major 1, with checksum-verified installation,
  backups and rollback. `zh-MO` falls back to the Hong Kong pack.
- Standard-library Python helpers for task planning, wording scans, mechanical
  rewrite checks, comment and docstring boundaries, edit evidence, installation
  diagnostics and reproducible release builds.
