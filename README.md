# Yaya · 牙牙学语

[English](README.en.md) · [安装与升级](INSTALL.md) · [操作指南](docs/workflows.md) · [更新记录](CHANGELOG.md)

Yaya 是写作编辑 Skill，在当前 AI 工具中完成去 AI 味、正文润色、注释整理、提示词优化和事实核对。编辑时保留原意、事实、作者口吻、技术细节和必要限定。

默认支持简体中文和英语，繁体中文、日语、韩语可按需安装。日常编辑使用当前宿主模型，无需另配模型 API 或后台服务。

## 能做什么

| 命令 | 适合的任务 | 交付内容 |
| --- | --- | --- |
| `human` | 去掉套话、空泛铺垫、机械重复和过度防御表达 | 改稿；`--focus direct` 只处理无效对比、防御性铺垫和重复限定 |
| `polish` | 调整正文结构、措辞和可读性 | 保留原意的润色稿 |
| `review` | 先看表达有哪些问题 | 问题、原因和建议，保持文件不变 |
| `verify` | 按代码、配置或资料核对主张 | 依据、结论和未确认项，保持文件不变 |
| `comment` | 整理代码注释 | 默认只改普通注释；docstring 需显式选择具体节点 |
| `prompt` | 整理提示词，或调整下游回答风格 | 保留任务、变量和输出约束的提示词 |
| `style` | 从样稿提炼表达习惯 | 风格卡和小例子；`--save` 可保存到指定的新路径 |
| `origin` | 评估“这段内容是不是 AI 写的” | AI 生成倾向、人工写作倾向或无法判断，并说明依据；保持原文不变 |
| `scan` | 按有限字面规则定位措辞 | 候选位置和原因，保持文件不变 |
| `check` | 比较原稿和候选稿的保护项 | 通过、失败或不支持，保持文件不变 |
| `doctor` | 排查本地安装问题 | 运行文件、Python 语法和资源检查结果，保持安装不变 |

一个显式命令对应一种任务。要组合使用，比如“核对并润色”，直接用自然语言说明即可。

## 安装

当前核心版本为 **0.5.0**，从 `main` 分支安装，尚未发布 GitHub Release。安装后核对实际版本。

### 让 AI 安装

把下面的请求交给可以访问仓库和本地文件的 AI 编程工具：

```text
请阅读 https://github.com/yuanqimanong/yaya/blob/main/INSTALL.md，
从 https://github.com/yuanqimanong/yaya/tree/main/core/yaya 安装完整核心。
只安装默认中英核心。已有安装时，先比较本地定制，
将旧目录备份到 Skill 发现路径之外，再按文档升级。
完成后报告安装路径和版本，运行 doctor，再用一句短文验证调用。
```

### 从源码安装

先取得本 README 对应的核心版本：

```text
git clone --branch main --single-branch https://github.com/yuanqimanong/yaya.git
cd yaya
python core/yaya/scripts/yaya.py --version
```

将完整的 `core/yaya/` 复制到所用工具的 Skill 目录，保留相对目录结构，跳过 `__pycache__`。Codex 可选以下位置：

