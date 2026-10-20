# 文件编辑与保存风格：独立端到端执行

结论：已使用冻结版 `core/yaya/SKILL.md` 实际完成 integration 请求中的三项文件操作，并执行一个 X002 式章节限定请求。结果通过工具检查、字节边界检查及保存后复验；本轮未发现需修改核心的问题。

最小可复现证据已从被 Git 忽略的运行目录保存至 [file-integration/](file-integration/)，包含 before/after、请求、diff、原始检查输出、核心哈希、manifest 和验证脚本。未复制冗余核心源码。历史命令输出中的原运行路径保持原样，以保留执行证据。

没有改动核心源码或原始 integration fixtures，没有查看历史生成 outputs/报告或场景 checks。X002 仅提取 `id`、`language`、`request`、`input`。

## 实际执行的请求

| 请求 | 实际文件操作 | 结果 |
| --- | --- | --- |
| 仅润色“收入说明” | [report.md](file-integration/after/report.md) 的一个正文段落，解释毛利率，保留数字及交付状态 | 完成 |
| 优化普通 Python 注释 | [metrics.py](file-integration/after/metrics.py) 仅修改一条普通注释为“判断 value 是否大于或等于 10。” | 完成 |
| 学习并保存风格 | 创建 [styles/plain.md](file-integration/after/styles/plain.md)，包括适用场景、可复制提示词、标明虚构的小例子及短样稿限制 | 完成 |
| X002 式章节限定 | [scoped-overview.md](file-integration/after/scoped-overview.md) 仅改 Overview；完整文档作为结果保留 | 完成 |

integration 输入目录没有实际提供 `styles/existing.md`。测试开始时在隔离目录建立了一份有独立内容的哨兵风格文件，并保留 [原始字节](file-integration/before/styles/existing.md)。新风格使用创建模式写入独立文件，[已有风格](file-integration/after/styles/existing.md) 未被覆盖。原请求保存在 [request.md](file-integration/request.md)，限定章节请求保存在 [x002-input-request.json](file-integration/x002-input-request.json)。

实际执行顺序为：读输入及按需指导 → 解析中文/英文语言包 → 保存原稿 → 准备候选 → 运行真实检查工具并检查语义及字节边界 → 写入实际文件 → 对保存后的文件再次运行真实工具。

## 实际工具结果

候选及实际保存文件分别运行一次，共 6 次检查，均 `status=passed`、退出码 0，stderr 为空。

```powershell
python -B core/yaya/scripts/check_rewrite.py tests/results/2026-10-20-upgrade/file-integration/before/report.md tests/results/2026-10-20-upgrade/file-integration/after/report.md
python -B core/yaya/scripts/check_comments.py tests/results/2026-10-20-upgrade/file-integration/before/metrics.py tests/results/2026-10-20-upgrade/file-integration/after/metrics.py
python -B core/yaya/scripts/check_rewrite.py tests/results/2026-10-20-upgrade/file-integration/before/scoped-overview.md tests/results/2026-10-20-upgrade/file-integration/after/scoped-overview.md
```

机器可读证据：

- [candidate-validation.json](file-integration/candidate-validation.json)：实际 argv、退出码、完整 JSON、stderr、14 项候选边界检查及受保护区域哈希。
- [saved-validation.json](file-integration/saved-validation.json)：实际保存文件的工具结果及 13 项保存核验。
- [save-result.json](file-integration/save-result.json)：写入的实际文件及哈希。
- [resolve-zh-Hans.json](file-integration/resolve-zh-Hans.json)、[resolve-en.json](file-integration/resolve-en.json)：本次真实语言包解析命令及 ready 结果。
- [manifest.json](file-integration/manifest.json)：保留证据的来源、大小和 SHA-256。

可重复验证保存结果：

```powershell
python -B tests/results/2026-10-20-upgrade/file-integration/verify.py
```

迁移后的文件哈希、范围边界及三次真实工具重跑均通过，结果保存在 [retained-verification.json](file-integration/retained-verification.json)。

## 范围与内容核验

所有独立检查为 true：

