# 本地 Codex CLI 生成

`run_cli.py` 为每题启动独立的临时 Codex CLI 进程，使用已有 CLI、登录状态和宿主配置。
它不安装服务或复制认证，也不修改 `CODEX_HOME`、模型配置或权限。
以下命令会调用模型并产生用量；普通单元测试使用本地 stub。

从项目根目录执行，将 `PATH_TO_CODEX` 替换为已安装的 CLI 路径。先准备运行目录，
再试跑每个条件各一题，最后继续剩余题目：

```text
python tests/evals/prepare.py tests/runs/humanize-cli --suite humanize --pilot
python tests/evals/run_cli.py tests/runs/humanize-cli --executable PATH_TO_CODEX --limit 1
python tests/evals/run_cli.py tests/runs/humanize-cli --executable PATH_TO_CODEX --resume
```

`--limit 1` 表示每个所选条件各生成一题。默认运行 `skill`、`baseline` 两组，
默认并发为 3 个进程，每题超时 180 秒；可用 `--workers`、`--timeout` 调整。
仅执行一组时指定 `--conditions skill` 或 `--conditions baseline`。

CLI 使用 `exec --ephemeral --sandbox read-only --skip-git-repo-check --color never --json`，
传入独立工作目录和结构化输出 schema。进程内设置 `-c project_doc_max_bytes=0`，
减少父级项目说明的影响；模型、reasoning 和采样参数沿用宿主配置。
报告分别记录配置中的模型名称和服务端精确修订；后者不可得时标为未知。

输入经 stdin 传入，写完即关闭。每个 prompt 只包含原始请求、原文和当前条件的指导材料。
任务和语言仅用于选择指导文件；`checks`、`group`、评分与答案不传给生成者。

stdout 和 stderr 直接写入证据文件，保留原始字节，避免等待后代进程关闭继承的 PIPE 句柄。
即使日志含 `turn.completed`，进程超时仍记为失败；未取得的退出码记为 `null`。

- Skill 组从本次运行的固定快照加载入口、一个任务参考和对应语言指南。humanize 使用语言 `PATTERNS.md`，缺少该文件时回退 `GUIDE.md`。繁体香港请求可回退到独立 `zh-Hant` 包。超出 Skill 范围的题只提供入口，让模型判断适用性。
- 无 Skill 基线不加载 Yaya。
- 生成任务禁止工具调用、网络、读取其他文件或持久保存风格。CLI 工具并未物理移除；执行器检查 JSONL，发现工具活动或未知 item 类型即将该次生成记为失败。合格记录只能表述为“日志中未观察到工具调用”。

CLI 仍继承用户现有的宿主配置。若平台沙箱阻止 CLI 自身状态库写入，由当前宿主正常审批；不要通过复制认证、改 `CODEX_HOME` 或放宽 CLI 沙箱来规避。运行器本身不请求或绕过审批。

每题证据保存到 `batch-NNN/cli-attempt-01/`：

| 文件 | 内容 |
| --- | --- |
| `prompt.txt`、`started.json` | 完整输入、输入/指导/schema 哈希、命令、开始时间 |
| `stdout.jsonl`、`stderr.txt` | 完整 CLI 日志和错误输出 |
| `final.json`、`output-schema.json` | CLI 原始最终 JSON 及本次固定 schema |
| `completion.json` | 退出码、耗时、实际返回的 usage、失败原因、产物哈希 |

只有 CLI 成功退出、JSONL 记录完成、没有工具活动、输出 schema 和 case ID 正确时才生成供收集器读取的 `outputs.json`。`skill_used` 专指 Yaya；竞品组仍是 `false`。

某些 CLI 版本把“忽略未识别配置项”记作 `item.type=error`。执行器仅接受一种已观察到且
逐字匹配的完整诊断：同一用户 `config.toml` 中，`model_providers.openai_https` 下的
`model`、`model_reasoning_effort`、`notify` 三项被忽略。诊断逐次保存在原始日志和
`completion.json` 的 `diagnostics` 中。其他字段、额外错误文本、未知或顶层 error、
失败事件及工具活动仍判为执行失败。此识别不修改配置，也不改变已有失败记录。

