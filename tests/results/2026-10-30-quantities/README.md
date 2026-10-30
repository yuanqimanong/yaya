# 0.3.2 数量表达保真验证

日期：2026-10-30。本轮修复正文检查器对币种、数量级、科学计数法和常用单位变化的漏检。
保留原有命令与编辑范围，检查仍按字面表达及出现次数比较。

## 修复前后

| 原稿 → 错误候选 | 0.3.1 | 最终 0.3.2 |
| --- | --- | --- |
| `USD 5 million` → `EUR 5 billion` | passed，漏检 | failed，检出 |
| `1e-3` → `1e+3` | passed，漏检 | failed，检出 |
| `1e3` → `9e3` | passed，漏检 | failed，检出 |
| `3 个百分点` → `3 个基点` | passed，漏检 | failed，检出 |
| `8 MiB` → `8 GiB` | passed，漏检 | failed，检出 |
| `500 万美元` → `500 万欧元` | passed，漏检 | failed，检出 |
| 精简 `USD 5 million` 前的普通铺垫，数量不变 | passed | passed |

完整输入与工具返回：[修复前](probes-before.json)、[修复后](probes-after.json)。
六个复现场景均实际执行，并保留旧版源码；此结果仅说明这些场景，不是通用准确率。

## 回归与修订

- 新增 10 个测试方法，覆盖币种与数量级、科学计数法、单位、普通措辞、列表转换、
  保护区、重复数量、精确授权、已知语义边界及长输入。
- 新测试在旧版执行时记录 27 个失败和 1 个错误；错误来自旧版未报告数量变化，
  导致精确授权测试取不到差异。原始日志保留，不算作模型失败。
- 首版实现通过新增测试后，额外复现了列表符号误报：`- USD 5 million` 的列表标记
  被当成负号。已限制符号与数量的相邻关系，补充正负对照；[原误报](bullet-regression-before.json)
  与[修正后](bullet-regression-after.json)均保留。
- 最终全量运行 **241 个测试方法，0 failure、0 error**。跳过记录 8 条：
  1 个方法需要 Python 3.14，4 个方法需要当前不可用的目录链接，另有 3 个符号链接子测试
  受 Windows 权限限制。见[完整统计](unittest.json)。
- Skill 结构校验与最终构建成功。

## 实际文件编辑

独立执行者仅收到 Skill 快照和两个文件编辑请求，没有看到预期答案或缺陷描述。
两题共享一个新的上下文，模型精确修订及完整设置不可得。

- `human --domain finance --write`：删去提醒式铺垫，保留当季 USD 5 million、下季
  EUR 6 million 预测、3 个百分点及各自审计限定。
- `polish --domain tech --write`：精简开头，保留 8 MiB、1e-3、仅缓解超时及连接泄漏尚未修复。

两份文件都实际编辑、保留原稿、执行检查；主代理检查了完整差异和语义关系。
执行者先读取输入再生成选择器计划，所有改动发生在有效计划之后；本次不作为命令读取顺序
的完整合规证明。隔离要求阻止读取外围 Git 元数据，执行者如实记录 Git 基线未验证。

文件执行使用了修复列表符号前的快照。最终源码对同一原稿/候选再次执行检查，两份均 passed，
输入及候选摘要绑定一致。见[完整结果摘要](file-results.json)和[最终检查记录](file-verification.json)。
没有开展跨模型比较或外部事实审计。

## 安装、证据与回滚

已安装到 `C:/Users/12761/.agents/skills/yaya`，41 个运行文件与最终源码一致。
安装后实际验证帮助、定向命令、只读写入拒绝，以及错误数量候选返回 1、正常精简返回 0。
这些检查均未改动输入。见[安装记录](installation.json)。

核心 ZIP：`dist/yaya-core-0.3.2.zip`；SHA-256：
`4bb71c0e2291cb8c2faa08ffb55cb330eb7cf8850d6803c537f6725641541484`。

[完整证据包](execution-evidence.zip)包含旧版与最终源码、文件执行快照、请求、输出、
工具报告和失败日志，共 157 个成员，全部回读核对。其 SHA-256：
`f4d2dd32d5d0621923fb9caa1ec688186cbfe7a0fc65526bad8a138fe4d4e9c7`。
另见[逐文件摘要](archive-index.json)、[最终运行摘要](runtime-sha256.json)和[总览](summary.json)。

本机备份 `.yaya/quantities-20261030/` 保存本轮开始时的 **0.3.1**，保留此前所有未提交成果。
恢复脚本先核对当前与备份摘要，拒绝覆盖后来修改。源码及安装恢复已在隔离副本实际验证，
本机当前仍为 0.3.2。见[回滚验证](recovery-validation.json)。

在仓库根目录预演，确认后应用：

```text
python .yaya/quantities-20261030/restore.py --scope installed
python .yaya/quantities-20261030/restore.py --scope installed --apply
```

恢复本轮源码及对应文档/产物使用 `--scope source`。恢复依赖本机上述备份目录。

数字与对象互换、未列单位、拼写数字、逗号小数及跨行单位标签仍需语义复核；
完整覆盖边界见[数量检查说明](../../../core/yaya/references/validation.md#quantities-in-prose)。
