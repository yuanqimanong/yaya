# tech — Technical and software communication

Scope: README text, API descriptions, operational procedures, incident explanations
and comments. Use the selected task's edit boundary. Software terminology does not
authorize code changes. Fact checking follows `../engineering.md` when requested.

## Editing decisions

- Name the acting component and observable outcome. Describe inputs, prerequisites
  and failure paths when present; keep a prerequisite next to the action it gates.
- Preserve identifiers, version ranges, configuration keys and exact API semantics.
  Default, locally resolved and production settings are distinct claims.
  A setting's name alone does not establish whether it is an environment variable,
  file setting or API parameter. Explain only the mechanism the source establishes.
- Keep `None`, missing, empty, zero and false distinct. Preserve the scope of retries,
  timeouts, cache lifetimes and permissions; do not exchange quantities' owners.
- Keep planned, implemented, deployed and observed states separate. A test or a
  code path alone does not prove production behavior or all-version support.
- For beginners, explain necessary terms briefly in context. For practitioners,
  prioritize the operation and its constraints; neither audience needs grand claims.

Original example (edit): “The system is currently in the process of retrying the
request, but only after a connection timeout and at most twice.” → “The system retries
the request only after a connection timeout, at most twice.”

Preserve: “生产环境通过环境变量覆盖默认值；当前未提供该变量的值。”
Do not turn this into a claim that production uses the default.

Boundary: no correctness proof, deployment acceptance or security audit. Unclear
code/comment conflicts may indicate code defects, not permission to bless behavior.

Rationale: [Google's technical documentation tone guidance](https://developers.google.com/style/tone)
supports direct, reader-focused explanation. Exact engineering relationships above
are Yaya's editing contract, not a claim that Google certified these checks.
