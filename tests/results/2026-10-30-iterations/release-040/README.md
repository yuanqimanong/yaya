# 0.4.0 delivery verification

Final local command: `python -B -X utf8 -m unittest discover -s tests`.
Observed result: 290 test methods in 85.572 seconds, no failures/errors, and eight
environment skip records. The existing Windows link/Python-version restrictions
remain represented as skips. Skill frontmatter validation also passed.

The release builder produced the core and optional language artifacts recorded in
`build-catalog.json`. The core archive SHA-256 is
`c0de4ce57157f709fbed554e86da0be1f7e04a1be08dc7912b3b881f89978655`.
Generated release ZIPs remain local build outputs and were not publicly released.

The verified local core was installed after checking the previous 0.3.2 receipt
and preserving a backup outside skill discovery. `installation.json` contains the
actual command smoke results and all 42 runtime file hashes. Source, archive and
installed runtime contents agree. Existing user customizations were checked before
replacement. This verifies local helpers and content, not every host's discovery UI.

Recovery was exercised in an isolated installed-tree copy: all 12 changed/new
runtime paths returned to the previous installation, including removal of the new
check guide. A second test refused a later user edit and left the test tree intact.
The real installation remains 0.4.0. Details are in `verification.json`.

No domain quality label changed. Financial/technical preservation checks are
mechanical; semantic relationships and professional accuracy still need review.
