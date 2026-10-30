# yaya · 牙牙学语

[English](README.en.md) · [安装](INSTALL.md) · [贡献语言包](CONTRIBUTING.md) · [包规范](docs/language-pack-spec.md)

yaya 是一个编辑 Skill，用你当前的 AI 工具润色正文、核对工程注释、优化提示词和学习样稿风格。可以改写、只审不改，或编辑文件中的指定部分；保留原意、作者口吻和关键约束。

默认包含简体中文和英语，繁中、日语、韩语按需安装。普通编辑无需额外服务或模型 API。

## 安装

### 让 AI 帮你安装

把下面这段话发给能访问网络和本地文件的 AI 编程工具：

```text
请阅读 https://github.com/yuanqimanong/yaya 的 INSTALL.md，按当前工具的技能目录规则安装 yaya。
只安装 core/yaya 中的完整中英核心；其他语言包暂不安装。
已有安装时，先把旧目录备份到技能发现路径之外，并保留本地定制。
安装后告诉我实际目录和版本，再用一句短文验证能否调用 yaya。
```

在提供 `$skill-installer` 的 Codex 中，也可以直接发：

```text
$skill-installer 请从 https://github.com/yuanqimanong/yaya/tree/main/core/yaya 安装 yaya。
```

安装器报已有目录时，按 [升级与回滚步骤](INSTALL.md#4-update-remove-or-roll-back)处理。AI 需要有读取仓库和写入目标目录的权限；只读 `SKILL.md` 可以试用，但不代表已安装或能被自动发现。

### 从源码手动安装

当前核心为 **0.3.2**，尚无公开 Release 下载。先克隆仓库：

```text
git clone https://github.com/yuanqimanong/yaya.git
cd yaya
```

将整个 `core/yaya/` 目录复制到所用工具的 Skill 目录。Codex 的常用位置如下：

| 范围 | 目标目录 |
| --- | --- |
| 当前用户 | `~/.agents/skills/yaya/`，Windows 下为 `%USERPROFILE%\.agents\skills\yaya\` |
| 单个项目 | `PROJECT_ROOT/.agents/skills/yaya/` |

路径依据 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)，核对日期为 2026-10-21。其他兼容工具按各自的目录规则安装。

首次安装到 Windows 个人目录，可在仓库根目录运行：

```powershell
$skillTarget = Join-Path $env:USERPROFILE '.agents\skills\yaya'
if (Test-Path -LiteralPath $skillTarget) { throw 'yaya 已存在，请先按 INSTALL.md 备份并升级。' }
New-Item -ItemType Directory -Path (Split-Path $skillTarget -Parent) -Force | Out-Null
Copy-Item -LiteralPath '.\core\yaya' -Destination $skillTarget -Recurse
```

复制后应有 `yaya/SKILL.md`、`references/`、`scripts/` 和 `languages/`。只需安装完整的核心目录；可选语言包使用下文的独立安装流程。Codex 通常会自动发现新技能；未出现时重启后再试。

## 直接这样用

安装后直接提出请求，或用 `$yaya` 显式指定。在 Codex 中也可输入 `$` 后选择 Yaya。

### 用短命令固定任务范围

```text
$yaya --help
$yaya human --focus direct -- 下面这段有多余的否定对比和免责声明……
$yaya polish --domain finance --audience 普通读者 -- 下面这段财报说明……
$yaya comment --file src/cache.py --write
$yaya prompt --target output --audience 新手 -- 让这个助手解释得容易懂：……
$yaya domains
$yaya domains tech
$yaya help prompt
```

| 命令 | 固定能力 |
| --- | --- |
| `polish` | 润色正文，保留原意与事实限定 |
| `human` | 去套话、空泛铺垫、机械重复和过度防御表达 |
| `review` | 只审表达，给问题与建议，不交完整改稿 |
| `verify` | 按证据核对主张，给依据与未确认项，不改稿 |
| `comment` | 默认只改普通注释；`--scope docstrings` 选择明确的 docstring 节点 |
| `prompt` | 默认优化提示词措辞；`--target output` 改下游回答风格，`both` 兼顾两者 |
| `style` | 从样稿提炼风格指令与示例；`--save PATH` 明确保存位置 |
| `origin` | 审阅“这是 AI 吗”的证据与不确定性 |

一个显式命令只执行一种任务。发现拼错的命令、未知领域或不适用的选项时，会报错并提示帮助，
不会悄悄扩大范围。`review`、`verify`、`origin` 保持只读。
改写类命令默认返回候选；`--file` 指定输入，`--write` 要求修改指定文件。
同一范围此前明确给过的文件修改授权仍有效，不必重复确认。

这是 **Skill 的聊天命令协议**，也接受 `yaya polish ...`；不会安装全局 shell 命令。
终端可运行 `python core/yaya/scripts/yaya.py --help`。该辅助入口只输出帮助或 JSON 任务计划，
实际改稿由当前 AI 宿主执行。完整选项以 `help COMMAND` / `COMMAND --help` 为准，
帮助与路由共用 [能力目录](core/yaya/catalog.json)。

### 定向处理过度防御表达

`human` 默认会检查“这是 X，而不是 Y”中的多余对比、替读者预设误解的辩解、
反复免责声明、重复缓和词，以及空泛夸赞和固定收尾。需要集中处理时：

```text
$yaya human --focus direct -- 只清理无效对比、防御性铺垫和重复限定，其余风格保留：……
$yaya review --focus direct -- 先指出这些问题和理由，不改稿：……
$yaya human --help
```

`--focus all` 是默认值；`direct` 只处理上述限定范围，仍可结合 `--domain tech`
或 `--domain finance`。例如“这不是要重新定义协作。通讯录新增按部门筛选。”
可改为“通讯录新增按部门筛选。”

判断依据是删后是否损失信息。“费用包含配送，不含安装”“尚未修复根因”
“本金可能亏损”等会影响理解或行动，应保留。用户未主动问到某项限制，也可能需要知道它。
已有清楚表述可以不改；不会通过虚构经历、补造事实或强行口语化制造“人味”。

这些规则按表达模式工作，未提供 GPT、Opus、DeepSeek、豆包的品牌预设或来源鉴定。
开源依据及证据限制见 [调研记录](tests/research/directness.md)，
本轮用例与实际输出见 [验证记录](tests/results/2026-10-30-directness/README.md)。

### 明确的领域规则

| `--domain` | 适用内容 | 重点保护 |
| --- | --- | --- |
| `tech` | 技术说明、API、运行手册、注释 | 接口语义、前置条件、有效配置、失败路径与发布状态 |
| `finance` | 财报解读、经营指标、投资者沟通 | 币种、期间、指标口径、同比/环比、收益和风险限定 |
| `data` | 指标、实验、调查和看板说明 | 样本与分母、时间窗、缺失值、相关/因果和不确定性 |
| `academic` | 摘要、方法、结果、讨论与综述 | 研究设计、引用归属、证据强度、局限与适用范围 |
| `business` | 工作邮件、进展、提案、客户通知 | 责任、日期、报价、交付条件、审批与承诺状态 |

领域、读者和语气分别选择。例如 `--domain finance --audience 普通读者 --tone 简明`，
既保留财务口径，也让非专业读者读懂。它不会为了“行业味”补造术语、数据或事实。
五类规则均有具体指南、原创改写/保留例和验收案例，目前标记为 **experimental**，
不等于行业认证或所有场景下的准确率保证。覆盖与排除项用 `yaya domains ID` 查询；
验证边界见 [领域说明](core/yaya/references/domains.md)。

### 自然语言可组合能力

原有调用方式继续有效，例如“用 yaya 核对并润色”会结合已请求的能力：

```text
$yaya 润色下面的文章，去掉空话，保留作者口吻和有用细节。
用 yaya 审阅这段话，指出问题和原因，先不要改写。
用 yaya 润色 report.md，让普通读者看懂，保留金融术语、数字和风险说明。
用 yaya 精简这个文件的普通注释，保留代码、docstring 和工具指令。
用 yaya 结合配置和接口样本核对这份技术说明，只修改说明文字。
用 yaya 优化下面的提示词，保留变量、输出格式和全部限制。
用 yaya 修改这个提示词，让 AI 用普通读者能懂的语言回答。
用 yaya 学习这段样稿，给我可复制的风格提示词和一个新例子。
用 yaya 以香港繁体中文润色这段说明，保留地区用语。
用 yaya 看看“这是 AI 吗”，给出依据和不确定性，不要改写。
```

| 功能 | 能做什么 |
| --- | --- |
| 去 AI 味与审稿 | 找出空泛铺垫、宣传语、翻译腔和机械重复，结合语境决定是否修改。 |
| 正文与文件润色 | 按指定用途、读者和风格调整文字，保留事实、数字和不确定性。 |
| 代码注释 | 结合代码改写注释，保留程序和工具指令。 |
| 工程事实核对 | 按需追踪配置、环境与接口来源，保留数字归属、条件和确定性；代码与注释冲突时报告可能的代码缺陷。 |
| 这是 AI 吗 | 审阅来源证据与写作迹象，给出 AI 生成倾向、人工写作倾向或无法判断；不把文本迹象当作来源鉴定。 |
| 提示词优化 | 整理提示词的措辞和结构，保留变量、输出格式和执行要求。需要改变 AI 的回答风格时，在请求中说明。 |
| 学习样稿风格 | 提炼表达习惯，生成可复制的风格提示词与示例。需要保存时，在请求中指定。 |

说“改写”就得到改稿，说“只检查”就得到问题和建议，说“修改这个文件”就编辑指定范围。原文已经清楚准确时可以不改。要求换语气或重组时，说明目标读者和用途；需要修改 docstring、日志或数据库元数据时，明确指定对象。

学习样稿提取的是表达习惯，不会迁移作者的身份、经历或观点，也不涉及模型训练。“这是 AI 吗”审阅写作迹象和来源材料；仅凭成文无法可靠区分人工、AI 生成与人机混写，不提供未经校准的概率或准确率。详见 [来源审阅边界](core/yaya/references/authorship.md)。

## 本地试用与开发

暂不安装时，让 AI 读取本地 [SKILL.md](core/yaya/SKILL.md)，再提交编辑请求。完整安装、更新和回滚见 [安装指南](INSTALL.md)。

在仓库根目录运行测试和构建：

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
python core/yaya/scripts/packs.py resolve --language zh-Hans
```

构建结果在 `dist/`，包含核心 ZIP、三个独立语言 ZIP、`catalog.json` 和 `SHA256SUMS`。克隆仓库会取得全部语言源码；安装时只复制核心和选定的语言包。

## 改写示例

原文：

> 在不断变化的行业环境中，新版本以创新为驱动，为用户开启全新篇章。它支持导出 CSV，目前仅向试用账户开放。

改写：

> 新版本支持导出 CSV，目前仅向试用账户开放。

英文原文：

> In today's fast-paced world, our groundbreaking update empowers teams to export shared notes as CSV. The feature is currently limited to trial accounts.

改写：

> Teams can now export shared notes as CSV. The feature is currently limited to trial accounts.

这是原创示例。实际改写还需核对论点、归因、条件和不确定性，例如“尚未证实”“预计”“可能”。“去 AI 味”是表达编辑，不用于判断作者是人还是 AI。

## 中英默认，其他语言按需安装

| 资源 | 默认安装 | 构建产物 |
| --- | --- | --- |
| 简体中文 `zh-Hans`、英语 `en` | 是 | `yaya-core-0.3.2.zip` |
| 繁体中文 `zh-Hant` | 否 | `yaya-lang-zh-Hant-0.2.0.zip` |
| 日语 `ja` | 否 | `yaya-lang-ja-0.2.0.zip` |
| 韩语 `ko` | 否 | `yaya-lang-ko-0.2.0.zip` |

语言包包含编辑指南和示例，安装后按任务语言加载，无需另外开启。可选包保存在核心目录之外，更新核心不会覆盖它们。缺少专门语言包时，AI 仍可尝试编辑，并说明未使用该语言的适配包；不会自动下载。

可以指定地区用语；未指定时保留原文习惯。目前所有语言包均为 **experimental**，尚未经过母语编辑的完整质量评估。

可选的 `PATTERNS.md` 提供该语言的去套话例子。语言包只包含文本数据，统一使用 `format_version: 1`、`core_major: 0` 的当前规范。新增语言无需修改核心路由；本地检测器的支持范围另行定义。

## 可选的本地检查

在已安装的 `yaya/` 目录运行：

```text
python scripts/detect_tells.py draft.md --language zh-Hans
python scripts/check_rewrite.py before.md after.md
python scripts/check_comments.py before.py after.py
python scripts/check_docstrings.py before.py after.py --allow approved-docstrings.json
```

| 工具 | 实际检查范围 |
| --- | --- |
| `detect_tells.py` | 仅支持 `en` 和 `zh-Hans`，扫描有限词句候选并输出位置和原因。命中需结合语境判断，不输出 AI 概率。 |
| `check_rewrite.py` | 比较 Markdown 保护片段、链接、占位符，以及已识别的币种、数量级、科学计数法和单位。成对引号内容需 `--protect-quotes`，其他指定原样片段需 `--protect-literal`。 |
| `check_comments.py` | Python `.py` / `.pyi` 普通 `#` 注释的修改边界，保护代码、字符串、行结构和已识别工具指令；不支持增删或移动注释行。 |
| `check_docstrings.py` | 独立检查明确授权的 Python docstring 节点；绑定具体候选与字面值，保护其他代码、字符串和已识别示例。 |
| `edit_evidence.py` | 保存任务开始的工作树原稿及 Git 基线，记录内容摘要、工具版本、命令、时间和状态；旧报告不能替代新验证。 |

检查器只读原稿和候选；证据工具仅在指定目录写快照和报告。前两个正文工具接受每份不超过 2 MiB 的 UTF-8 输入。检查通过后仍需核对语义：数字是否属于原来的对象，条件、否定、归因和确定性是否保留。

0.3.2 补上了 `USD 5 million → EUR 5 billion`、`1e-3 → 1e+3`、`3 个百分点 → 3 个基点`、
`8 MiB → 8 GiB` 等变化的漏检。数量检查比较原样表达与出现次数，单位换算和数字格式变化也需复核。
它无法确认数字归属、跨行币种标签或未列出的单位；支持范围见 [数量检查说明](core/yaya/references/validation.md#quantities-in-prose)，
实际修复对照见 [验证记录](tests/results/2026-10-30-quantities/README.md)。

`--allow` 自 0.2.1 起接受绑定具体文件摘要和差异的 JSON，拒绝旧式整类放行。docstring 改动会改变 `__doc__`，AST 比较只验证机械范围。用法、Windows 编码边界和批量统计见 [验证指南](core/yaya/references/validation.md)。普通润色仍直接交付，无需固定评分或报告。

“这是 AI 吗”使用当前宿主模型审阅；`detect_tells.py` 只扫描措辞候选，两者的结果不能互相替代。

Markdown 扫描器支持有限语法；识别到缩进块、列表内围栏、脚注、多行链接或原始 HTML 块等结构时，会返回不支持。它无法识别所有超出范围的结构，请一并查看 JSON 中的 `limitations`。Python 源码须能被当前解释器解析；其他编程语言的注释需要宿主解析器或人工检查。

工具需要 **Python 3.10+**，仅使用标准库。二进制文档读取和版式处理使用宿主已有工具。

## 为你的语言贡献支持

从 [语言包模板](templates/language-pack/README.md) 开始，编写 `pack.json`、`GUIDE.md`、`examples.md` 和 `LICENSE`；需要专项规则时添加 `PATTERNS.md`。同时提供值得改写和应当保留的例子，通过校验后提交。新增语言沿用同一套加载和安装流程。

语言标识、版本、文件格式和审核要求见 [语言包规范](docs/language-pack-spec.md)。模板中的 `fr` 是法语编写示例，尚未作为支持包发布。

安装、升级和回滚见 [安装指南](INSTALL.md)；版本改动见 [0.2 升级说明](docs/upgrade-0.2.md)；设计和实测结果见 [设计说明](docs/design.md)、[验收记录](tests/README.md)。

[MIT License](LICENSE)
