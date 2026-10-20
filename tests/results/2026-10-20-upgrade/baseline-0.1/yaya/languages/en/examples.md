# English teaching examples

All scenarios below are fictional teaching material. Each revision must use only its supplied facts.

## 1. Edit a financial paragraph

Input: Revenue was $12 million this period, up 8% from the same period last year. Gross margin went from 20% to 23%. The company thinks demand may be recovering, but it has not provided order data.

Acceptable: Revenue for the period was $12 million, up 8% year over year. Gross margin increased from 20% to 23%, a gain of 3 percentage points. The company believes demand may be recovering but has not provided order data.

Unacceptable: Strong orders confirm a sustained recovery in demand.

Why: The rejected version invents order evidence and removes uncertainty. The percentage-point change is directly calculable from the input.

## 2. Rewrite a code comment

Input:

```python
def should_retry(status):
    # Here we intelligently check whether this is a status that calls for retrying.
    return status == 429
```

Replace only the comment with: `# Return True for status 429 to indicate that a retry is needed.`

Unacceptable: `# Automatically retry all server failures until successful.`

Why: The code checks one value; it does not perform retries or specify a retry limit. Keep the function and its code unchanged.

## 3. Remove empty framing from a prompt

Input: You are a world-class summarization expert. Use your exceptional abilities to summarize only {{text}} in three points, each at most 20 words. If the material is insufficient, ask one question and wait for the answer before summarizing.

Acceptable: Summarize only {{text}} in three points, each at most 20 words. If the material is insufficient, ask one clarifying question and wait for the answer before summarizing.

Unacceptable: Use your knowledge to write a detailed summary.

Why: The rejected version drops the variable, source restriction, length, count, and waiting condition.

## 4. Transfer a sample's style

Sample: First, check that it works. Then find what is slow. If you have not tested something, leave the conclusion open.

Transferable choices: short sentences, clear sequence, action-led wording, explicit uncertainty.

New task: Write a prompt for checking supplied logs.

Acceptable: Find the errors in {{log}}. List them in the order they appear. Use only the log. Say when the evidence is insufficient.

Unacceptable: I have fixed hundreds of servers, so trust my diagnosis.

Why: The rejected version invents experience and identity instead of transferring the sample's structure.
