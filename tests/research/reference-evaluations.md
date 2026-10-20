# 同类项目如何评测：公开实现核查

核查日期：2026-10-20。目标：为 yaya 的全量测试选择可执行、可复核的做法。

**结论：应采用“确定性回归 + 改写行为评测 + 独立语义复核”三层证据。** 规则命中、保护片段未变、模型协议完整、文本更好读，是四种不同结论，不能由一项测试替代其他三项。尤其不能把词表低分解释为“人类写作概率”，也不能把全部复制原文视作成功改写。

本次读取了仓库目录树、测试源码、fixture、runner、评分协议和已发布结果，没有运行这些外部项目，也没有复制它们的语料。下面描述的是公开实现与证据强度，不是本次实测成绩。所有源码链接固定到本次 GitHub 分支查询返回的完整 commit SHA；issue 的内容可能继续变化。

## 固定修订与总览

| 项目与固定修订 | 实际评测层级 | 语言 / 场景范围 | 可直接借鉴 | 不能据此宣称 |
| --- | --- | --- | --- | --- |
| [shuorenhua](https://github.com/MrGeDiao/shuorenhua/tree/6c4b9353b87185c26e684c4525be1af47f82fee9) `6c4b9353b87185c26e684c4525be1af47f82fee9` | 协议单测、冻结模型运行、独立保真 / 任务 / 编辑质量判分 | 中文优先，主集含英文及代码；不同编辑范围 | 硬项与质量分离，正常文本反例，简单提示 baseline，正向收益防守 | 一次运行代表所有模型；历史词表指标等于语义质量 |
| [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing/tree/209815cdeb4af942616daec89a5e0a706c804e3a) `209815cdeb4af942616daec89a5e0a706c804e3a` | regex detector / preservation validator 单测；冻结比较 harness；独立自动化场景门槛 | 所读 48 条比较用例为英文，覆盖 6 种 profile | 正反例与 mutation controls；保护内容检查；完整输出和 provenance 校验 | detector 低分证明文笔好；历史比较 harness 已全部执行 |
| [speak-human-tw](https://github.com/Raymondhou0917/speak-human-tw/tree/fbac573c7e1bb9f41759d52ae2b9125afc6d22ca) `fbac573c7e1bb9f41759d52ae2b9125afc6d22ca` | Markdown benchmark，人工执行 / 双模型交叉判分 | 繁体中文、台湾用语；社群、电子报、销售、客服、办公文书 | SF / SNF 成对，不用同族套话替换，按交互模式冻结预期 | 这是盲测；42 条当前用例已由旧版 40 条结果覆盖 |
| [your-voice](https://github.com/parasdoshicom/your-voice/tree/e92148bdd28ebb33ff78a017302b64075eb78caf) `e92148bdd28ebb33ff78a017302b64075eb78caf` | 确定性 verifier / judge 计分单测；有归档输出的三臂实验与盲审材料 | 所读简洁性实验为英文合成写作请求；包含关系、解释、道歉等任务 | no-skill / old / candidate 对照；保留失败版本；单独评意义与沟通效果 | 模型盲审等于人类认可；示例 human_label 代表真人标注 |
| [blader/humanizer](https://github.com/blader/humanizer/tree/8c307f367c91bd974002f10f2be2965d642c13df) `8c307f367c91bd974002f10f2be2965d642c13df` | 仓库内可执行检查主要为包与文档一致性；另引用外部实验 | 包检查不建立语言质量覆盖 | 区分包装验证与外部质量证据 | 仓库 CI 已执行 README 引用的盲评 |

## 1. shuorenhua：从字符串指标转向独立编辑判据

### 读到了什么

- [suite.json](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/evals/v2.5/suite.json)：123 条；本次按字段计数得到 58 条 `normal=true`、7 条 `positive=true`。每条保存原文、中性请求、旧编号；英文原文和代码注释也存在于主集中。
- [criteria.md](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/evals/v2.5/criteria.md)：独立评价 `fidelity`、`task`、`quality`，明确不评价作者是不是 AI。
- [runner.py](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/automation/eval/runner.py)：`validate_plan` 禁止 rewrite 阶段带 judge 的 outputs / rubric；`prepare` 快照并哈希候选；运行校验模型身份、输入、持久会话和工具边界；`report` 将运行完整性与内容状态分开。
- [protocol.py](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/automation/eval/protocol.py) 与 [test_protocol.py](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/automation/eval/test_protocol.py)：拒绝缺题、重复 ID、未知 ID、重复 JSON key、额外字段；judge 必须提供证据；`review` 不被合并为通过。

### 具体评什么

信息保真不只是找数字：判据要求核对实体与数字配对、主体动作、归属、范围、条件、否定、时态、情态、比较和强度。任务检查另管输出类型、语言、编辑范围及原文内指令边界。编辑质量允许 `better / same / worse / review`、多个好答案及不改原文；未删某个词或句式不自动失败。[判据源码](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/evals/v2.5/criteria.md)

门槛包含两面：正常文本误改率按模型单独统计，分子是 `quality=worse` 或硬项失败的题目并集，阈值 `<10%`；7 条冻结正向样本至少 5 条 `better`、其余不能 `worse` 且硬项全过，防止原样返回钻空子。简单提示、旧规则、新规则必须在同模型同核心集上盲比，偏好不抵消硬失败。[同一判据](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/evals/v2.5/criteria.md)

### 字符串测试与实际改写的界线

旧 [hard_metrics.py](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/automation/eval/hard_metrics.py) 计算长度、破折号、残留词和保护 token 等。新的[运行说明](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/automation/eval/README.md) 明确它不能直接解析新版 JSON，也不是语义判官。上述 protocol 单测证明协议校验器能抓坏记录，不能证明新输出事实无误。

### 实际结果与未覆盖项

[v2.6.0 记录](https://github.com/MrGeDiao/shuorenhua/blob/6c4b9353b87185c26e684c4525be1af47f82fee9/evals/results-v2.6.0.md) 报告主集 123/123 有效，同时披露 B-33 有信息 / 任务失败、B-06 质量变差；新模式小测中 Claude 未达到全部预设门槛，维护者仍决定发布。因此“有发布版本”不能反推“所有原定门槛全过”。该记录也说明判官更换后分数不宜直接同比，mini 未单独验证，模型判分不等于人类共识，完整 CLI 会话未公开。它的优点是披露限制，而不是证明普遍可靠。

## 2. avoid-ai-writing：检测引擎、保真检查、改写实验明确分层

### 真实单测

[detector/patterns.test.js](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/detector/patterns.test.js) 直接调用 `analyzeText`，断言 issue、分数、跨度、长度边界、Markdown masking 和性能。它有必须命中的例子，也有普通否定句、版本标题分隔符、技术语境等不得误报的例子。这是规则扫描器回归，不是模型生成评测。

[detector/validate.test.js](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/detector/validate.test.js) 用人工构造的 before / after 测代码块、引文、表格、URL、路径、frontmatter 等保护规则，并测试“detector 分数下降但 protected token 丢失仍失败”。数字丢失与大幅缩短在部分校验中只是 warning；这些检查不验证命题、否定或因果关系。

### 历史比较 harness 的设计

[cases.json](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/evals/rewrite/cases.json) 有 48 条英文合成用例：clean、clear-edit、context、preservation 各 12 条；development 36、heldout 12。六种 profile 为 linkedin、casual、technical-blog、docs、blog、investor-email。fixture 保存原子 claims、逐字保护片段、允许修改和 preserve / change 预期；作者与文档跨 split 不重叠。

[protocol.json](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/evals/rewrite/protocol.json) 冻结 baseline / candidate / simple 三臂、每题每臂 3 次、仅 rewrite 模式。三个独立失败维度是信息损坏、不必要修改、漏掉应改问题。

[scripts/rewrite-eval.js](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/scripts/rewrite-eval.js) 的实际约束比普通结果表更强：

- `prepare` / `checkPlan` 从 pinned Git commit 重读规则和语料，校验 prompt、任务清单与 hash，防止看完结果再改计划。
- `extractFinalText` / `checkResults` 要求完整的边界内最终输出，不能挑选有利子串；核对模型、provider 和 prompt hash。
- `blind` 随机顺序并分配匿名 alias；`checkKey` 检查一对一映射；`report` 拒绝重复裁决，缺失结果或人工裁决不算完整。
- [rewrite-eval.test.js](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/scripts/rewrite-eval.test.js) 实际构造了 split 泄漏、篡改 source / prompt、减少重复次数、截取输出、非法 ballot 等反例。测试末尾明确表示未进行模型比较。

### 已执行与未执行必须分开

[比较说明](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/evals/rewrite/README.md) 明确历史 pilot 的基础设施及合成 plumbing 输出不证明质量；其人工盲审路线不能因后来采用自动门槛而被改称“已完成人工验证”。它也承认 literal phrase 检查会错杀未列出的等义改写，并可能放过包含目标词的矛盾句。

当前[自动化门槛](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/evals/rewrite/automated-gate.md) 改用至少两个 editor 模型家族、独立模型复核、冻结输入、保留失败、明确工具可用性；包含 useful edit、no-op、保真、技术例外、保护片段、显式转换、内嵌指令和 detect scope。文档自称自动化回归，不声称普遍写作质量提升。批量案例共享上下文，不是独立样本；提供工具中间状态也不证明真实文件修改发生。

另一个重要边界是 [PROOF.md](https://github.com/conorbronsdon/avoid-ai-writing/blob/209815cdeb4af942616daec89a5e0a706c804e3a/PROOF.md)：文档自扫描区分 raw 与排除示例后的分数，预算只是回归上限。它公开说明低分不证明写得好或由人写，并报告既有语料的聚合分数区分能力很弱。yaya 不应借用它的 score 作为“去 AI 味成功率”。

## 3. speak-human-tw：可读的正反例与交叉判分，盲测较弱

[benchmark.md](https://github.com/Raymondhou0917/speak-human-tw/blob/fbac573c7e1bb9f41759d52ae2b9125afc6d22ca/evals/benchmark.md) 当前为 42 条，27 SF（应改）和 15 SNF（不应误改）。反例覆盖真实排比、一次合理对比、正式公告、技术用语、讨论 AI 词语本身、真实口语碎片等；它还检查台湾用语和标点，不宜直接当作简体中文或英文规范。

[run-eval.md](https://github.com/Raymondhou0917/speak-human-tw/blob/fbac573c7e1bb9f41759d52ae2b9125afc6d22ca/evals/run-eval.md) 每题同时看问题处理 / 正常文本放行、保护清单、不换成同族空话；长文另看句子及节奏保留。发布目标是 SF ≥90%、SNF 误杀为 0。规则新增时要求配反例，另有原文内指令测试。

但公开执行提示要求改写端直接读含问题与预期的 benchmark，并区别 SF / SNF 作答。因此这是“知道用例标签的回归”，不是预期隐藏的盲测。判分端不加载 skill，可减少一部分规则跟随，却不能消除生成时的答案泄漏。所读目录树没有独立测试 runner 或质量测试单元文件；主要是人 / Agent 按文档操作。

[results-v1.4.0.md](https://github.com/Raymondhou0917/speak-human-tw/blob/fbac573c7e1bb9f41759d52ae2b9125afc6d22ca/evals/results-v1.4.0.md) 实际报告的是 40 条而非当前 42 条。它披露交互 / 非交互模式预期不一致造成争议，三次“新增事实”怀疑经对照原文被推翻；这是需要证据复核的具体案例。该结果还明确“人味”八个目标未测、交互模式未完整回归，也没有 baseline、随机盲比、重复运行或真人读者质量验证。报告中的 96% 不应扩展为这些能力的通过率。

## 4. your-voice：对照实验、盲审和对自身评测的审计

### 确定性检查的真实边界

[verify_benchmark_output.py](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/scripts/verify_benchmark_output.py) 检查指定词、禁止词、精确命令 / URL、数值 token、句子块及长度。`_verify_concision` 的注释明确：只能检查表面约束，交付条件仍需人工理解。[test_verify_benchmark_output.py](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/tests/test_verify_benchmark_output.py) 验证大小写敏感保护片段、数字完整 token、虚构百分比和注入内容等反例。这些测试有用，但字符串齐全不意味着条件关系正确。

[score_judges.py](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/scripts/score_judges.py) 按 failure mode 和 train / dev / test split 单独计算人工 Pass 的命中率与人工 Fail 的拒绝率，缺少某类标签时结果为未定义，并检查每类样本量。[test_score_judges.py](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/tests/test_score_judges.py) 覆盖双向误判、小样本、证据缺失和 split 过滤。这里的 `TPR` 正类被定义为 Pass，使用时应避免与“缺陷命中率”的正类约定混淆。

### 真正执行过的比较

第二阶段 [run_experiment.py](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/evals/concision-rerun-2026-09-22/stage-2/run_experiment.py) 读取 12 条 heldout 合成请求；none / old / candidate 三臂、各 2 次，共 6 个批量 Codex 会话。脚本随机用例及 job 顺序，只把 ID / request / source 放进生成请求，保存 prompt hash、CLI 版本、解析到的模型信息和输出完整性。它依赖原宿主的配置与路径，不能原样视作通用 runner。

[prepare_review.py](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/evals/concision-rerun-2026-09-22/stage-2/prepare_review.py) 对 72 份稿件做 exact span、word range、punctuation-only 检查，打乱后只给 reviewer 匿名 `sample_id`、请求、原文和草稿，单独保存 arm 映射。它不生成评审结论。

[review-protocol.md](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/evals/concision-rerun-2026-09-22/review-protocol.md) 用两个 Agent 分别评“必要意义损失 / 无根据确定性”和“缩短后是否仍能完成沟通目的”。不以最短为最好，要求先给片段证据再给 Pass / Fail。但没有真人标签或 few-shot 校准，评审 Agent 的完整宿主上下文与精确设置未独立归档。

### 结果与审计的价值

[实验说明](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/evals/concision-rerun-2026-09-22/README.md) 保留失败的 stage 1；两阶段都未达到预设“缩短一半”目标。其[评测审计](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/reports/2026-09-22-eval-audit.md) 进一步指出：旧 baseline 的 48 份稿件只有 2 份被判冗长，目标失败几乎未出现；96 份输出不等于 96 次独立试验；CI 只测结构工具，没有重跑写作行为；合成 `human_label` 是格式示例，不是人工事实。

它的[评测政策](https://github.com/parasdoshicom/your-voice/blob/e92148bdd28ebb33ff78a017302b64075eb78caf/references/evaluation.md) 值得参考，但应与已达成证据分开：同模型同设置 baseline、隐藏真人参考答案、按来源事件切分、写作与编辑分开报告、语义作为硬门槛、用目标作者的 heldout 标签校准 judge。政策建议不等于已实际完成人工校准。

## 5. humanizer：不要把包验证或外部 issue 统计当成项目内部 benchmark

固定修订的 [scripts/validate-package.py](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/scripts/validate-package.py) 校验 metadata、版本、插件路径、README 与 SKILL pattern 编号 / 名称一致性以及字数预算。目录树没有仓库内 tests / fixtures / evals 质量 runner。可以据此说明所读提交的 CI 验证内容，不能断言项目从未有外部质量研究。

外部贡献者的 [issue #229](https://github.com/blader/humanizer/issues/229) 报告“rewrite 相对 raw 的 16/16 偏好”，并链接另一个研究仓库；同一 issue 明确 judge 都来自一个模型家族、计划 144 次质量比较只完成 77 次、人类对照未匹配主题，而且质量偏好收益没有转化为检测规避。此处未复核其外部 tally / corpus，故只记录为**贡献者报告，非本次复现**。issue 最后更新时间为 2026-09-28，未固定不可变修订。

## yaya 本轮可采用的五条建议

1. **分开报告三层通过情况。** 确定性测试测安装 / 解析 / 扫描 / 保护片段；模型运行测真实调用、完整覆盖和输出契约；语义复核测事实与任务。报告必须同时列出“已执行、失败、未执行”，不要用全局绿色覆盖缺口。
2. **先冻硬门槛，再看自然程度。** 为每题标注必要命题、数字与实体的配对、否定 / 条件 / 情态、逐字保护片段和允许修改范围。判分分别保存 `fidelity`、`task`、`quality` 与原文 / 输出证据；硬失败或未裁决 review 不被风格收益抵消。数字匹配只作初筛。
3. **正反例成对，并阻止 no-op 投机。** 同时覆盖必须改的问题、含相同词但合理的普通文本、技术术语、引用、长文、代码 / URL、源文指令和语言保持。正常文本误改与应改文本漏改分别计数；至少一组冻结样本必须观察到实际编辑收益。简体、繁体、英文和可选语言分别报告，不能互相外推。
4. **同条件对照并隐藏预期。** 比较无 skill / 简单提示与 yaya；有规则变更时增加旧版。固定模型、上下文、工具、请求、来源和预算；生成者只见请求与原文，reviewer 见匿名随机输出。由不同 reviewer 独立检查意义和可用性；没有真人标注时明写“模型评估，尚未校准”。
5. **保留首轮、失败和可复算分母。** 保存 skill / case / prompt hash、有效模型身份、完整输出、时间 / 用量、错误及裁决。重试另留记录，不覆盖坏结果；缺题、截断、协议失败不能排除后算通过。合成样本、同源变体与批量会话不冒充独立真实事件，公开用例参与调参后也不能再声称是未见留出集。

这些建议借鉴的是评测结构，不直接沿用别人的通过率或门槛。yaya 的本轮结果应以实际执行范围和预先确定的验收标准为准；没有 baseline、独立质量裁决或真实运行证据时，明确限制即可，不补写不存在的成绩。