| 使用范围 | 安装目录 |
| --- | --- |
| 当前用户 | `~/.agents/skills/yaya/`；Windows 为 `%USERPROFILE%\.agents\skills\yaya\` |
| 单个项目 | `PROJECT_ROOT/.agents/skills/yaya/` |

选择适用的位置安装。其他兼容工具遵循各自的 Skill 目录规则。安装目录应包含 `SKILL.md`、`catalog.json`、`version.json`、`references/`、`scripts/` 和 `languages/`。

已有安装时，按 [安装与回滚指南](INSTALL.md#4-update-remove-or-roll-back)准备独立副本、核对文件并备份后再替换。外部语言包和保存的风格卡单独保留。

从安装后的 `yaya/` 目录运行：

```text
python scripts/yaya.py --version --json
python scripts/yaya.py doctor --json
```

版本应为 `0.5.0`，诊断应为 `ready`。`doctor` 检查本地安装结构与语法；接着在下一轮对话中选择 Yaya，提交一条编辑请求，确认宿主能找到并使用它。列表中未出现时，按宿主的方式重新加载或重启。

本地助手需要 **Python 3.10+**，仅使用标准库，用于语言包管理和本地检查。宿主仍可直接读取编辑指南，无需 Python。

## 在聊天中使用

安装后，在 Codex 中输入 `$` 选择 Yaya，或直接发送下面的命令。也支持 `yaya COMMAND ...`。

```text
$yaya --help
$yaya help human
$yaya domains
$yaya domains tech
$yaya --version
```

### 技术文档去 AI 味

计算机、软件工程和 AI 项目的 README、接口说明与运行手册使用 `tech` 领域：

```text
$yaya human --domain tech --audience 开发者 --file README.md --write
```

Yaya 会直接修改指定文件的文字，保留命令、代码、参数、版本和使用条件。清楚准确的段落可以不改。

如果只想处理“这是 X，而不是 Y”式的多余对比、反复免责声明和防御性铺垫：

```text
$yaya human --focus direct --domain tech --file README.md --write
```

`direct` 保留其余风格；默认的 `all` 还会检查套话、空泛夸赞、机械重复和固定收尾。删改前先判断这段话是否提供了信息。例如：

原文：

> 这不是要重新定义模型调用。客户端只在连接超时时重试，最多重试 2 次。

改写：

> 客户端只在连接超时时重试，最多重试 2 次。

“只在连接超时时”和次数界定接口行为，应保留。实际风险、归因和不确定性同样要保留；改写只使用原文已有的事实与经历。

### 这段内容是不是 AI 写的？

用 `origin` 评估写作迹象和来源证据：

```text
$yaya origin -- 这里粘贴待判断的内容……
$yaya origin --file article.md
$yaya help origin
```

也可以直接说：“用 yaya 看看这段内容是不是 AI 写的，给出依据，先不要改写。”

结果会给出 **AI 生成倾向**、**人工写作倾向** 或 **无法判断**，并引用具体片段解释依据。整个过程保持原文不变。

仅凭文字通常无法确定作者来源；证据不足时会返回“无法判断”，不会编造 AI 概率。草稿、修改历史或生成记录可以帮助判断。具体方法见 [来源评估指南](core/yaya/references/authorship.md)。

### 其他常用任务

查看问题，暂不修改：

```text
$yaya review --focus direct --file draft.md
```

润色财务说明：

```text
$yaya polish --domain finance --audience 普通读者 --file report.md --write
```

按资料核对技术主张；多个来源可重复使用 `--source`：

```text
$yaya verify --domain tech --file deploy.md --source config.py --source api-contract.md
```

整理普通注释；需要修改 docstring 时明确节点：

```text
$yaya comment --domain tech --file src/cache.py --write
$yaya comment --scope docstrings --file app.py -- 仅处理函数 get_data 的 docstring
```

调整提示词要求的回答风格：

```text
$yaya prompt --target output --domain tech --audience 新手 --tone 简明 --file prompt.md --write
```

`prompt` 默认的 `--target wording` 只整理提示词自身措辞，`output` 调整下游回答的表达要求，`both` 允许同时处理两者。

学习并复用样稿风格：

```text
$yaya style --file sample.md --save team-style.md
$yaya polish --domain business --style team-style.md --file announcement.md
```

风格卡用于指导表达，样稿的事实、身份和经历不会迁入新稿。提炼风格不涉及模型训练，也不自动改变全局偏好。

### 参数与文件修改

- `--file PATH` 指定输入。改写类命令默认返回候选；添加 `--write` 可要求宿主写回文件。同一范围已有的明确修改授权仍然有效。
- `--domain` 选择领域，`--audience` 指定读者，`--tone` 指定语气；`--lang` 选择语言或地区。各命令支持的选项以帮助为准。
- `--style` 可用于 `human`、`polish`、`comment` 和 `prompt`；`style --save` 只保存到指定的新路径。
- 选项写在材料前，`--` 后的内容作为正文或请求。路径有空格时加引号。

例如，直接粘贴文字：

```text
$yaya human --domain tech -- 连接超时后，客户端会进行请求的重新尝试。
```

`review`、`verify`、`origin`、`scan` 和 `check` 都是只读任务。命令拼错、领域未知或参数不适用时，会报错并提示帮助，任务范围保持不变。

也可以自然描述需求：

```text
用 yaya 结合 config.py 核对 deploy.md，再润色其中的说明文字，直接修改文件。
用 yaya 优化这段提示词，让回答更直接，保留变量、输出格式和全部限制。
```

## 支持哪些领域和语言

| `--domain` | 适用材料 | 编辑时重点保留 |
| --- | --- | --- |
| `tech` | README、API 说明、运行手册、故障说明、代码注释 | 接口语义、版本、前置条件、失败路径、默认与实际配置、计划与完成状态 |
| `finance` | 财报解读、经营指标、投资者沟通 | 币种、期间、指标口径、同比与环比、基点与百分点、预测与已实现、风险限定 |
| `data` | 指标解读、实验结果、调查与看板说明 | 样本、分母、时间窗、缺失值、相关与因果、不确定性 |
| `academic` | 摘要、方法、结果、讨论和文献综述 | 研究设计、引用归属、证据强度、局限与适用范围 |
| `business` | 工作邮件、进展、提案、产品说明、客户通知 | 责任人、日期、报价、交付条件、审批和承诺状态 |

领域规则约束表达和事实关系，读者与语气分别设置。金融说明写得通俗，仍要保留财务口径；技术文档优先说清操作和条件，按需使用术语。完整范围和排除项见 `yaya domains ID` 与 [领域指南](core/yaya/references/domains.md)。

| 语言 | 标识 | 安装方式 |
| --- | --- | --- |
| 简体中文、英语 | `zh-Hans`、`en` | 随核心安装 |
| 繁体中文、日语、韩语 | `zh-Hant`、`ja`、`ko` | 按需安装独立语言包 |

Yaya 默认保留原文语言和地区习惯，也可指定 `--lang zh-Hant-TW`、`--lang en-GB` 等标签。语言包按需加载，安装流程见 [语言包安装](INSTALL.md#3-add-a-requested-language)。缺包时会说明情况，可尝试通用编辑；需要的包由用户选择安装。

五个领域与当前语言包均标记为 **experimental**。已有指南和验证案例，专业语义评审、母语评审及跨模型复测仍需继续补充。

## 本地检查与终端用法

`$yaya ...` 用在聊天中。终端通过 Python 助手查看帮助、生成任务计划或执行诊断；安装 Skill 不会生成全局 shell 命令。

从仓库根目录运行以下命令；从安装目录运行时去掉路径中的 `core/yaya/`：

```text
python core/yaya/scripts/yaya.py --help
python core/yaya/scripts/yaya.py human --domain tech --file README.md
python core/yaya/scripts/yaya.py doctor --json
```

第二条输出 JSON 任务计划，实际改稿由当前 AI 宿主完成；第三条直接执行只读安装诊断。扫描和比较也可以在聊天中发起：

```text
$yaya scan --file draft.md --lang zh-Hans --rule zh-stock-close
$yaya check --before original.md --after candidate.md --literal API_KEY --quotes
```

宿主会按计划运行检查器。`scan --help` 列出规则，`--rule` 可重复选择；`check` 默认检查正文，`--kind comments` 检查 Python 普通注释边界。要在终端直接执行对应检查器，运行：

```text
python core/yaya/scripts/detect_tells.py draft.md --language zh-Hans --rule zh-stock-close
python core/yaya/scripts/check_rewrite.py original.md candidate.md --protect-literal API_KEY --protect-quotes
```

- 扫描器仅覆盖简中和英语的有限字面规则，输出候选位置、理由和输入哈希。过度防御表达需要结合上下文判断；零命中不能说明文章已经自然。
- 正文检查器比较支持的 Markdown 保护片段、链接、占位符和数字表达，包括区间、比例、日期、单位及部分公式。默认的有限识别范围之外，可用指定原样片段补充保护。
- 机械通过后，仍需核对数字归属、条件、否定、因果、归因和确定性。Markdown 只覆盖部分语法，结果中的限制也需一并查看；Python 注释与 docstring 有各自的专用检查器。

检查范围、返回状态和文件证据用法见 [操作指南](docs/workflows.md)与[验证指南](core/yaya/references/validation.md)。正文扫描和比较工具每份输入上限为 2 MiB，使用 UTF-8 编码。

## 当前验证与开发

0.5.0 的交付验证共运行 350 项本地测试，无失败或错误，8 项因 Python 版本或链接权限跳过。CI 覆盖 Ubuntu、Windows 和 Python 3.10、3.13、3.14；另有可复现构建、安装校验与隔离回滚记录。

验证覆盖工具行为和已记录的案例，写作效果仍取决于宿主模型、材料与任务。去 AI 味规则针对表达模式；`origin` 审阅来源证据，不提供 AI 概率。单句口头禅无法可靠识别 GPT、Opus、DeepSeek 或豆包。

在仓库根目录运行测试和构建：

```text
python -m unittest discover -s tests -v
python scripts/build_release.py
```

`dist/` 包含核心 ZIP、三个可选语言 ZIP、`catalog.json` 和 `SHA256SUMS`。新增语言从模板开始；修改能力或规则时，提交能够说明问题的案例及实际验证结果。

- [0.5 升级说明](docs/upgrade-0.5.md)
- [30 轮迭代与 PR 台账](tests/results/2026-10-30-iterations30/README.md)
- [0.5.0 交付验收](tests/results/2026-10-30-iterations30/release-050/README.md)
- [贡献指南](CONTRIBUTING.md) · [语言包模板](templates/language-pack/README.md) · [语言包规范](docs/language-pack-spec.md)

[MIT License](LICENSE)
