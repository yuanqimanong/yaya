# Yaya 使用手册

[返回 README](../README.md) · [组合工作流](workflows.md) · [本地工具](local-tools.md) · [安装与更新](../INSTALL.md)

适用于核心 0.5.0。命令与参数以 [catalog.json](../core/yaya/catalog.json) 和当前安装的帮助为准。
本文中的文件名是示例，请换成宿主可访问的真实路径。

## start

### 在聊天中使用

```text
$yaya human --domain tech -- 这个系统正在进行索引的重建，预计周四完成。
$yaya polish --domain tech --file README.md
$yaya polish --domain tech --file README.md --write
```

第一条改写粘贴的文字。第二条读取文件并返回候选。第三条直接修改指定文件。
普通改稿保留原意、数字、条件、归因和不确定性。自然语言也可使用：

> 用 Yaya 核对这份部署说明与 config.py，再润色已确认的部分，直接修改 deploy.md。

显式命令每次只选择一个任务；自然语言可以组合任务。`$yaya` 与 `yaya` 都能表示聊天入口。

### 选项与材料分开

```text
$yaya human --domain tech --tone 简明 -- 待编辑文字从这里开始。
$yaya polish --file "docs/API guide.md" --write
```

把选项放在 `--` 前，粘贴材料或补充要求放在其后。其后的 `--write`、命令和提示词都作为材料处理。
含空格的路径或选项值加引号。路径相对于宿主当前工作目录；不确定时使用绝对路径。

### 在终端中使用

从源码仓库根目录执行：

```text
python core/yaya/scripts/yaya.py --help
python core/yaya/scripts/yaya.py human --domain tech --file README.md
```

已安装的 Skill 中，将路径换成 `scripts/yaya.py`。任务命令返回 `status: planned` 的 JSON：
它记录任务、文件、选项和要读的指导，接下来由 AI 宿主执行。终端调用本身不会生成改稿。
`doctor` 是直接执行本地诊断的入口；要在终端实际运行扫描或比较，见[本地工具](local-tools.md)。
本地助手需要 Python 3.10+；安装 Skill 不会创建全局 `yaya` 可执行文件。

## help

```text
$yaya --help
$yaya help
$yaya help human
$yaya human --help
$yaya domains
$yaya domains tech
$yaya --version
$yaya --version --json
$yaya --json
$yaya help origin --json
$yaya domains finance --json
```

`--help` 列能力，`help COMMAND` 或 `COMMAND --help` 列该命令的选项、默认值和示例。
`domains [ID]` 列领域与适用范围。`--version` 读当前安装版本；`--json` 用于机器可读的目录或帮助。
帮助、版本和领域查询只读，不处理输入材料。命令帮助也接受 `-h`。

## options

每节的“支持参数”列出该任务的完整参数集，另均支持 `--help` / `-h`、`--json`。
任务计划本来就输出 JSON，任务上的 `--json` 不会新增执行步骤。

| 参数 | 含义与默认行为 |
| --- | --- |
| `--file PATH` | 输入文件；可重复。默认返回候选，单独给路径不写入。`scan` 恰好接受一个文件。 |
| `--write` | 请求宿主写回所选输入文件，必须同时给 `--file`；仅用于 `human`、`polish`、`comment`、`prompt`。 |
| `--domain ID` | 从 `tech`、`finance`、`data`、`academic`、`business` 中选择一个；不填则不显式加载领域。 |
| `--audience TEXT` | 目标读者，如新手、开发者、管理层；不填则沿用原文和任务上下文。 |
| `--tone TEXT` | 语气，如简明、正式、亲切；不填则保留原文声音。 |
| `--lang TAG` | 目标语言或地区，如 `zh-Hans`、`en-GB`、`zh-HK`；不填保留输入语言。`scan` 必填且仅接受 `en` / `zh-Hans`。 |
| `--style PATH` | 读取已保存风格卡，仅作表达指导，保持风格卡本身不变；用于四个改写命令。 |
| `--focus all\|direct` | `human`、`review` 的重点；默认 `all`，`direct` 只处理无效对比、防御性铺垫和重复限定。 |
| `--source PATH` | `verify` 的证据文件，可重复；与待核对的 `--file` 分开。 |
| `--scope comments\|docstrings` | `comment` 的对象，默认 `comments`；选 docstring 后仍须明确函数、类等节点。 |
| `--target wording\|output\|both` | `prompt` 的改动目标，默认 `wording`。 |
| `--save PATH` | `style` 的保存路径；不填只返回风格卡，指定路径须为新文件。 |
| `--rule ID` | `scan` 的规则选择，可重复；不填运行该语言全部规则。 |
| `--before PATH` / `--after PATH` | `check` 的原稿和候选稿，两者必填，均只读。 |
| `--kind prose\|comments` | `check` 的比较对象，默认 `prose`。 |
| `--literal TEXT` | `check` 额外保护的原文片段，可重复，片段须存在于原稿；仅用于 `prose`。 |
| `--quotes` | `check` 保护成对双引号、弯引号和中日韩引文；仅用于 `prose`。 |

