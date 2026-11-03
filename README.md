# Yaya · 牙牙学语

[English](README.en.md) · [完整用法](docs/usage.md) · [安装与更新](INSTALL.md)

Yaya 是装在 AI 助手里使用的写作编辑 Skill。它可以去 AI 味、润色文档、核对事实、整理代码注释、优化提示词、学习样稿风格，也能判断一段文字有没有 AI 写作的迹象。

改稿由你正在用的 AI 助手完成，本地 Python 工具只负责解析命令、扫描措辞和检查受保护的内容，不需要另配模型账号、API Key 或后台服务。当前版本为 **1.0.0**，源码在 `main` 分支，尚未发布 GitHub Release。

## 开始使用

把这句话发给支持安装 Skill 的 AI 助手：

> 阅读 https://github.com/yuanqimanong/yaya/blob/main/INSTALL.md，从 main 分支安装默认中英核心。

装好后在聊天中输入：

```text
$yaya --help
$yaya human --domain tech --file README.md
$yaya origin -- 这里粘贴需要判断来源的文字。
```

第二条返回改好的稿子；要直接改文件，加 `--write`。也可以直接说：“用 Yaya 给这份 README 去 AI 味，按技术文档润色，直接修改文件。”

`$yaya` 和 `yaya` 只在聊天中使用，安装不会往终端的 PATH 里加命令。在终端查看帮助：

```text
python core/yaya/scripts/yaya.py --help
```

这条命令在源码仓库根目录运行；在已安装的 `yaya/` 目录中运行时，去掉 `core/yaya/`。命令里的文件必须放在 AI 助手能访问的位置，见[调用方式与文件规则](docs/usage.md#start)。

## 都能做什么

| 需求 | 命令 | 结果与详细用法 |
| --- | --- | --- |
| 去 AI 味 | `human` | 改写套话、空泛铺垫、机械重复和过度防御的表达；[用法](docs/usage.md#human) |
| 润色正文 | `polish` | 按读者、语气和领域改善表达与结构；[用法](docs/usage.md#polish) |
| 只审不改 | `review` | 列出原句、问题和建议；[用法](docs/usage.md#review) |
| 核对事实 | `verify` | 对照代码或给定来源，列出证据和未确认项；[用法](docs/usage.md#verify) |
| 整理代码注释 | `comment` | 参照附近代码修改普通注释，docstring 需单独指定；[用法](docs/usage.md#comment) |
| 优化提示词 | `prompt` | 整理提示词措辞，或调整下游回答的风格；[用法](docs/usage.md#prompt) |
| 学习样稿风格 | `style` | 提炼可保存、可复用的风格卡；[用法](docs/usage.md#style) |
| 判断是否有 AI 写作迹象 | `origin` | 给出来源倾向、片段依据和不确定项；[用法](docs/usage.md#origin) |
| 本地措辞扫描 | `scan` | 用有限的字面规则定位中英文候选；[用法](docs/usage.md#scan) |
| 比较原稿与改稿 | `check` | 检查受保护内容或 Python 普通注释的边界；[用法](docs/usage.md#check) |
| 检查安装 | `doctor` | 检查本地运行文件、语法和资源；[用法](docs/usage.md#doctor) |

每条命令只做表中对应的一件事。用自然语言可以组合任务，例如“先核对部署说明，再润色已确认的部分”。全部参数、默认值、输入输出和示例见[使用手册](docs/usage.md)。

## 判断一段文字是不是 AI 写的

```text
$yaya origin --file article.md
$yaya origin --file article.md --file revision-history.md
$yaya help origin
```

结果是 **AI 生成倾向、人工写作倾向或无法判断** 之一，并引用原文片段说明依据。评估不改动原文；草稿、修改记录或生成记录可以作为补充证据。单凭文字通常无法认定作者，所以 Yaya 不给未经校准的“AI 百分比”。[完整说明](docs/usage.md#origin)

## 去掉过度防御的表达

```text
$yaya human --focus direct --domain tech --file draft.md
$yaya review --focus direct --file draft.md
```

`direct` 只处理无效的否定对比、假想的反驳和重复的限定。例如：

> 改前：这不是要重新定义协作。新版通讯录支持按部门查找联系人。
>
> 改后：新版通讯录支持按部门查找联系人。

影响操作的条件照样保留，例如“只在连接超时后重试，最多两次”。规则按上下文判断，同样适用于 GPT、Opus、DeepSeek、豆包等模型写出的文字，没有按模型品牌划分的预设。[适用范围](docs/usage.md#human)

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

领域、读者、语气和语言各自独立选择。五个领域目前都是 `experimental`，覆盖范围和排除项见[领域说明](docs/usage.md#domains)。

核心自带 **简体中文 `zh-Hans`** 和 **英语 `en`**。其他语言按需安装：

| 语言 | ID | 语言 | ID |
| --- | --- | --- | --- |
| 繁体中文（台湾） | `zh-Hant-TW` | 西班牙语 | `es` |
| 繁体中文（香港） | `zh-Hant-HK` | 巴西葡萄牙语 | `pt-BR` |
| 日语 | `ja` | 俄语 | `ru` |
| 韩语 | `ko` | 阿拉伯语（从右到左） | `ar` |
| 法语 | `fr` | | |

台湾和香港的用词、字形和语体不同，所以分成两个包，互不替代；`zh-MO` 使用香港包。所有语言包都是实验性的编辑指导。`scan` 的字面规则只有简体中文和英语。[语言选择与安装](docs/usage.md#language)

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [完整用法](docs/usage.md) | 每条命令的参数、默认值、输入输出和常见错误 |
| [组合工作流](docs/workflows.md) | 技术核对、金融改稿、风格复用与恢复 |
| [本地工具](docs/local-tools.md) | 终端扫描、保护检查、docstring 授权、批量证据、退出码 |
| [安装与更新](INSTALL.md) | 核心与语言包的安装、校验、更新、卸载和回滚 |
| [设计](docs/design.md) / [贡献](CONTRIBUTING.md) | 模块职责、扩展方式、开发检查 |
| [测试](tests/README.md) | 本地脚本与发布构建的单元测试 |
| [语言包规范](docs/language-pack-spec.md) | 包格式、解析规则和新语言贡献 |

开发检查在仓库根目录运行，需要 Python 3.10+：

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
```

构建结果写入 `dist/`。本地工具只用 Python 标准库。改文件时保留可恢复的原稿或 diff；机械检查通过后，仍要核对原意和读感。

[MIT License](LICENSE)
