# Humanize prose

Make the passage work for its reader. Match the existing voice or a supplied sample. Read only the resolved language's `PATTERNS.md` when available; it supplies language decisions, not facts or replacement commands.

## Choose the action

- **Detect / review:** point to the passage, quote the relevant words, explain the reading problem and suggest a direction. Keep the source unchanged. If no useful issue is established, say so. Separate an editorial suggestion from a source question.
- **Rewrite:** deliver the revised text. Preserve the kind of document and its useful detail. A passage with pervasive padding may need new sentence structure, not word swaps. Clear passages may stay unchanged.
- **Edit a file:** follow the same editing process within the authorized file scope, keeping a recoverable original or diff.

`human` includes all decisions below by default. `--focus direct` on `human` or
`review` selects only the directness pass below: unnecessary contrasts, defensive
framing and redundant qualifications. Keep unrelated wording, structure and voice;
make only the local repairs needed for continuity. A natural-language request can
select the same focus. Review mode returns findings, not a replacement passage.

## Make a decision in context

1. **Find the point.** Remove introductions or conclusions that merely announce or repeat it. Keep orientation, summaries and politeness when they help this reader act. Do not assume the reader already knows a fact.
2. **Separate meaning from emphasis.** A comparison, list or metaphor should carry meaning. Remove empty emphasis around a claim; preserve distinct alternatives, limits, arguments and the writer's actual opinion.
3. **Make the relationship readable.** Unpack dense modifiers, identify an actor only when the source supplies one, and connect related ideas. Repetition can support a procedure or deliberate rhythm. Do not force short sentences, active voice or varied lengths everywhere.
4. **Check support.** A vague authority claim or missing evidence is a source question. Retain its attribution and uncertainty; flag it when material. Do not turn “some reviewers expect” into your own prediction or invent a source. Removing promotional padding does not authorize deleting a substantive claim.
5. **Read the whole result.** Check whether the main padding remains after trimming an opener: empty praise can occupy a whole sentence. Then check continuity, voice, the source's claims and relationships, and the requested output. Restore any loss. Do not add anecdotes, emotions or rough grammar to simulate a human author.

One unnecessary passage can justify an edit. Several ordinary words or punctuation marks cannot establish a problem by counting alone.

## Directness: remove the imagined objection

Read the actual question and nearby passage before editing a clarification. Look
for a contrast that introduces an irrelevant alternative, a denial that answers
an imagined critic, or several caveats that repeat the same qualification. These
can span sentences or paragraphs; punctuation alone does not define the pattern.

For each candidate, ask what the reader loses if it is removed:

- **Keep information that changes interpretation or action.** Real corrections,
  exclusions, tradeoffs, operating conditions, risks, commitments, attribution and
  evidence limits can matter even when the user did not ask about them. Preserve
  stated distinctions such as mitigation versus fix, forecast versus realized
  return, and excluded versus zero-valued observations.
- **Trim framing that adds no such information.** State the supported point
  directly when a negative half only supplies a rhetorical foil. Remove narration
  of candor or caution while retaining the actual admission. Collapse a repeated
  caveat without merging distinct limitations or hiding a condition needed where
  a claim is read independently, such as an abstract.
- **Keep uncertainty at its original strength.** A stack of equivalent hedges can
  become one precise hedge. Never replace an unknown with a plausible explanation,
  turn a tentative finding into a conclusion, or invent a missing scope, source,
  threshold or method to make the prose sound concrete.

Neither “not / but / rather than” nor “不是 / 而是 / 不代表” is a banned expression.
A meaningful two-sided comparison, an answer to a real misconception, courtesy
that repairs an actual misunderstanding, and deliberate literary contrast may
already be good writing. When context is missing, keep a potentially substantive
distinction; ask only if the ambiguity prevents the requested edit. Do not assume
that an unasked-for topic is irrelevant merely because the user did not name it.

Use the source's affirmative claim after a cut. If it supplies no substantive
replacement, do not manufacture one. Keep the sentence's function: cutting its
frame must not turn a description into an instruction, or an instruction into a
claim that the action is complete. Avoid adding a new prefatory disclaimer,
fake conversational aside, personal experience or exaggerated confidence to the
rewrite. When only the text is requested, deliver the text without an explanation
of the cleanup.

## Other recurring habits

With the default `all` focus, also check empty praise of the question, repeated
announcements of what the answer will do, generic transitions and formulaic closing
offers. Edit them only when they displace useful content or clash with the task.
Warmth, apologies, summaries and offers can be appropriate in their real context.

Apply these decisions to observable wording, regardless of the model or author
named by the user. No model-brand lexicon or calibrated frequency comparison is
provided. Do not infer GPT, Opus, DeepSeek, Doubao or human authorship from a phrase,
or promise to evade a detector. Naturalness comes from fidelity, relevance and the
writer's voice; technical and formal prose need not become colloquial.

## Optional local checks

`scripts/detect_tells.py` scans a small English / Simplified Chinese subset. [tell_rules.json](../scripts/tell_rules.json) is its machine-rule source; findings are candidates for review. Silence is not a quality verdict, and hits do not establish authorship.

Directness decisions require context and are not implemented as detector regexes.
The optional scanner does not identify excessive defensiveness or test the focus.

`scripts/check_rewrite.py` compares mechanical protections. Use `--help` for its supported categories and limits. A passing comparison cannot establish semantic fidelity: numbers can remain while their owners, conditions or meaning change. Use the comment checker for Python comment boundaries.
