# [Language name] teaching examples

All examples are fictional. Each revision uses only the information given in its input. Write the examples in the pack's language and replace every bracketed instruction.

## 1. Financial paragraph

Input: [Revenue of 1.2 million in a local currency, up 8% year on year. Gross margin rose from 20% to 23%. The company thinks demand may recover but gave no order data.]

Acceptable: [A clearer version that keeps the currency, period, comparison basis, the 3 percentage-point change and the company's uncertain view.]

Unacceptable: [A version that claims strong orders and a confirmed recovery.]

Reason: [It invents order data and turns a possibility into a fact.]

## 2. Code comment

Input:

```python
def should_retry(status):
    # [A vague comment in the pack's language]
    return status == 429
```

Change only the comment: `# [Returns True for status 429 to indicate that a retry is needed.]`

Unacceptable: `# [Claims that all server errors are retried automatically until success.]`

Reason: [The code checks one value. It does not retry and sets no retry count. The function and code stay unchanged.]

## 3. Shorter prompt

Input: [A prompt with a decorative expert title that asks for exactly three points from {{text}}, at most 50 words each, and asks one question and waits if the material is insufficient.]

Acceptable: [The same instructions without the decorative title, keeping {{text}}, the count, the length and the waiting condition.]

Unacceptable: [A prompt that asks for a detailed explanation from general knowledge.]

Reason: [It loses the variable, the source restriction, the count, the length and the waiting condition.]

## 4. Style transfer

Sample: [Three short sentences: check that it works, then find what is slow, and do not conclude about untested parts.]

Transferable choices: [Short sentences, explicit order, direct actions, kept uncertainty.]

New task: write a prompt for reviewing a supplied log.

Acceptable: [Find the errors in {{log}}, list them in order of appearance, use only the log and state what cannot be determined.]

Unacceptable: [A claim to have repaired hundreds of servers.]

Reason: [It invents experience and identity instead of transferring the sample's structure.]
