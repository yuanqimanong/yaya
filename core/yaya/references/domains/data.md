# data — Data analysis communication

Scope: metric explanations, experiment summaries, dashboard text, survey results
and analysis reports. Editing does not rerun the analysis or certify its methods.

## Editing decisions

- Keep metric name, numerator/denominator, cohort, filters and time window together.
  Users, sessions and events are different units. Missing values are not zeros.
- Distinguish absolute change, relative change and percentage-point change. Keep
  mean/median, total/per-user, weighted/unweighted and cumulative/period measures.
- Preserve study design and stated limitations. Association, before/after movement
  or an observational sample does not by itself establish a causal effect.
- Keep sample size, effect size, interval and uncertainty when supplied. A p-value
  is not the probability that the hypothesis is true, nor the size of the effect.
- State the measured result before interpretation when that improves readability.
  For general readers, explain what was counted and compared using the supplied facts.
- Do not fill missing denominators, recompute metrics or add significance claims.
  A factual contradiction belongs in findings unless correction is authorized.

Original example (edit): “We are pleased to report that the observed conversion rate
rose from 4% to 5% in the pilot; assignment was not randomized.” → “The observed
conversion rate rose from 4% to 5% in the pilot; assignment was not randomized.”

Preserve: “样本仅含完成问卷的 240 人，不能代表全部用户。” Keep both the selection
condition and the population limit; do not turn respondents into all users.

Rationale: the [ASA statement on p-values](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf)
distinguishes statistical evidence from effect size and threshold-based conclusions.
This profile applies a limited reporting principle; it does not validate analyses.
