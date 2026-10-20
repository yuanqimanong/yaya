# 操作记录

## 读取与语言选择

- 读取 `core/yaya/SKILL.md`。
- 根据四个独立请求，读取 `references/text.md`、`references/prompts.md`、`references/comments.md`、`references/style-learning.md`；为保持中文文本及英文注释各自的语言，读取 `references/language-packs.md`。
- 在 `D:\AIProjects\yaya\core\yaya` 分别运行：

```text
python scripts/packs.py resolve --language zh-Hans --project D:\AIProjects\yaya
python scripts/packs.py resolve --language en --project D:\AIProjects\yaya
```

- 两次均退出0。返回 `status: ready`、`available: true`、`source: bundled`、`quality: experimental`、`version: 0.1.0`；分别解析到 `zh-Hans` 和 `en`。
- 读取返回的 `languages/zh-Hans/GUIDE.md` 和 `languages/en/GUIDE.md`。没有读取示例文件。
- 未读取 `evals/`、`tests/`、`docs/validation.md` 或其他代理报告。

## 输出与检查

- 将四项输入保存到 `inputs.md`，四项真实输出保存到 `outputs.md`。
- 保存原始 `before.py` 与候选 `after.py`；仅把普通注释改为 `# Pause the current thread for delay seconds.`。
- 在 `D:\AIProjects\yaya\core\yaya` 实际运行：

```text
python scripts/check_comments.py '..\..\.tmp\forward-smoke\before.py' '..\..\.tmp\forward-smoke\after.py'
```

退出码：0。检查器原始 JSON 输出：

```json
{"status": "passed", "language": "python", "changed_comment_lines": [4], "violations": [], "limitations": ["Only .py/.pyi sources parseable by the running Python interpreter are supported.", "Only ordinary # comment text may change; line count, line endings, BOM, and all other bytes must remain identical.", "Docstrings, f-strings, and doctests inside strings are immutable; recognized comment directives and comment doctest blocks are protected.", "Unknown external-tool directives cannot be exhaustively recognized; review the diff and run the host project's checks.", "A pass does not verify that comments are accurate, useful, or consistent with the code.", "LF and CRLF are supported; lone-CR newlines and encodings that cannot be mapped exactly are unsupported."]}
```

对改写内容的复核：收入金额、同比口径、毛利率起止值、公司归因及需求判断的不确定性均保留；提示词保留变量、条数、字数、澄清等待及 JSON 键；英文注释未翻译；风格例子未带入样文个人经历，未保存为常驻偏好。

## 使用中遇到的阻碍

- 每次 PowerShell 命令输出开头都有 `Attempting to perform the InitializeDefaultDrives operation on the 'FileSystem' provider failed.`。命令仍成功执行并返回退出码0，读取和 Python helper 均可用，未阻止本次试用。
- 提示词原文没有说明澄清提问阶段如何与仅输出 `summary` 键的 JSON 格式衔接。保留原要求，并在输出中另列可选格式约定，没有静默改动行为。
- 没有其他阻止完成的障碍。所有写入均在 `.tmp/forward-smoke/`，没有修改 Skill 源码。
