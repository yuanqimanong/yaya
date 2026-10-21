# Text editing

Let the user's purpose set the degree of change. Ordinary polishing addresses the stated problem; use [Humanize](humanize.md) when formulaic wording is the focus. Reorganize sentences and remove empty repetition where that helps, retaining substantive meaning. A request to edit an article does not authorize replacing it with a summary.

## Adapt expression

- **Domain:** preserve the relationships the field depends on. Finance: reporting period, currency, units, assumptions, attribution, and risk qualification. Computing: interfaces, versions, preconditions, failure states, and observed versus expected behavior. Data analysis: population, sample, metric definitions, and association versus causation.
- **Audience:** explain necessary terms for unfamiliar readers; retain precise terminology for specialists. Plain language can still be exact. Do not add an unsupported analogy or procedure to fill a gap.
- **Tone:** adjust directness, formality, warmth, humor, and sentence rhythm. Keep the writer's substantive opinion and degree of certainty unless the user asks to change them.
- **Samples:** borrow observable expression habits while keeping the target material's content. Use the style-learning guide if a reusable style description is requested.

These are editing criteria, not domain verification. A polished financial statement has not thereby been audited; an elegant technical explanation has not thereby been tested.

For requested technical fact checking or a disputed engineering claim, use [engineering fidelity](engineering.md). Pure polishing preserves claims and uncertainty. Review-only work reports findings without writing. Reuse the user's existing authorization; changes to examples, runtime strings, schema metadata, or code require their own scope.

## Files and structure

Keep code fences containing programs, inline code, link destinations, front matter, IDs, and table data intact. Preserve headings and anchors unless their revision is requested; check dependent links when changing them. A prose passage inside a fence is still prose when the request identifies it as the editing target.

Retain operational order: a prerequisite belongs before the step it constrains. Keep independent list items and the pairing between figures and labels. Do not turn a long article into a summary unless requested. Handle rich document formats with an available document tool; do not edit their binary content as plain text.

For a file rewrite with protected text or Markdown structure, use the read-only `scripts/check_rewrite.py BEFORE AFTER` on a saved original and candidate. Its JSON states the implemented protections and any unsupported syntax. A pass checks mechanical boundaries only: still compare facts, ownership of numbers, negation, conditions, and certainty. `--allow` accepts a reviewed manifest bound to this exact input/candidate and enumerated differences; category-wide bypasses are rejected. See [validation](validation.md) for batch evidence and exact grants.

## Small examples

Source: “We are currently in the process of reviewing the forecast. The estimate may change after the audit.”

Edit: “We are reviewing the forecast. The estimate may change after the audit.”

Keep: “Only retry after the transaction has rolled back.” Removing “only” or moving the condition changes the operation, not merely its style.

Source: “Revenue was CNY 8 million in Q2, up 6% year on year; the figures are unaudited.” A simpler version must keep the currency, period, comparison basis, and unaudited status. Do not replace it with “Revenue performed well.”
