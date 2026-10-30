# 升级到 Yaya 0.5

0.5.0 整合 0.4.0 之后的 30 轮改进，每轮保留独立 PR 和验证记录。
从 `main` 分支获取核心源码；尚未发布 GitHub Release。本机安装版本需单独检查。
完整变更和证据见 [迭代台账](../tests/results/2026-10-30-iterations30/README.md)。

## 可以直接使用的变化

| 功能 | 用法 | 范围 |
| --- | --- | --- |
| 本地诊断 | `$yaya doctor --json` | 检查安装结构与语法，不自动修复 |
| 字面扫描 | `$yaya scan --file draft.md --lang en --rule en-stock-close` | 可限定规则，定位候选并记录输入版本 |
| 复用风格 | `$yaya polish --style team-style.md --file draft.md` | 卡作为表达指导，草稿是编辑对象 |
| 选择核对来源 | `$yaya verify --file claims.md --source evidence.md` | 主张、来源分开，均只读 |
| 保护术语与引文 | `$yaya check --before old.md --after new.md --literal API_KEY --quotes` | 检查原样保留，不核定语义 |

技术和金融领域优先验证，同时保留数据分析、学术和商务规则。
过度防御表达仍由 `human --focus direct` 或 `review --focus direct` 处理；
必要条件、实际风险、归因和不确定性继续保留。五领域质量标签仍为 `experimental`。

## 兼容性与行为变化

- 核心仍为标准库 Python 3.10+，语言包仍使用 `format_version: 1`、`core_major: 0`。
  可选繁体中文、日语、韩语包不需要因本次核心升级而重装。
- `check` 的文件参数不再接受单独的 `-`；真实文件名为 `-` 时使用 `./-`。
  专用检查器仍可接收 stdin，并标记无法绑定稳定文件的限制。
- 新增保护项可能让以前的机械通过变为失败。先检查具体差异，确认需要改动后再给
  与两版文件摘要及实际差异绑定的授权；不要整类放行。
- 新评测执行器拒绝不完整文件集、非有限超时、重复 JSON 字段和未知事件。
  runner 哈希变化后应准备新运行，旧输出与失败记录保留，不强行续跑旧证据。
- `scan` 只覆盖中英有限字面规则；不判断作者、模型品牌或“AI 概率”。
  `doctor` 就绪不代表编辑质量、所有格式兼容或宿主自动发现成功。

## 升级与回滚

按 [INSTALL.md](../INSTALL.md) 从选定提交构建核心 ZIP，核对 catalog 中的 SHA-256，
在独立目录解压并检查文件。备份现有安装到宿主发现目录之外；若存在用户定制，先比较，
不要覆盖不明修改。替换完整核心目录，保留外部语言包和风格卡。

从安装目录执行：

```text
python scripts/yaya.py --version --json
python scripts/yaya.py doctor --json
python scripts/yaya.py scan --help
python scripts/yaya.py check --help
```

版本应为 0.5.0，诊断应为 `ready`。再由宿主选择技能，完成一条短文本任务，
确认发现与调用路径。单独读取 SKILL.md 或运行 Python 助手不能证明宿主已刷新技能列表。

需要回滚时，核对当前文件是否有升级后的修改；备份新修改后，从旧备份恢复已升级文件，
仅移除本次新增且未被修改的运行文件。重跑旧版版本检查和相关检查器。
本批本机安装收据、隔离回滚演练与验证限制见 [交付验收](../tests/results/2026-10-30-iterations30/release-050/README.md)。