`--resume` 重新检查冻结输入、prompt、schema、输出与日志，只跳过完整且未改变的成功记录。
失败、超时、中断、错误 ID、损坏 JSON 和缺失文件均保留。独立试验使用新运行目录；
基础设施失败按下节恢复。报告须单列首次失败、恢复次数和最终有效样本。

执行器同时提交的任务不超过 `--workers`。失败后停止追加，已启动任务继续记录结果；
其余标为 `not_started`，不创建尝试目录，也不自动重试。报告分别统计计划数量、
实际启动数量、失败和未启动数量；未启动项不计入生成失败或有效样本。

## 基础设施恢复

`continue_cli.py` 处理已经冻结的生成运行。它跳过经重新校验的成功样本，在 `cli-attempt-01` 启动从未执行的题；只有显式指定 `--retry-infrastructure`，才允许已审计的基础设施失败追加一次 `cli-attempt-02`：

```text
python tests/evals/continue_cli.py tests/runs/full-run --retry-infrastructure --workers 3
python tests/evals/continue_cli.py tests/runs/competitor-run --retry-infrastructure --workers 3 --competitors-dir tests/runs/competitor-sources
```

两个命令须顺序执行，将总并发控制在 3 以内。工具限制单次运行最多 3 个进程，
不会跨命令协调并发。恢复沿用原始 CLI 命令、模型配置和冻结输入，
不修改 `run_cli.py`、`cli-run.json` 或原始 runner 哈希。

仅允许恢复两类失败：直接 CLI 进程超时且未取得退出码；或非零退出，且 stderr 包含完整的
`memory allocation of 数字 bytes failed` 行。恢复前核对身份、命令和所有原始日志哈希，
重新审计 JSONL。工具活动、未知事件、模型错误、损坏 JSONL、错误 case ID、
最终 JSON 不符合 schema 或未知非零退出均不能自动恢复。

保留原失败及已经返回的模型回答。仅将首次成功退出且通过全部检查的结果写入 `outputs.json`。
成功样本不能再次生成；恢复后的第二次尝试仍失败时停止补充队列，保留已启动结果和未启动项，
不自动进行第三次尝试。每个运行只接受一次 continuation 操作，再次执行拒绝覆盖。

`continuation-started.json` 保存恢复前计划、原始元数据哈希、失败证据、保留结果及待启动任务；`continuation.json` 保存实际结果、恢复产物哈希与未启动项。基础设施恢复是额外模型调用，不能当作独立 benchmark 重复运行，也不能把恢复后的结果表述成“所有首次执行成功”。

## 竞品条件

先在 `tests/runs/competitor-sources/` 下准备固定修订的源码，子目录为 `humanizer/` 和 `humanizer-zh/`。
各目录包含 `SKILL.md`、`LICENSE`、`source.json`；后者记录完整 commit SHA 和两个文件的 SHA-256。
可将[已归档的评测源码](../results/2026-10-20-upgrade/competitor-sources/README.md)复制到该目录，
或重新取得并记录另一修订。执行器核对哈希，只读取指导，不运行竞品代码。

```text
python tests/evals/run_cli.py tests/runs/competitor-run --executable PATH_TO_CODEX --conditions baseline --competitors-dir tests/runs/competitor-sources
```

运行前须准备共同适用的用例：任务为 `text` 或 `humanize`，语言为 `en` 或 `zh-Hans`。
其他任务或语言在调用模型前即被拒绝。英文使用 Humanizer，简中使用 Humanizer-zh；
`cli-run.json` 将 `baseline_kind` 记为 `competitor`，与 `no_skill` 分开统计。
指导原文完整进入 prompt，回答完整保留。

复用另一运行的 Yaya 输出时，记录来源、冻结输入与模型配置的一致性，以及原始产物哈希；
`run_cli.py` 不自动复制。随后收集完整输出、匿名评审并解盲。执行成功仍需质量评审；
单模型的一次生成只能提供该次试验的证据。

用 `compare_runs.py` 可以把完整无 Skill 对照运行中的首次成功 Yaya 输出复用到单独的竞品运行：

```text
python tests/evals/compare_runs.py reuse tests/runs/full-run tests/runs/competitor-run
```

目标运行必须事先冻结要比较的全部用例，并且只用 `--conditions baseline --competitors-dir ...` 生成竞品组。脚本按目标的全部 ID 复用，没有挑题或挑轮次选项。源、目标的核心和语言包快照、完整用例（含 `suite` 与检查要求）、每题请求、模型及 reasoning 配置、输出 schema、CLI 实现和实际命令选项必须一致。目录、并发数、执行时长、源运行含更多用例及不同条件选择是允许的调度差异。