除标明可重复的参数外，每个选项只提供一次。`--write`、`--quotes` 是开关，不接 `true` 或 `false`。
未列出的命令、领域和参数组合会报错；它们不会自动变成不受限制的自然语言任务。

## human

**用途：** 去掉空泛铺垫、套话、机械重复、翻译腔和过度防御表达，保留作者的有效观点与语气。

**输入：** `--` 后的文字，或一个/多个 `--file`。**输出：** 改稿；加 `--write` 时写回文件。

**支持参数：** `--focus`、`--domain`、`--audience`、`--tone`、`--lang`、`--file`、`--write`、`--style`。

```text
$yaya human -- 在不断变化的行业环境中，新版本开启全新篇章。它支持导出 CSV，目前仅向试用账户开放。
$yaya human --domain tech --file README.md --write
$yaya human --focus direct --domain finance --file report.md
$yaya human --style team-style.md --file draft.md
```

第一条例子可以改为：“新版本支持导出 CSV，目前仅向试用账户开放。”

默认 `--focus all` 覆盖全部表达问题。`direct` 只处理无效对比、假想反驳、防御性铺垫和重复限定，
例如删掉功能介绍中无关的“这不是要重新定义协作”。它仍保留“仅支持 Linux”“本金可能亏损”等实质条件。
其他表达不随 `direct` 一起大改；领域和语气参数也不会扩大这个范围。

规则按上下文判断，没有 GPT、Opus、DeepSeek 或豆包专属词表。真实对比、致谢、局限和清楚文字可以保留。
想只看问题用 `review`；想判断来源用 `origin`。

## polish

**用途：** 改善句子、段落结构和可读性，按指定领域、读者与语气表达。

**输入：** 粘贴文字或文件。**输出：** 改稿，或所选文件的修改。

**支持参数：** `--domain`、`--audience`、`--tone`、`--lang`、`--file`、`--write`、`--style`。

```text
$yaya polish --domain tech --audience 新手 --tone 简明 --file api-guide.md
$yaya polish --domain finance --file report.md --write
$yaya polish --lang en-GB --style team-style.md --file draft.md
```

保留原文事实和完整信息，不自动把文章缩成摘要。`--lang` 明确指定输出语言或地区；仅选领域不会翻译。
润色不执行事实核对，需要核对时先用 `verify`，或通过自然语言明确组合请求。

## review

**用途：** 查看表达问题后再决定是否改稿。

**输入：** 粘贴文字或文件。**输出：** 问题片段、原因和建议；保持文件不变，不交付替换全文。

**支持参数：** `--focus`、`--domain`、`--audience`、`--tone`、`--lang`、`--file`。

```text
$yaya review --domain academic --file abstract.md
$yaya review --focus direct --file draft.md
$yaya review -- 这段话是否有空泛铺垫：新版本开启协作的新篇章，支持按部门查询。
```

默认检查全部表达问题；`--focus direct` 只检查直接性。没有实际问题时可以说明无需修改。
事实证据用 `verify`；`review` 不接受 `--write` 或 `--style`。

## verify

