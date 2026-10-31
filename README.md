# Yaya · 牙牙学语

[English](README.en.md) · [完整用法](docs/usage.md) · [安装与更新](INSTALL.md)

Yaya 是给 AI 助手使用的写作编辑 Skill。它能去 AI 味、润色文档、核对事实、整理代码注释、优化提示词、学习样稿风格，也能评估一段文字是否有 AI 写作迹象。

编辑由当前 AI 助手完成；本地 Python 工具负责命令解析、扫描和保护检查。无需另配模型账号、API Key 或后台服务。核心版本为 **0.5.0**，源码在 `main`；目前尚未发布 GitHub Release。

## 开始使用

将这句话发给支持 Skill 安装的 AI 助手：

> 阅读 https://github.com/yuanqimanong/yaya/blob/main/INSTALL.md，从 main 分支安装默认中英核心。

安装后在聊天中输入：

```text
$yaya --help
$yaya human --domain tech --file README.md
$yaya origin -- 这里粘贴需要判断来源的文字。
```

第二条返回改稿；需要直接修改文件时加 `--write`。也可以自然描述：“用 Yaya 给这份 README 去 AI 味，按技术文档润色，直接修改文件。”

`$yaya` 和 `yaya` 是聊天中的任务入口。安装不会向终端 PATH 添加全局命令。终端查看帮助使用：

```text
python core/yaya/scripts/yaya.py --help
```

以上路径从源码仓库根目录运行；在已安装的 `yaya/` 目录中，去掉 `core/yaya/`。文件路径需让当前 AI 助手可访问。详见[调用方式与文件规则](docs/usage.md#start)。

## 都能做什么

| 需求 | 命令 | 结果与详细用法 |
| --- | --- | --- |
| 去 AI 味 | `human` | 改写套话、空泛铺垫、机械重复和过度防御表达；[用法](docs/usage.md#human) |
| 润色正文 | `polish` | 按读者、语气和领域改善表达与结构；[用法](docs/usage.md#polish) |
| 只审不改 | `review` | 给出原句、问题和建议；[用法](docs/usage.md#review) |
| 核对事实 | `verify` | 根据代码或提供的来源列出证据与未确认项；[用法](docs/usage.md#verify) |
| 整理代码注释 | `comment` | 结合附近代码改普通注释，docstring 可单独指定；[用法](docs/usage.md#comment) |
| 优化提示词 | `prompt` | 整理提示词措辞，或调整下游回答风格；[用法](docs/usage.md#prompt) |
| 学习样稿风格 | `style` | 提炼可保存、复用的风格卡；[用法](docs/usage.md#style) |
| 判断是否有 AI 写作迹象 | `origin` | 给出来源倾向、片段依据和不确定项；[用法](docs/usage.md#origin) |
| 本地措辞扫描 | `scan` | 按有限字面规则定位中英文候选；[用法](docs/usage.md#scan) |
| 比较原稿与改稿 | `check` | 检查受保护内容或 Python 普通注释边界；[用法](docs/usage.md#check) |
| 检查安装 | `doctor` | 检查本地运行文件、语法和资源；[用法](docs/usage.md#doctor) |

每条显式命令只做表中选定任务。自然语言可以组合任务，例如“先核对部署说明，再润色已确认的部分”。完整参数、默认值、输入输出和例子见[使用手册](docs/usage.md)。

## 判断一段文字是不是 AI 写的

这项能力使用 `origin`：

```text
$yaya origin --file article.md
$yaya origin --file article.md --file revision-history.md
$yaya help origin
```

结果为 **AI 生成倾向、人工写作倾向或无法判断**，并引用具体片段解释依据。评估保留原文；草稿、修改记录或生成记录可以补充来源证据。仅凭文字通常无法认定作者，Yaya 不提供未经校准的“AI 百分比”。[查看完整说明](docs/usage.md#origin)。

## 去掉过度防御的表达

```text
$yaya human --focus direct --domain tech --file draft.md
$yaya review --focus direct --file draft.md
```

`direct` 专门处理无效否定对比、假想反驳和重复限定。例如：

> 改前：这不是要重新定义协作。新版通讯录支持按部门查找联系人。
>
> 改后：新版通讯录支持按部门查找联系人。

影响操作的条件仍需保留，例如“只在连接超时后重试，最多两次”。规则按上下文判断，适用于 GPT、Opus、DeepSeek、豆包等模型产生的文字；目前没有按模型品牌划分的预设。[查看适用范围](docs/usage.md#human)。

## 支持的领域和语言

| 领域 ID | 适合的材料 | 编辑时重点保留 |
| --- | --- | --- |
| `tech` | README、API、运行手册、故障说明、代码注释 | 接口、前置条件、默认值、实际配置、完成状态 |
| `finance` | 财报、经营指标、投资者沟通、已有风险说明 | 币种、期间、指标口径、同比/环比、预测与风险 |
| `data` | 实验、调查、看板、分析报告 | 样本、分母、时间窗、缺失值、相关与因果 |
| `academic` | 摘要、方法、结果、讨论、文献综述 | 研究设计、引用归属、证据强度、局限 |
| `business` | 工作邮件、进展、提案、客户通知 | 责任人、日期、价格、审批、交付条件与承诺 |

```text
$yaya domains
$yaya domains finance
$yaya polish --domain finance --audience 普通读者 --tone 简明 --file report.md
```

领域、读者、语气和语言分别选择。五类领域规则目前均为 `experimental`，具体覆盖与排除项见[领域说明](docs/usage.md#domains)。

核心自带 **简体中文 `zh-Hans` 和英语 `en`**；**繁体中文 `zh-Hant`、日语 `ja`、韩语 `ko`** 按需安装。五个语言包均为实验性指导。`scan` 目前仅有简中和英语字面规则；[语言选择与安装](docs/usage.md#language)。

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [完整用法](docs/usage.md) | 每条命令、全部参数、默认值、输入输出、常见错误 |
| [组合工作流](docs/workflows.md) | 技术核对、金融改稿、风格复用与恢复 |
| [本地工具](docs/local-tools.md) | 终端扫描、保护检查、docstring 授权、批量证据、退出码 |
| [安装与更新](INSTALL.md) | 核心与语言包安装、校验、升级、卸载和回滚 |
| [0.5 升级说明](docs/upgrade-0.5.md) | 当前版本变化与兼容性 |
| [设计](docs/design.md) / [贡献](CONTRIBUTING.md) | 模块职责、扩展方式、开发检查 |
| [测试与评测](tests/README.md) | 脚本回归、写作评测和执行证据 |
| [语言包规范](docs/language-pack-spec.md) | 包格式、解析规则和新语言贡献 |

开发检查从仓库根目录运行，需要 Python 3.10+：

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
```

构建输出位于 `dist/`，本地工具仅使用 Python 标准库。文件编辑保留可恢复原稿或 diff；机械检查之后仍需核对原意与阅读效果。

[MIT License](LICENSE)
