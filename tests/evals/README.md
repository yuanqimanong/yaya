# 编辑行为评测

评测使用虚构材料，分别检查原意保留、任务完成和表达质量。脚本准备材料并校验证据，
当前宿主执行模型调用；使用本地 Codex CLI 时见 [CLI.md](CLI.md)。

| 材料 | 用途 |
| --- | --- |
| `cases.json` | 26 条回归用例：五种语言、四类任务与范围边界 |
| `heldout.json` | 8 条新增用例；创建时不在运行指南中，用于迭代后须标为回归 |
| `humanize.json` | 72 条原创合成用例：中英改写、清楚文本、内容保护和任务范围；预先列出 12 条 pilot |
| `scenarios.json` | 6 条跨场景材料：较长财务说明、局部章节、明确换语气、作者声音、代码上下文和提示词行为契约 |
| `refinement.json` | H019 首轮失败后新增的 2 条具体观点保留控制例；仅用于显式选择的修正复测，不计入默认主矩阵 |
| `integration/` | 真实文件编辑与保存风格的隔离素材 |
| `downstream.json` | 原提示词和改写后提示词的执行检查 |

## 准备和生成

从项目根目录准备新的运行目录。每次试验使用不同目录名：

```text
python tests/evals/prepare.py tests/runs/my-run
```

默认从四个集合准备 112 题，为 `skill/`、`baseline/` 两组各生成 112 个独立上下文的请求包。
此步骤不调用模型。

只选一个集合，或先运行预定的 pilot：

```text
python tests/evals/prepare.py tests/runs/humanize-full --suite humanize
python tests/evals/prepare.py tests/runs/humanize-pilot --suite humanize --pilot
python tests/evals/prepare.py tests/runs/regression --suite cases --suite heldout
```

`--suite` 可重复使用，只读取 `tests/evals/` 内的 JSON 文件。`--pilot` 要求只选择一个集合，并按其 `pilot_case_ids` 的顺序准备请求；当前 humanize pilot 是 12 题、两组共 24 次独立生成。pilot 不能代替全部用例或多轮验证。

竞品对照和定向复测可重复传入 `--case-id ID`，冻结本次子集，不能与 `--pilot` 混用。
报告须列明选题范围；子集结果不能代表全部 112 题。

准备脚本保存核心和外部语言包快照，冻结评审条件。生成包仅含 `id`、`request`、`input`，
不含 group、checks、来源标签或 pilot 说明。`criteria.json` 留待收集与评审使用；
manifest 记录文件哈希、文件集和隔离方式。

用同一模型、相同设置，为每个 `batch-NNN/requests.json` 启动全新上下文：

- Skill 组可读取快照的 `SKILL.md` 及相关引用，语言包数据目录为本次运行的 `data/`。
- baseline 组直接处理请求，不读取 Skill、项目源码或其他结果。
- 两组均不可读取评审条件、原始用例文件、其他批次输出或以往结论。每题独立处理，不复用其他题的事实。
- 每批只写自己的 `outputs.json`。保留完整交付文本，不截取有利片段。代码注释题交付完整代码，不加 Markdown 围栏。

结果格式：

```json
[
  {
    "id": "请求中的 ID",
    "text": "完整交付文本",
    "notes": "实际执行过的检查或限制，不填自评分",
    "skill_used": true
  }
]
```

baseline 的 `skill_used` 为 `false`；普通算术、代码创建等不适用任务，即使在 Skill 组也应为 `false`。这个字段是执行者的记录，不能单独证明触发器正确。

默认 `--batch-size 1` 要求每题隔离。设为大于 1 时，同批用例共享上下文，manifest 标为“每批隔离”。
执行时必须按记录创建独立上下文，分目录存储本身不保证隔离。记录模型版本、设置和工具使用；
宿主未提供的字段写“未知”。

## 收集与匿名评审

```text
python tests/evals/collect.py tests/runs/my-run tests/results/my-run
```

收集器核对冻结条件、快照、请求与外部数据，拒绝缺题、重复或未知 ID、跨请求包输出、
空输出、重复 JSON key 和格式错误。protocol 2 还拒绝未记录的新增文件，仅忽略
`__pycache__` 与 `.pyc`。随后检查指定保护片段和 Python 注释范围，生成每包最多 12 对的
匿名 A/B 评审包。评审分批不改变生成时的每题隔离。

存在 `cli-run.json` 时，收集器重新核对每题原始日志、final JSON、输入哈希与已发布输出；
复用结果回查原运行的成功尝试。`execution-audit.json` 分列首次失败、恢复调用和复用数量。
缺少 CLI 元数据的历史材料标为 `not_recorded`，执行来源视为未验证。已有匿名评审目录不覆盖。
汇总时 A/B 必须与两组一一对应，机械检查不得重复或缺失；检查器 error 计为不确定。

完整生成后，可额外保存固定正文子集的机械保护结果：

```text
python tests/evals/check_outputs.py tests/runs/my-run tests/results/my-run/prose-mechanical.json
```

脚本先执行 `verify_run`，要求 protocol 2 且两组整个 run 的输出完整。固定检查 H001–H060、
X001、X002、X004，每组 63 题，不接受选题参数。使用本次快照的
`snapshot/yaya/scripts/check_rewrite.py` 比较原文与完整交付，保留包装，不添加 `--allow`
或其他放宽选项。Python 注释仍由 `collect.py` 检查。