每个源结果必须来自成功的 `cli-attempt-01`，或由上述恢复工具证明的首次成功 `cli-attempt-02`，且日志、原始 JSON、已发布结果和所有哈希一致。后一种同时保存原失败、恢复日志和两次尝试，并明确标注 `recovered_after_infrastructure_failure`。成功的第一次执行不得另有第二次生成。目标 Skill 目录必须还没有输出。脚本先完成全部比对，再新建目标 `outputs.json`；原始 CLI 证据另存 `reused-skill/`，`reuse-provenance.json` 记录来源路径及输入、输出、产物哈希。不会把复用伪装成目标新执行的 CLI job，也不会修改目标 `cli-run.json`。已有复用或任何输出均拒绝覆盖。复用不是新的独立样本。

生成、收集、评审结束后，把原始运行证据保存在可提交的结果目录：

```text
python tests/evals/compare_runs.py archive tests/runs/full-run tests/results/full-run
python tests/evals/compare_runs.py archive tests/runs/competitor-run tests/results/competitor-run
```

归档新建 `cli-evidence/`，保留冻结输入、运行元数据、原始日志、首次失败、恢复计划与结果、
复用来源及已有评审证据，并附文件大小与 SHA-256 清单。已有归档不覆盖。
工具仅复制本次运行的已知证据，不读取宿主认证或配置文件；日志中的本机路径原样保留。
归档不改变失败判定。确认归档完整后可删除对应临时运行目录；下次试验重新准备。

## 匿名 CLI 评审

完成生成并运行 `collect.py` 后，可以用 `judge_cli.py` 评审收集器生成的匿名包：

```text
python tests/evals/judge_cli.py tests/runs/my-run/review tests/results/my-run --executable PATH_TO_CODEX --limit 1
python tests/evals/judge_cli.py tests/runs/my-run/review tests/results/my-run --executable PATH_TO_CODEX --resume
python tests/evals/summarize.py tests/results/my-run
```

此处 `--limit 1` 表示一批评审，最多 12 对。每批使用独立 CLI 上下文，默认 3 个并发、
180 秒超时。评审者只接收 `id`、用户请求、原文、检查要求和匿名 `A` / `B` 完整回答。
执行器不读取 `blind-key.json`、Skill、生成者 notes 或其他批次结果。
检查要求仅在评审阶段可见。

模型分别判断两份回答的事实保留、任务完成和相对原文的表达质量，给出具体证据，再选择 A、B、持平或不确定。硬项失败或不确定的一方不能凭表达偏好胜过硬项通过的一方。代码创建、算术等任务允许将编辑质量标为不适用。不确定项不能计作通过。

`review/judge-cli-run.json` 冻结所有匿名包、prompt、评审执行器、共享 CLI 实现和 schema 的哈希。每批原始材料、prompt、完整日志、最终 JSON、usage、退出码与首次失败记录保存在 `review/cli-judgments/batch-NN/attempt-01/`。模型返回 `{"judgments": [...]}`；只有全部批次完整有效时，执行器才在结果目录新建兼容 `summarize.py` 的 `judgments.json` 数组。不会发布缺题的部分结果。

恢复时重新校验全部输入和已完成产物；失败或损坏的首次尝试必须保留。再次试验使用新评审目录，不能覆盖原始评审。已有 `judgments.json` 仅能在恢复时核对一致，不能覆盖改判。需要裁决争议时，保留原判，在单独材料中说明依据。

生成和评审沿用同一宿主模型配置，因此即使上下文独立，也仅有单模型家族的证据，
仍需母语人工校准。工具调用由任务约束和日志审计限制，未被物理禁用。
CLI 权限、认证及状态库处理沿用上文约束。

评审执行器复用同一日志审计函数；上述已知配置诊断同样逐条保留，未知错误仍拒绝。任何执行器修改都会改变运行哈希，新版本只能在新的运行目录开始；已有首轮失败和快照保持原样。

评审同样直接保存输出流，并在首次执行失败后停止启动剩余批次。已启动批次继续保留结果；未启动批次标为 `not_started`，全部批次未完成时不发布 `judgments.json`。
