# 0.3 命令与领域设计调研

核对日期：2026-10-30。以下记录实际查阅的项目或官方资料，以及本次采用的具体设计。
未复制第三方代码、规则集或品牌文案，也未把来源项目的效果统计用作 yaya 的成绩。

| 来源 | 看到的机制 | 本次采用 |
| --- | --- | --- |
| [Fabric README](https://github.com/danielmiessler/Fabric/blob/main/README.md) | 按任务组织 prompts；提供 pattern 选择、列表和读取入口 | 固定短命令与可发现目录；帮助直接来自实际任务契约 |
| [Vale styles](https://docs.vale.sh/topics/styles) | 规则明确检查对象、作用范围、消息和来源；规则组织为可选择的 style | 领域有明确适用范围、保护关系与来源；不把一套抽象“专业语气”施加给所有任务 |
| [Google technical tone](https://developers.google.com/style/tone) | 面向读者、直接说明、避免无用术语与套话 | 技术领域规则和读者选项分离；面向新手也保留准确接口语义 |
| [SEC plain writing](https://www.sec.gov/about/plain-writing-initiative) | 强调面向投资者的可理解表达 | 财务事实与通俗表达并存；不将美国规范当作全球合规结论 |
| [ASA p-value statement](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf) | p-value 不代表效应大小或假设为真的概率 | 数据领域保留效应、样本与不确定性，不用“显著”替代实际结论 |
| [ICMJE manuscript preparation](https://icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html) | 研究设计、结果、限制与结论相匹配；不同文章格式不同 | 学术领域保留引用和证据边界，不对所有文本强制套 IMRAD |
| [Mailchimp voice and tone](https://styleguide.mailchimp.com/voice-and-tone/) | 区分稳定表达习惯和随情境调整的语气，清晰优先 | 商务沟通按对象和情境表达；不导入其品牌人格或幽默要求 |

GitHub 文件由连接器读取。Fabric README 的文件 blob 为
`cc5d6b3b2e62a87a307cec439d0e67820111d468`，读取覆盖任务定位与 Usage；
Vale README 的文件 blob 为 `a55ce4e4c08453860b05c4631541bdb1e80b75e2`，分支为 `v3`。
这些是文件 blob，不冒充完整仓库 commit。网页来源为上述日期看到的版本，未宣称不可变。
最初读取旧 `errata-ai/vale` 文件路径失败；随后根据项目现址读取 `vale-cli/vale`。
Vale vocabularies 页面读取失败，未用其内容支撑具体实现。

## 取舍

1. 采用 Skill 对话命令与可移植帮助/计划工具。普通编辑继续用宿主模型，不引入 Fabric
   的模型账号、后台服务、全局 shell profile 或新执行框架。
2. `catalog.json` 定义命令和领域。解析器拒绝未知名称、重复单值选项、不适用选项及越界写入请求。
   它只产出计划，实际语义约束仍由宿主执行，不能把 JSON 计划当作完成证明。
3. 显式命令一次选择一个动作；辅助读代码属于注释任务的必要支撑。
   多动作由自然语言明确请求或分别调用，避免 `review` 随手改稿。
4. 首批 `tech`、`finance`、`data`、`academic`、`business` 是具体编辑适配，均标 experimental。
   不提供医疗/法律专业支持标签，不以词表命中率证明领域准确。
5. 先声明语义验收条件，再将仅含请求与原文的包交给独立执行者；保留完整输出和失败。
   结构回归、真实模型输出与语义判定分开报告。合成案例和未经人工校准的模型判断
   不证明行业通用准确率，也不自动证明比旧版更好。

上述来源说明设计选择的依据。Yaya 的实际效果见本仓库对应的执行记录。
