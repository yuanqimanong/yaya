# Yaya 本地工具手册

[使用手册](usage.md) · [安装与更新](../INSTALL.md) · [保护范围与授权格式](../core/yaya/references/validation.md)

以下命令从源码仓库根目录运行，需要 Python 3.10+，仅使用标准库。在已安装的 `yaya/` 目录运行时，
去掉路径前的 `core/yaya/`。示例文件名与大写占位符需替换为实际路径或值。

## execution

`yaya.py` 的任务命令输出供宿主执行的计划。`detect_tells.py`、`check_rewrite.py` 等专用工具才直接检查文件。
`doctor` 可通过任一入口直接运行：

```text
python core/yaya/scripts/yaya.py --help
python core/yaya/scripts/yaya.py --version --json
python core/yaya/scripts/yaya.py doctor --json
python core/yaya/scripts/doctor.py
```

诊断不读取待编辑材料，不修复安装。`doctor.py` 始终输出 JSON，`--json` 是兼容开关。

## scan

```text
python core/yaya/scripts/detect_tells.py draft.md --language zh-Hans
python core/yaya/scripts/detect_tells.py draft.md --language en --rule en-stock-close --fail-on P2
```

| 参数 | 行为 |
| --- | --- |
| `file` | UTF-8 文件；省略或给 `-` 时从 stdin 读取。 |
| `--language` | 必填，`en` 或 `zh-Hans`。 |
| `--rule ID` | 可重复，限定同语言规则；不填运行该语言全部规则，见[规则表](usage.md#scan)。 |
| `--fail-on P1\|P2` | 可选失败阈值；P1 只对 P1 候选退出 1，P2 对 P1/P2 候选退出 1。默认有候选也可退出 0。 |
| `--json` | 兼容开关，工具始终输出 JSON。 |

`findings` 包含位置和审阅提示，`enabled_rules` 列实际规则；`evidence` 记录输入摘要和稳定性。
stdin 的 `input_stable` 为 `null`，没有稳定文件身份。文件改变后应重扫。
候选需要语境判断，扫描不产出改稿或作者概率。支持的 Markdown 代码、表格、引文等片段被排除。

## rewrite

```text
python core/yaya/scripts/check_rewrite.py original.md candidate.md
python core/yaya/scripts/check_rewrite.py original.md candidate.md --protect-literal retry_limit --protect-literal EBITDA --protect-quotes
```

| 参数 | 行为 |
| --- | --- |
| `before` / `after` | 原稿与候选，均只读；可用 `-` 读 stdin，但不能获得稳定的文件绑定证据。 |
| `--protect-literal TEXT` | 可重复；保护原稿中指定片段的拼写和出现次数。 |
| `--protect-quotes` | 额外保护成对双引号、弯引号和中日韩引文。 |
| `--allow PATH` | 已审阅的具体差异授权 JSON；绑定两版文件哈希和完整差异。 |
| `--language TAG` | 仅记录元数据，不改变机械保护规则。 |
| `--json` | 兼容开关，工具始终输出 JSON。 |

两份输入中最多一份可从标准输入读取。每个输入最多 2 MiB，须为 UTF-8。保护项包含支持的代码片段、链接及图片角色、表格、占位符、任务状态、
部分公式、数字、币种、单位、日期时间、范围和比例。完整边界见[验证说明](../core/yaya/references/validation.md)。
缩进代码块、脚注、多行链接、原始 HTML 等部分结构会返回 `unsupported`；工具只实现 Markdown 子集。

用户明确要求改变受保护内容时，先核对请求与实际差异，再准备 `--allow`。按[授权格式](../core/yaya/references/validation.md#exact-grants)
记录文件 SHA-256 与具体 `changes`，保存后执行：

```text
python core/yaya/scripts/check_rewrite.py original.md candidate.md --allow approved-changes.json
```

`--allow numbers` 这类整类放行无效。候选、原稿或差异变化后，旧授权不能复用。
检查通过后仍需对照数字属于谁、条件是否改变、引用是否仍支持结论。

## comments

```text
python core/yaya/scripts/check_comments.py original.py candidate.py
```

这个工具只接受两个位置参数，没有通用选项。原稿扩展名需为 `.py` 或 `.pyi`，候选可用临时文件名；
源文件须能被当前 Python 解释器解析。

允许改变普通 `#` 注释中的文字，保护代码、字符串、docstring、换行、编码与已识别工具指令。
增删、移动或重新折行注释超出支持范围。其他语言需要相应检查工具；注释是否准确仍须结合代码阅读。

## docstrings

docstring 属于运行时字符串。先明确要改的节点，再列出原稿中的精确选择器：

```text
python core/yaya/scripts/check_docstrings.py --inventory original.py
```

结果列出所属节点、原始行号和字面量哈希，选择器如 `C.method@12`。为选定节点准备候选，
按[授权格式](../core/yaya/references/validation.md#exact-grants)保存 `schema`、原稿/候选 SHA-256，
以及 `docstrings` 中每个节点和前后字面量哈希，然后运行：

```text
python core/yaya/scripts/check_docstrings.py original.py candidate.py --allow approved-docstrings.json
```

| 参数 | 行为 |
| --- | --- |
| `before` | 原始 Python 文件。 |
| `after` | 比较时的候选文件；只列 inventory 时省略。 |
| `--inventory` | 列出可选的现有 docstring 节点。 |
| `--allow PATH` | 与指定节点、原稿和候选绑定的授权记录。 |

仅支持 UTF-8、单个字符串 token 的现有 docstring。节点外的代码、其他字符串和普通注释保持不变；
已识别的示例、doctest 也保持受保护。节点增删、移动、换行重排和通配授权不受支持。
普通注释与 docstring 同时编辑时，需要分别保存中间候选并串联检查，不能用一次检查覆盖混合修改。

## evidence

批量编辑先快照**当前工作树**，再修改。下面假设从仓库根目录运行，`SNAPSHOT_DIRECTORY` 是新的证据目录：

```text
python core/yaya/scripts/edit_evidence.py start . SNAPSHOT_DIRECTORY --target README.md:prose --target README.md:manual --target core/yaya/scripts/yaya.py:comments
python core/yaya/scripts/edit_evidence.py check SNAPSHOT_DIRECTORY --target README.md:prose
python core/yaya/scripts/edit_evidence.py check SNAPSHOT_DIRECTORY --target core/yaya/scripts/yaya.py:comments
python core/yaya/scripts/edit_evidence.py check SNAPSHOT_DIRECTORY --target README.md:manual --disposition accepted --note "Reviewed the changed wording against the command catalog."
python core/yaya/scripts/edit_evidence.py summary SNAPSHOT_DIRECTORY
```

第一条必须在编辑前执行，之后的检查针对编辑后的文件。不要在尚未审阅时照抄人工接受说明。

| 子命令 | 参数与产物 |
| --- | --- |
| `start PROJECT SNAPSHOT` | 重复 `--target PATH:KIND`，保存所选现有文件、Git HEAD/status 与独立差异。PATH 用相对项目的正斜杠路径；KIND 为 `prose`、`comments`、`docstrings` 或 `manual`。 |
| `check SNAPSHOT` | 必填一个已登记的 `--target PATH:KIND`；可提供 `--allow PATH` 给相应检查器，或用 `--disposition` / `--note` 记录人工判断。 |
| `summary SNAPSHOT` | 重新核对快照、候选与工具哈希，汇总证据状态。 |

`--disposition` 接受 `accepted`、`excluded`、`unresolved`，必须配具体 `--note`。
人工说明与 `--allow` 不能混用。人工接受记录为 `manual_review`，不是机械通过；
失败只有修正后重检通过，或有具体依据的 `excluded` 记录才算处理。`accepted` 不会消掉原失败。

报告分别统计 `passed`、`failed`、`unsupported`、`manual_review`、`unverified`。
工具或候选改变会让旧报告过期。只有全部机械通过时 `complete` 才为 true；人工检查需要阅读具体记录。
新增/删除文件、全文重构或混合编辑链另建清单，记录原因和验证，不要自动生成授权来消除差异。
证据助手只向指定证据目录写快照与报告。

## packs

从安装目录查看子命令帮助，例如 `python scripts/packs.py install --help`。
从源码仓库根目录执行的完整接口如下：

```text
python core/yaya/scripts/packs.py validate language-packs/ja
python core/yaya/scripts/packs.py resolve --language ja
python core/yaya/scripts/packs.py list
python core/yaya/scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256
python core/yaya/scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256 --replace
python core/yaya/scripts/packs.py remove ja
python core/yaya/scripts/packs.py rollback ja
```

| 子命令 | 参数 |
| --- | --- |
| `validate` | 包目录路径，检查内容和元数据。 |
| `resolve` | 必填 `--language TAG`；可选 `--project ROOT`、`--data-dir DIRECTORY`。 |
| `list` | 可选 `--project ROOT`、`--data-dir DIRECTORY`，列出所选位置的包。 |
| `install` | 归档路径与必填 `--sha256`；已有不同内容时需 `--replace`；目标用 `--project` 或 `--data-dir`。 |
| `remove` / `rollback` | 包 ID；目标用 `--project` 或 `--data-dir`。 |

默认用户数据目录为 `HOME/.yaya/`，项目目标为 `PROJECT_ROOT/.yaya/`。
`--data-dir` 指数据根目录本身，不是其 `language-packs/` 子目录。
修改操作的两个目标参数互斥；查询可同时指定显式项目和自定义用户数据目录，仍按项目优先解析。
安装、移除和恢复按数据目录串行执行。备份及异常恢复见[安装指南](../INSTALL.md#4-update-remove-or-roll-back)。

## exits

| 工具 | 退出 0 | 退出 1 | 退出 2 |
| --- | --- | --- | --- |
| `yaya.py` | 帮助/计划成功，或 doctor 就绪 | doctor 为 degraded | 参数或输入错误 |
| `doctor.py` | ready | degraded | 调用错误 |
| `detect_tells.py` | 扫描完成，未触发指定阈值 | 命中显式失败阈值 | 错误或不支持 |
| `check_rewrite.py` | 已执行保护项通过 | 存在未授权差异 | 错误或不支持 |
| `check_comments.py` / `check_docstrings.py` | 机械范围通过 | 范围检查失败 | 不支持或调用错误 |
| `edit_evidence.py check` | 检查通过 | 检查失败 | 不支持、人工记录或调用错误 |
| `edit_evidence.py summary` | complete 为 true | 尚有其他状态，需读报告 | 调用错误 |
| `packs.py` | 操作完成；解析可能为 ready 或 missing，须读 status | invalid / incompatible 或操作错误 | 命令行参数错误 |

检查结果以工具 JSON 与实际进程退出码为准。脚本参数一般可加 `--help`；普通注释检查器采用上面的两个位置参数接口。
写作行为评测会调用模型，独立于这些本地检查；开发者用法见[评测流程](../tests/evals/README.md)和[CLI 执行说明](../tests/evals/CLI.md)。