**用途：** 根据代码、配置、接口约定或给定来源核对主张。

**输入：** `--file` 指定待核对文字，重复 `--source` 指定证据；也可在 `--` 后提供主张与来源说明。
**输出：** 差异、证据位置与未确认项；所有文件只读。

**支持参数：** `--domain`、`--lang`、`--file`、`--source`。

```text
$yaya verify --domain tech --file deploy.md --source config.py --source production.env
$yaya verify --domain finance --file report.md --source quarterly-results.md
$yaya verify --domain data -- 实验摘要称转化率提高；请按已提供的结果表核对分母和时间窗。
```

如说明写“生产超时为 30 秒”，代码只显示默认值，报告应区分默认值与生产实际配置。
没有足够证据的结论保持未确认；来源文件不可读时会说明影响。来源选择不等于来源已独立认证。
`--source` 可省略，宿主按任务查找可访问的相关证据；本地命令本身不会联网或读取输入。
修正文稿是另一个步骤，`verify` 不接受 `--write`。

## comment

**用途：** 结合附近代码，说明用途、边界或有依据的原因。

**输入：** 代码片段或源码文件。**输出：** 注释候选或所选文件的注释修改。

**支持参数：** `--domain`、`--audience`、`--tone`、`--lang`、`--file`、`--write`、`--scope`、`--style`。

```text
$yaya comment --domain tech --file src/cache.py --write
$yaya comment --file src/cache.py --file src/client.py --write
$yaya comment --scope docstrings --file app.py -- 仅处理函数 get_data 的 docstring，返回候选。
```

默认 `--scope comments` 只改普通注释。代码、日志、报错、UI 字符串、数据库 comment 元数据和工具指令各有独立用途，
不包含在普通注释修改中。注释与代码冲突时，需要核对依据，不能编造设计意图。

