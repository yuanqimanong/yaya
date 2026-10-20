# 交付说明

已完成三项请求。

| 文件 | 实际修改 |
| --- | --- |
| `report.md` | 仅润色“收入说明”：将“同比”写成“比去年同季”，解释毛利率，并明确从21%升至22%是提高1个百分点。保留860万元、6%、尚未完成交付、款项暂未计入收入，以及下月交付仍属预计、具体日期未定。 |
| `metrics.py` | 只把第3行普通注释改为“判断 value 是否大于或等于 10。”，去掉无依据的效率评价。 |
| `styles/plain.md` | 新建可复用风格提示词，提炼短句、直接说明问题、给出相关例子、明确缺少的信息等表达习惯，包含使用边界和小例子。 |

`styles/existing.md` 保留原样。文风说明只是根据短样本提炼的暂定偏好，没有修改全局指令或创建新技能。

## 实际工具检查

- 使用快照中的 `scripts/packs.py resolve --language zh-Hans --project <本工作目录>`：返回 `status: ready`、`resolved: zh-Hans`、`source: bundled`。已读取返回的简体中文指南；该指南标记为实验性。
- 修改前保存原文件，先生成注释候选文件，再运行快照中的 `scripts/check_comments.py BEFORE AFTER`。候选文件和最终写入的 `metrics.py` 均返回 `status: passed`、退出码0，`changed_comment_lines: [3]`、`violations: []`。
- 用 Python 字节比较确认：“收入说明”之前及“接口说明”开始之后的报告内容均与原文件一致；`styles/existing.md` 与原文件逐字节一致。
- 用 SHA-256 核对原始备份与修改前基线一致，`request.md` 未变；确认最终 `metrics.py` 与已检查候选文件逐字节一致。
- 以 UTF-8 读取并查看三个交付文件及已有风格文件。核对收入数字、同比口径、百分点表述、交付状态和不确定性；核对注释与 `return value >= 10` 一致，docstring、`# noqa: PLR2004`、字符串和程序语句均未改动。
- 检查 `styles/plain.md` 可正常读取，包含可替换的 `{待处理内容}`、风格边界和示例。

机器检查结果保存在 `.yaya-backup/checks.json`，修改前哈希保存在 `.yaya-backup/baseline.json`。注释检查确认的是修改范围和语法可解析性；未执行额外业务测试，未对财务数据做外部审计。

## 回滚

原始文件保存在 `.yaya-backup/report.md`、`.yaya-backup/metrics.py` 和 `.yaya-backup/styles/existing.md`。需要撤销本次编辑时，用对应备份恢复 `report.md`、`metrics.py`；撤销新风格时移除 `styles/plain.md`。恢复前先确认交付文件没有后续编辑，以免覆盖新内容。