结果写入新的 JSON 子文件，不覆盖已有文件或修改输入、评级。每组记录 `passed`、`failed`、
`unsupported`、`error`；每题保留 violations、完整 checker 结果和原文/输出 SHA-256，
并记录 run 输入读取前后的哈希。机械 failed 需另查语义，unsupported/error 不能算通过，
passed 也不能证明语义正确。退出 0 仅表示结果收集完整。先运行 `collect.py` 建立主结果目录，
再写此子文件，避免触发收集器的拒绝覆盖规则。

让独立评审者只读 `review/batch-*.json`。不提供 `blind-key.json`、Skill、执行者 notes 或其他评审意见。每个候选分别记录：

- `fidelity`、`task`：`pass` / `fail` / `uncertain`，附原文与输出的具体证据。
- `quality`：相对原文 `better` / `same` / `worse` / `uncertain`；创作或算术等不适用题用 `not_applicable`。
- `preference`：`A` / `B` / `tie` / `uncertain`。表达偏好不能抵消事实或任务失败。

争议另行复核，保留原判与裁决理由；未裁决项不能计作通过。
母语质量仍需胜任该语言的人工编辑审核。

把完整评审数组保存为结果目录的 `judgments.json`，每项包含 `id`、`A`、`B`、`preference`、`reason`；A/B 内含 `fidelity`、`task`、`quality`、`evidence`，理由和证据为字符串。然后运行：

```text
python tests/evals/summarize.py tests/results/my-run
```

汇总器校验完整性和硬项，保存 `summary.json`，并按用例的 group 汇总质量判断与偏好。原始输出和评审不被重写。文字发生变化不等于误改；清楚文本是否被过度修改，需要结合请求和评审证据判断。

## 迭代与补充验证

保留首轮输出、失败、快照哈希和条件映射。确认问题后修改相关规则或程序，在新目录
复测失败场景及相邻正常场景。参与调参的新增用例转为回归，不再计入未见留出集。

文件测试先把 `integration/` 复制到隔离工作目录，再按其中的请求实际编辑。核对限定范围外的字节、指令和既有文件，保留修改前后文件及真实检查结果。风格文件只写本次测试明确指定的位置。

提示词执行测试使用 `downstream.json` 的材料替换相应占位符，对原提示词和改写后提示词分别运行。检查输出格式、数量、等待条件与事实。它验证所选样例的行为，不证明所有下游模型都有提升。

评审关注实际阅读效果、原意和任务要求。篇幅、连接词数量、模型自评分或“AI 写作概率”
均不能代替这些判断。CI 只运行确定性检查，模型评测须显式启动。

按 [CLI.md](CLI.md) 归档完整证据后，可清理对应的临时运行目录。
历史报告与原始输出留在 `tests/results/`；新试验从准备步骤重新开始。

2026-10-20 的 0.1 首轮采用早期 protocol 1、每批最多 5 题：运行前已快照 Skill，评审条件未提前哈希；收集时核对了全部生成请求与用例。旧结果仍按旧协议读取。当前 protocol 2 冻结条件、请求和外部语言包，并核对完整文件集；这些保证不能追溯到旧运行。

## 工程保真与“这是 AI 吗”的旧版对照

`engineering.json` 的 12 个工程案例和 4 个来源审阅案例带有预设检查条件。它们是定向回归，不是隐藏测试集或来源分类准确率基准。机械约束由 `test_comments.py`、`test_docstrings.py`、`test_edit_evidence.py` 和 `test_check_rewrite.py` 单独验证。

先取得任务开始时的旧技能副本，再冻结两组相同请求；生成者不会看到 checks。以下命令使用已有 CLI 和宿主模型配置，会产生模型用量：

```text
python tests/evals/engineering_compare.py prepare tests/runs/paired --old PATH_TO_OLD_YAYA
python tests/evals/engineering_compare.py run tests/runs/paired --workers 1 --timeout 180
python tests/evals/engineering_compare.py collect tests/runs/paired --destination tests/results/paired
python tests/evals/judge_cli.py tests/runs/paired/review tests/results/paired --workers 1
```

旧版/新版按题交错，各题独立上下文。共同输入、接口样本、模型设置保持一致；仅任务相关的技能指导不同，新增规则不会伪装成旧版材料。CLI 退出码、事件、完整回答、工具活动、内容摘要和缺失结果均保留。生成失败时停止追加；`--resume` 仅复用经校验的成功记录，不覆盖失败。匿名评审仍是模型判断，必须复核具体证据，不能代替人工标注或跨模型重复测试。不要把同一题的试跑、基础设施失败或未启动项计为通过样本。

明确要求交付验证说明的案例使用 `review_delivered_notes: true`，将实际交付的 notes 一起传给评审，避免把收集器隐藏字段误判为模型遗漏。这个标记和 checks 一样不传给生成者。其他案例继续只审用户可见正文；无关生成元数据不进入匿名材料。已启动运行冻结收集器版本；改动脚本后使用新运行目录，旧证据保留原脚本及摘要。
