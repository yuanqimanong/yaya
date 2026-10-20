# 指导修正后的发布物复核

2026-10-20；Windows / CPython 3.13.5。范围仅为两份编辑指导修正后的结构、包格式、归档内容和加载体积；本次没有运行真实模型，不评价 H019 是否已修复。

| 检查 | 实际结果 |
| --- | --- |
| Skill `quick_validate.py` | 通过；PyYAML 使用现有 `.tmp/validation-deps`，未增加产品运行依赖 |
| `test_release.py` | 14 个测试方法，0 失败、0 错误；1 个方法内的 3 个符号链接子用例因 Windows 权限不足跳过；测试报告用时 8.016 秒 |
| 重建 `dist/` | 成功，生成核心 ZIP、3 个语言 ZIP、`catalog.json` 和 `SHA256SUMS` |
| 逐文件 SHA-256 | 核心 26 个文件、可选包共 15 个文件，全部与当前源码逐字节一致 |
| 包规范 | 唯一 `format_version: 1` schema；5 个实际包和 1 个模板的 metadata 通过；5 个实际包目录通过本地完整校验 |
| 发布索引 | 4 个归档的大小、SHA-256 与 catalog、SHA256SUMS 一致；三个可选语言 ZIP 的字节未变 |
| 修正范围 | 新旧核心 ZIP 文件集相同，仅 `references/humanize.md` 和 `languages/zh-Hans/PATTERNS.md` 内容变化 |
| 历史证据 | 原 `context-cost.json`、`file-integration/release-verification.json` 及 3 个修正前备份的 SHA-256 均未变 |

当前 `yaya-core-0.2.0.zip` 为 **43,017 bytes**，SHA-256：

```text
ee912ab878e4d557189ba8c5c9abf08e369455dcfcb4d5abbeba0659a24a291a
```

修正前核心的 SHA-256 为 `f1f5c3e317917e268e1a0e463a84f14bbcec2ff48a49f0ab6449f126e9ad4101`。当前仍为未发布的 `0.2.0`；使用时须匹配当前 catalog 和校验值，不能仅凭文件名区分两份归档。

## 加载体积

口径沿用原记录：完整入口 + 一份任务指导 + 一份语言专项/指南，统计 UTF-8 文件字节，**不是模型 token 数**。不包含用户输入、宿主提示词、工具输出或额外指南。

| 去 AI 味语言 | 修正前 bytes | 当前 bytes | 增量 |
| --- | ---: | ---: | ---: |
| `en` | 10,245 | 10,349 | +104 |
| `zh-Hans` | 9,940 | 10,098 | +158 |
| `zh-Hant` | 9,203 | 9,307 | +104 |
| `ja` | 9,691 | 9,795 | +104 |
| `ko` | 9,802 | 9,906 | +104 |

其余 20 个任务/语言组合体积未变。`humanize.md` 增加 104 bytes，简中 `PATTERNS.md` 增加 54 bytes。

原始输出：[结构校验](quick-validate-refinement.json)、[发布测试](test-release-refinement.json)、[构建](build-release-refinement.json)。完整逐文件证据见 [release-refinement.json](release-refinement.json)，25 项体积记录见 [context-cost-refinement.json](context-cost-refinement.json)，核对脚本见 [verify-refinement.py](verify-refinement.py)。

修正前核心 ZIP 与两份指南保留在 `.tmp/pre-refinement-0.2/`。需要回滚时，恢复两份指南后重新构建，使核心 ZIP、catalog 和 SHA256SUMS 保持一致。旧报告保留其当时证据，不代表当前发行物的哈希或当前语言质量。
