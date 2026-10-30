# 过度防御与模型口头禅：0.3.1 调研

查阅日期：2026-10-30。研究对象是编辑模式及误删控制。没有安装下列第三方技能，
没有复制其实现或整段规则，语言示例为本项目原创。文件 blob 仅标识查阅的文件，
不是仓库 commit；网页反映查阅当日版本。

## 开源项目提供的经验

| 来源 | 核实内容 | yaya 的取舍 |
| --- | --- | --- |
| [Kiterlin/anti-defensive-writing](https://github.com/Kiterlin/anti-defensive-writing/blob/main/skill/anti-defensive-writing/SKILL.md) | 专门讨论围绕假想批评者展开的辩解；区分无用免责声明、范围条件、方法限制和有效比较 | 以信息作用决定删留；保留影响结论有效性和读者行动的限定，合并重复而不吞掉不同条件 |
| [blader/humanizer](https://github.com/blader/humanizer/blob/main/SKILL.md) | 处理否定对比及跨句形式，保留真实纠错；检查叠加缓和词和资料缺口 | 读完整上下文，直接呈现原文已有主张；没有依据时不补造更具体的正向结论 |
| [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing/blob/main/dist/avoid-ai-writing.md) | 先列候选再判断；普通 not-only / not-but 关联结构保留为语义判断；自述部分词频说法没有本项目数据验证 | 不禁用句式，不将别人的词频/准确率声明移植为本项目证据；原文判断和来源判断分开 |
| [itsryanlenk/humanist](https://github.com/itsryanlenk/humanist/blob/main/README.md) | 区分改写、扫描与篇章审阅；README 报告曾因人类文本误报而降低否定排比检测等级 | 此次不增加宽泛对比正则；直接性由宿主结合语境判断。该项目实验未在此复现，数字不作 yaya 成绩 |

查阅的文件 blob，依表格顺序：

1. `c756be063b4cdc344394a5e7d4e9ae95d839e5f8`
2. `19fc634208e8cc6ae55d4ff287152583216fd244`
3. `573011ffe6319e4604e23d463e154d8fd27e4d5e`
4. `f2c808a1d3ab34c89ebf99ee20cb290a44f5fe86`

部分外部改写示例会以具体方法、范围或效果替换空话；只有原文支持这些信息时才能采用。
yaya 只使用上述决策思路，不照搬可能补入事实的示例。

## GPT、Opus、DeepSeek、豆包能否各列口头禅

| 对象 | 本次证据 | 可得结论 |
| --- | --- | --- |
| GPT | [OpenAI 模型使用指南](https://developers.openai.com/api/docs/guides/latest-model#personality-and-writing-style) 明确讨论重复措辞、过多格式和引入无关替代项的对比，并提供风格调整提示 | 官方资料承认这些写作倾向值得调节；不能据此估计所有 GPT 版本的频率或把句式视为独有指纹 |
| Claude Opus | [Opus 4.6 公开系统提示](https://platform.claude.com/docs/en/release-notes/system-prompts/claude-opus-4-6) 包含具体用词/排版偏好，也有金融法律场景的限定要求 | 提示词可影响表面风格；这是某版本、某产品的配置，不是 Opus 全系列输出统计 |
| DeepSeek | 检索模型名、写作口头禅、否定对比和 GitHub 项目，所得相关材料不足以建立可比样本 | 本轮没有足够证据归纳独有短语或频率 |
| 豆包 | 同类检索主要得到第三方接入与提示词项目，没有足够的受控写作对照 | 本轮没有足够证据归纳独有短语或频率 |

没有对四家 API 进行并行实测，也没有获得控制版本、语言、系统提示和任务的横向语料。
“某模型可能出现这类模式”和“这些词能识别某模型”是不同的证据要求。
当前建议按可观察模式编辑，保留品牌作为用户提供的背景，不建立品牌黑名单。

## 落实方式

- `human` 默认检查无效对比、假想反驳、防御性铺垫、重复限定和其他已有去套话决策。
- `human/review --focus direct` 仅处理直接性问题；其他风格保持原样。
- 双语例子同时覆盖删改与保留；技术、金融、数据、学术和商务约束继续生效。
- `detect_tells.py` 不增宽泛正则，避免以词法命中冒充语义诊断。
- [案例集合](../evals/directness.json) 包含首轮预先声明的 24 条，以及观察到句子功能疑点后
  增加的 2 条控制例；各轮冻结后交给独立执行者，生成包不含检查标准。
  实际输出、失败、复测和验证限制在 [本轮报告](../results/2026-10-30-directness/README.md) 单独记录。

自然程度没有统一的可计算分数。此次目标是可核查地减少冗余、保留事实关系与作者口吻，
不会用字数变少、禁用词次数或“AI 概率”代替质量判断。