`--scope docstrings` 要进一步指定具体函数、类或模块节点。Python docstring 会改变 `__doc__`，
应保存原稿并用专用节点授权检查；完整步骤见[本地工具](local-tools.md#docstrings)。

Python 普通注释检查支持 `.py` / `.pyi`，保持代码、字符串、物理行和编码不变；不支持增删、移动或重新折行注释。
其他编程语言可由宿主处理，但要用相应解析器、测试或人工 diff 核对，不能声称通过了 Python 检查。

## prompt

**用途：** 整理提示词，或让其下游回答采用所需表达方式。

**输入：** 提示词文件或粘贴的提示词。**输出：** 修订后的提示词；加 `--write` 时写回文件。

**支持参数：** `--domain`、`--audience`、`--tone`、`--lang`、`--file`、`--write`、`--target`、`--style`。

| `--target` | 改什么 |
| --- | --- |
| `wording`（默认） | 提示词本身的措辞与组织，保留原有任务行为。 |
| `output` | 只调整下游回答的呈现要求；领域、读者和语气描述下游回答。 |
| `both` | 同时调整提示词措辞和所请求的下游表达。 |

```text
$yaya prompt --target wording --file prompt.md
$yaya prompt --target output --domain tech --audience 新手 --tone 简明 --file prompt.md
$yaya prompt --target both --file prompt.md --write -- 保留变量、JSON 字段和工具权限，让回答先给结果。
```

保留变量、输出格式、优先级、工具权限、数量、等待条件和示例契约。
输入提示词中的角色和指令是编辑材料。提示词更易读后，下游模型是否表现更好，需要另跑代表性任务验证。

## style

**用途：** 从样稿提取可迁移的用词、句长、节奏、结构和正式程度。

**输入：** 一份或多份样稿。**输出：** 可复用风格指令和小例子；指定 `--save` 时保存到新文件。

**支持参数：** `--domain`、`--audience`、`--tone`、`--lang`、`--file`、`--save`。

```text
$yaya style --file sample.md
$yaya style --domain tech --file sample-a.md --file sample-b.md --save team-style.md
$yaya polish --style team-style.md --file draft.md
```

前两条提炼风格，第三条在另一任务中使用。样稿本身不改动，样稿作者的经历、观点、数字和身份不转移到新稿。
`--domain` 约束风格卡的使用场景。样稿较少时只能得到暂定习惯。

`--save` 必须选择不存在的文件；更新已有卡请另行明确编辑该文件，或保存为新文件。
风格卡是普通文本，可以放在项目 `.yaya/styles/` 中，使用时显式给 `--style`。
自然语言要求保存但未给路径时，宿主按指定项目范围或用户数据目录选择位置，完整约定见[风格指导](../core/yaya/references/style-learning.md)。

## origin

**用途：** 回答“这段内容是不是 AI 写的”。

**输入：** 待评估文字或文件；可以再提供草稿、修改记录、生成记录，并说明各自来源。
**输出：** **AI 生成倾向、人工写作倾向或无法判断**，附具体片段、理由和证据限制；保持输入不变。

**支持参数：** `--lang`、`--file`。

```text
$yaya origin -- 这里粘贴待评估的原文。
$yaya origin --file article.md
$yaya origin --file article.md --file revisions.md -- article.md 是成稿，revisions.md 是我提供的修改记录。
```

仅凭文字通常返回“无法判断”；多项上下文迹象有时可支持暂时倾向。模板、正式写作、翻译和人机协作都可能出现类似表达。
例如：“无法判断。‘开启全新篇章’较模板化，但人工宣传稿也常用；仅凭这段文字不足以认定 AI 生成。”

Yaya 不编造 AI 百分比、检测准确率或具体生成模型。可靠过程证据能支持更具体的结论，报告会说明它实际证明的部分。
想降低套话用 `human`，想找字面候选用 `scan`；这两项结果不能换算成作者来源结论。

## scan

**用途：** 用本地有限字面规则找待审阅措辞。

**输入：** 恰好一个 `--file`，并明确 `--lang en` 或 `--lang zh-Hans`。
**输出：** 命中的措辞、行列位置、规则、审阅提示与输入版本；文件只读。

**支持参数：** `--file`、`--lang`、`--rule`。

```text
$yaya scan --file draft.md --lang zh-Hans
$yaya scan --file draft.md --lang en --rule en-stock-close
$yaya scan --file draft.md --lang zh-Hans --rule zh-empty-opener --rule zh-light-verb
```

| 候选类型 | 英语规则 | 简体中文规则 |
| --- | --- | --- |
| 空泛开头 | `en-empty-opener` | `zh-empty-opener` |
| 宣传套话 | `en-hype` | `zh-hype` |
| 模板收尾 | `en-stock-close` | `zh-stock-close` |
| 间接动词表达 | `en-light-verb` | `zh-light-verb` |

不填 `--rule` 时运行该语言全部规则；可重复选择同语言规则。未知规则或语言不匹配会报错。
报告的 `enabled_rules` 是实际扫描范围，`evidence` 记录路径、SHA-256、字节数和输入稳定性；改稿后需要重扫。

命中项需要结合上下文判断。空结果仅表示所选字面规则未命中。过度防御需要上下文判断，请用 `review --focus direct`。
安装日语等语言包不会增加扫描规则。文件选项不接受单独的 `-`；名为 `-` 的文件使用 `./-`。
终端实际扫描命令见[本地工具](local-tools.md#scan)。

## check

**用途：** 比较原稿与候选稿，检查受保护内容是否发生变化。

**输入：** 必填的 `--before` 和 `--after` 两个文件。**输出：** 已执行的检查状态与差异，文件只读。

**支持参数：** `--before`、`--after`、`--kind`、`--literal`、`--quotes`。

```text
$yaya check --before original.md --after candidate.md
$yaya check --before original.md --after candidate.md --literal retry_limit --literal EBITDA --quotes
$yaya check --kind comments --before original.py --after candidate.py
```

默认 `--kind prose` 检查支持的 Markdown 保护片段、链接、占位符、数字及部分单位等。
`--literal` 保护额外片段的原样出现，`--quotes` 保护支持的成对引文。每个 literal 必须存在于原稿。
`--kind comments` 选择 Python 普通注释检查，不接受 `--literal` 或 `--quotes`。

| 状态 | 如何处理 |
| --- | --- |
| `passed` | 已实现的机械检查通过；继续对照数字归属、条件、否定和结论。 |
| `failed` | 存在受保护内容变化；查看具体差异，再修正候选或单独审阅确有必要的改动。 |
| `unsupported` | 格式或语法超出检查范围；换适合的工具或人工复核。 |
| `error` | 路径、输入、授权文件等有问题；修正调用后重跑。 |

`check` 不改稿、不自动批准差异。文件参数拒绝单独的 `-`；真实文件名为 `-` 时用 `./-`。
Python docstring 与用户明确要求改变受保护内容的检查，使用[专用工具与具体授权](local-tools.md#rewrite)。

## doctor

**用途：** 排查安装文件缺失、命令目录异常、脚本语法或内置资源问题。

**输入：** 无任务文件。**输出：** `ready` 或 `degraded`，以及各项检查结果；不会自动修复。

**支持参数：** `--json`、`--help` / `-h`。

```text
$yaya doctor
$yaya doctor --json
$yaya help doctor
```

`ready` 表示本地结构与语法检查通过。确认宿主能发现 Skill，还需在聊天中选择 Yaya 并实际做一次短文本编辑。
若命令入口无法启动，在安装目录执行 `python scripts/doctor.py`。损坏安装按[安装指南](../INSTALL.md)从校验过的完整副本恢复。

## domains

五类领域用于约束表达和重要事实关系，可以与读者、语气、语言独立组合：

```text
$yaya domains tech
$yaya polish --domain tech --audience 新手 --tone 简明 --file api-guide.md
$yaya human --domain finance --audience 普通读者 --file report.md
$yaya review --domain data --file experiment.md
$yaya polish --domain academic --file abstract.md
$yaya polish --domain business --file customer-notice.md
```

| ID | 适用材料 | 重点保留 | 不包含的工作 |
| --- | --- | --- | --- |
| `tech` | README、API、运维、故障说明、注释 | 接口、版本、前置条件、失败路径、默认与实际配置、计划与完成 | 代码正确性证明、生产验收、安全审计 |
| `finance` | 财报、经营指标、投资者沟通、已有产品风险说明 | 币种、期间、指标口径、同比/环比、基点/百分点、预测、审计与风险限定 | 投资建议、会计审计、监管认证、自动补充行情法规 |
| `data` | 指标、实验、看板、调查分析 | 样本、分母、时间窗、缺失值、百分比/百分点、相关/因果、不确定性 | 自动重算数据、统计方法审计、因果识别认证 |
| `academic` | 摘要、方法、结果、讨论、局限、综述 | 研究设计、样本范围、结果与解释、引用归属、证据强度 | 虚构引用、补做研究、期刊认证、全学科术语核定 |
| `business` | 邮件、进展、提案、产品说明、客户通知 | 责任人、日期、价格范围、审批、交付条件、承诺与可用范围 | 代发邮件、代作承诺、合同效力认定、生成营销数据 |

例如技术说明中的“默认值为 30 秒”不能润色成“生产环境使用 30 秒”；金融说明中的“提高 3 个百分点”不能改成“增长 3%”。
规则当前均为 `experimental`，提供具体编辑指导，专业事实仍需来源核对。医疗、法律等尚无专门领域 ID；
可以自然语言请求通用编辑，不能写 `--domain medical` 并期待它自动降级。

## files

### 单文件和批量编辑

```text
$yaya human --domain tech --file README.md --write
$yaya polish --domain tech --file docs/api.md --file docs/deploy.md --write
$yaya polish --file README.md --write -- 仅修改简介，保留命令、链接和其他章节。
```

路径选择不自动授权写入。`--write` 明确请求编辑；会话中已给出的同文件、同范围修改授权也可以沿用。
当前选择 `review` 等只读命令时，以只读范围为准。

批量工作先保存当前工作树中的原稿，再记录实际改动和检查。已有未提交内容属于原稿的一部分，不能拿 Git HEAD 直接替代。
`--file` 不自带目录递归或通配展开；批量文件显式列出，或自然语言指定目录让宿主先确认具体文件范围。
要只查看候选，省略 `--write`，且不要在同一请求中要求直接修改文件。

### 输入格式

宿主能读取的 Markdown、纯文本和源码可直接处理。Word、PDF 等二进制文件的解析、排版和导出依赖宿主已有工具。
本地正文检查器只接受 UTF-8 文本，每个输入最多 2 MiB；复杂 Markdown 可能返回 `unsupported`。
完整工具覆盖和退出码见[本地工具](local-tools.md)。

## language

| 语言 | 标签 | 安装方式 |
| --- | --- | --- |
| 简体中文 | `zh-Hans` | 核心自带 |
| 英语 | `en` | 核心自带 |
| 繁体中文 | `zh-Hant` | 可选语言包 |
| 日语 | `ja` | 可选语言包 |
| 韩语 | `ko` | 可选语言包 |

```text
$yaya polish --lang zh-HK --file notice.md
$yaya human --lang en-GB --file article.md
```

没有指定 `--lang` 时保留原文语言和地区习惯。`zh-HK` 可使用繁中包，同时保留香港用语；裸 `zh` 不自动选择简繁。
所有包目前均为实验性指导。法语目录是贡献模板，尚未作为支持包发布。

可选包从源码构建：

```text
python scripts/build_release.py
```

在已安装的 `yaya/` 目录运行以下命令；将 `ARCHIVE` 和 `EXPECTED_SHA256` 换成构建输出路径与可信 catalog 中的摘要：

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256
python scripts/packs.py resolve --language ja
python scripts/packs.py list
```

安装后无需额外启用。解析顺序为显式项目、用户、内置资源；每个位置内先匹配具体地区，再回退较宽标签。
项目安装与自定义数据目录分别用 `--project PROJECT_ROOT`、`--data-dir DATA_DIRECTORY`，后续操作沿用同一目标。
缺少专门指导时，宿主可说明限制后尝试通用编辑；不会自动下载。

升级、移除和恢复分别执行所需命令：

```text
python scripts/packs.py install ARCHIVE --sha256 EXPECTED_SHA256 --replace
python scripts/packs.py remove ja
python scripts/packs.py rollback ja
```

替换和移除会保留旧包；`rollback` 验证并恢复最新备份。核心更新另按[安装与恢复步骤](../INSTALL.md#4-update-remove-or-roll-back)，
备份旧核心到 Skill 发现目录之外，保留独立的语言包和风格卡。新核心有后续修改时先保存，再恢复旧版。

## troubleshooting

| 现象 | 原因与处理 |
| --- | --- |
| 终端提示找不到 `yaya` | 使用 `python core/yaya/scripts/yaya.py ...`；聊天中才用 `$yaya ...`。 |
| 终端只输出 `planned` | 路由已完成；将请求交给 AI 宿主，或用专用脚本执行本地扫描/比较。 |
| 参数或领域报错 | 用 `help COMMAND` / `domains` 核对准确名称和允许组合，单值选项不要重复。 |
| `--write` 报错 | 同时给 `--file`，并确认命令属于四个改写任务。 |
| 文件没有修改 | 检查是否只请求了候选、路径是否正确、宿主是否有文件权限；`planned` 不是写入收据。 |
| 风格卡未生效 | 检查 `--style` 路径是否可读，以及当前任务、读者或语言是否限制了卡的适用范围。 |
| `scan` 拒绝语言或规则 | 仅用 `en` / `zh-Hans` 与同语言规则；其他语言用宿主审阅。 |
| `check` 返回不支持 | 查看具体结构或语法原因，改用适当解析器或人工复核，不计为通过。 |
| `origin` 返回无法判断 | 当前证据不足；可补充草稿或修改记录，也可保留这一结论。 |
| `doctor` 正常但宿主看不到 Skill | 检查安装目录与宿主加载方式，按宿主要求刷新或重启，再试一条短文本请求。 |

从 `human`、`polish` 或 `origin` 选一个任务即可开始。终端执行步骤与检查范围见[本地工具手册](local-tools.md)。
