# Initial smoke runs — 2026-10-19

These are selected original evaluation transcripts, not a language benchmark.
The inherited Codex host model produced the responses; an exact model revision,
temperature and random seed were not exposed or recorded. No separate model API
was called. Run notes record the actual local helpers used.

- `inputs.md`: the four shared requests for the main trial and baseline.
- `with-skill.md`: one fresh subagent context with the Skill and raw requests.
- `without-skill.md`: another fresh context given only the same four requests.
- `skill-run-notes.md`: main trial tool actions and actual checker result.
- `optional-languages.md`: a third fresh context installing three optional packs
  into an isolated data directory, then using their returned guides.
- `language-run-notes.md`: installation and resolution evidence and requests' context.

Each agent handled a batch; individual cases within each batch were not separate
sessions. The agents were not given `evals/cases.json`, expected answers, or each
other's outputs. Outputs are reproduced as generated. Notes from producing agents
are observations, not independent scores. The main implementer subsequently read
the outputs to check preservation and task boundaries, not to certify native quality.

One observed difference: the baseline silently chose an array type for `summary`;
the Skill trial kept the original schema requirement and placed a proposed type
convention outside the rewrite. The Skill trial kept the Python comment in English
and ran the comment checker; the baseline translated it to Chinese. These are
individual observations, not a measured improvement rate or a proof of causality.

The first main trial preceded the final wording clarifications about language-guide
selection and saved-style paths, and additional package-helper boundary fixes.
The optional packs' content was unchanged. Helper regressions and release builds
were rerun after code fixes. These logs do not constitute a full rerun of all
26 evaluation cases against the final release.

No native editor has reviewed these outputs, no downstream prompt benchmark was
run, and no language pack's `experimental` status was changed.
