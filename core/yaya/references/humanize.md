# Humanize prose

Make the passage work for its reader. Match the existing voice or a supplied sample. Read only the resolved language's `PATTERNS.md` when available; it supplies language decisions, not facts or replacement commands.

## Choose the action

- **Detect / review:** point to the passage, quote the relevant words, explain the reading problem and suggest a direction. Keep the source unchanged. If no useful issue is established, say so. Separate an editorial suggestion from a source question.
- **Rewrite:** deliver the revised text. Preserve the kind of document and its useful detail. A passage with pervasive padding may need new sentence structure, not word swaps. Clear passages may stay unchanged.
- **Edit a file:** follow the same editing process within the authorized file scope, keeping a recoverable original or diff.

## Make a decision in context

1. **Find the point.** Remove introductions or conclusions that merely announce or repeat it. Keep orientation, summaries and politeness when they help this reader act. Do not assume the reader already knows a fact.
2. **Separate meaning from emphasis.** A comparison, list or metaphor should carry meaning. Remove empty emphasis around a claim; preserve distinct alternatives, limits, arguments and the writer's actual opinion.
3. **Make the relationship readable.** Unpack dense modifiers, identify an actor only when the source supplies one, and connect related ideas. Repetition can support a procedure or deliberate rhythm. Do not force short sentences, active voice or varied lengths everywhere.
4. **Check support.** A vague authority claim or missing evidence is a source question. Retain its attribution and uncertainty; flag it when material. Do not turn “some reviewers expect” into your own prediction or invent a source. Removing promotional padding does not authorize deleting a substantive claim.
5. **Read the whole result.** Check whether the main padding remains after trimming an opener: empty praise can occupy a whole sentence. Then check continuity, voice, the source's claims and relationships, and the requested output. Restore any loss. Do not add anecdotes, emotions or rough grammar to simulate a human author.

One unnecessary passage can justify an edit. Several ordinary words or punctuation marks cannot establish a problem by counting alone.

## Optional local checks

`scripts/detect_tells.py` scans a small English / Simplified Chinese subset. [tell_rules.json](../scripts/tell_rules.json) is its machine-rule source; findings are candidates for review. Silence is not a quality verdict, and hits do not establish authorship.

`scripts/check_rewrite.py` compares mechanical protections. Use `--help` for its supported categories and limits. A passing comparison cannot establish semantic fidelity: numbers can remain while their owners, conditions or meaning change. Use the comment checker for Python comment boundaries.
