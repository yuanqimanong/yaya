# Check command: independent execution

Two fresh Codex subagent contexts received the frozen skill and raw requests/files,
without expected answers. The inherited model's exact ID/settings were not exposed.
`initial/` retains three requests; `retest/` retains two requests after a reporting
clarification. Each contains original inputs, actual tool results/responses, and a
ZIP of the runtime used. `manifest.json` records hashes. All inputs remained intact.

| Case | Executed status | Observed behavior |
| --- | --- | --- |
| Currency parentheses removed | failed | Reported the exact amount token change; no repair or grant |
| Python ordinary comment edit | passed | Executed the comment checker; no source modification |
| TypeScript comment edit | unsupported | Kept unsupported distinct; no fallback to another kind |

The initial TypeScript response quoted the host shell's exit 1 as the checker exit.
A direct subprocess check confirmed the checker itself returned 2 with JSON status
unsupported. The guide now requests JSON status first and permits quoting an exit
code only when captured from that process. It also asks for result-specific limits
instead of listing every possible caveat. The fresh two-case retest captured checker
exit codes directly (0 and 2) and reported both outcomes correctly.

This is a small command-routing and delivery test. It does not establish editorial
accuracy, cross-model performance, or support for TypeScript comment checking.
