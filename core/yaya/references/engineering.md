# Engineering fidelity

Use this for technical fact checking, disputed comments, docstrings, and operational documentation. Ordinary polishing stays lightweight: preserve the original claim, inspect actual changes, and deliver directly. Do not force a report or turn domain examples into universal business rules.

## Evidence and scope

Start with the local implementation and types. Expand only when the claim depends on an override, inherited behavior, effective configuration, call chain, data lifecycle, or external contract. Follow the dependency that determines the claim; do not scan an entire repository by default. For external APIs, inspect the available contract or representative supplied response; a guessed field name is insufficient.

A factual correction needs a file path plus symbol/line, or an identified contract/sample and its relevant fields. Cite enough to distinguish observation from inference. When evidence is unavailable, retain uncertainty or report the unresolved claim. Do not infer intent solely from a comment, or design correctness solely from current code. A probable implementation bug remains visible; never silently edit business code or describe the questionable behavior as correct to reconcile a comment.

Distinguish **pre-existing conflict**, **problem introduced by this edit**, and **unconfirmed issue**. Fix or revert introduced wording errors within authorization. Report other objects without changing them. Prior authorization persists; do not request it again for the same scope.

## Review only the claims affected by the diff

| Relationship | Check |
| --- | --- |
| Subject and object | Who performs the action, who/what receives it, and which API supplies each field. |
| Quantity and unit | Keep the entity and relationship as well as the number/unit. Retention and query windows can differ. |
| Condition and range | First non-None preserves `False`, `0`, and empty values; first truthy does not. Inclusive `00…06` has seven members. |
| Negation and exceptions | Preserve only/unless/excluding and exception paths; missing, empty, false, and string `"false"` differ. |
| Certainty | Capability/possibility does not establish current status: “可以正常” cannot become “属正常” without new evidence. |
| Time and state | Keep historical/current, intended/implemented, planned/completed, and observed/expected separate. |
| Effective configuration | A default is not the resolved setting. Local and production may use different transports or overrides. |

Examples are synthetic relationships to test, not rules for an unrelated project: local `HTTP_TUNNEL` can coexist with production `HTTP_FIXED`; a database may retain 90 days while a dashboard queries 7 days; author data may come from search while summaries come from a detail API. Establish each relationship from this task's evidence.

Accurate text may remain unchanged. Avoid mass replacement for stylistic uniformity. A numeric/token checker cannot verify these relationships; vocabulary hits or zero hits measure neither naturalness nor factual correctness.