- `report.md` 的目标章节之前字节未变，从“接口说明”标题起至文件末尾的每个字节未变，所有标题字节未变。
- `scoped-overview.md` 的 Overview 之前及 `## API` 起的每个字节未变，所有标题字节未变。
- Python AST、所有非注释 token 值相同；docstring、`# noqa: PLR2004` 所在整行及 `LABEL` 字符串所在整行字节相同；恰好一条普通注释变化。
- `styles/existing.md` 与原始哨兵文件逐字节相同。
- 实际保存文件与已检查候选、after 快照相同；X002 response 是完整保存文档；原始 integration 三份 fixtures 未变。

受保护尾部的 before/after SHA-256 相同：

| 区域 | SHA-256 |
| --- | --- |
| report 从“接口说明”起 | `d72afca9662a5f6124250203c3ab50aa174f8af3c5505ae1abbce075c2f4f1d9` |
| scoped-overview 从 API 起 | `ebb6adc74d3361b8557204a23219fc45763fcc1098b876e198ceadcba05e317b` |
| 已有 style 全文件 | `e068d9ccb40a877aed3bc3b48987c9fe2218088518b8667ca71a5ee0df1e6269` |

模型语义复核确认保留了：本季度、860万元、同比6%、毛利率21%至22%、未完成交付、相关款项暂未计入收入、预计下月但日期未定。没有把比率变化改成增幅或增加审计结论。

英文结果为：

> The tool exports shared notes as CSV. For now, this feature is available only to trial accounts.

模型语义复核确认：共享笔记、CSV、目前仅试用账号可用的功能限制均保留。限制仍指该功能，没有扩展到整个工具。机械 passed 未被用来替代这一步语义复核；这不构成人类编辑审核。

## 使用的核心快照

[core-snapshot.json](file-integration/core-snapshot.json) 保存本次 SKILL、编辑指导和检查工具的哈希，不在证据目录重复保存核心内容。

| 文件 | 本次使用的 SHA-256 |
| --- | --- |
| `core/yaya/SKILL.md` | `b421b42b2888e97790aeb77f39ac723fa152245202879113042068e5bf18d901` |
| `core/yaya/scripts/check_comments.py` | `b9bdeeeffcd607eba23364d2aebaca731931499165c198aec67c0188082e3539` |
| `core/yaya/scripts/check_rewrite.py` | `c5789b5571a38d81930e90284c7154a461bd59ed425efb884359fcf9b6f09b4c` |
| `core/yaya/scripts/prose_scan.py` | `273b5d879a909721f8bf6f914a3e9303dbf0b3f54b67567d00651e9ec74ea596` |

上述 SKILL、编辑参考和检查脚本在本次执行前后没有变化。执行期间仅观测到 `packs.py` 因并行的语言包单一规范调整而改变；当时解析出的 bundled 中文 GUIDE、英文 PATTERNS 已读取并记录哈希，ready 输出也保留原样。早先的 resolver 输出不作为调整后规范的验收证据；当前发行物与 schema 的独立验收见下节。

原稿在 [before/](file-integration/before/)，落盘结果在 [after/](file-integration/after/)，统一差异在 [recoverable.diff](file-integration/recoverable.diff)。需要回退时，仅用对应 before 副本恢复隔离目录内的文件即可；风格新增文件可单独移除，不影响 existing 风格。

## 当前 0.2.0 发行物与单一 schema 独立验收

只读核对当前 dist，结果全部通过：

| 核对项 | 实际结果 |
| --- | --- |
| 核心 ZIP 与当前 core 源码 | 文件集合一致，26 个文件的 SHA-256 逐一相同 |
| ja、ko、zh-Hant 三个语言 ZIP | 每个均为 flat，5 个成员直接位于根目录；format_version 为 1；与对应来源文件字节相同 |
| schema | 仅有 `schemas/language-pack.schema.json`，format_version 限定为 1 |
| 六份 metadata | en、zh-Hans、ja、ko、zh-Hant、模板 fr，全部通过同一 Draft 2020-12 schema |
| SHA256SUMS | 四个 ZIP 均与清单相符 |

核心 ZIP SHA-256：`f1f5c3e317917e268e1a0e463a84f14bbcec2ff48a49f0ab6449f126e9ad4101`。

验证只使用现有 `.tmp/validation-deps` 中的 jsonschema 作为测试依赖；没有安装新依赖或修改产品代码。完整逐文件哈希、六份 metadata 结果及依赖路径记录在 [release-verification.json](file-integration/release-verification.json)。

```powershell
python -B tests/results/2026-10-20-upgrade/file-integration/verify_release.py
```
