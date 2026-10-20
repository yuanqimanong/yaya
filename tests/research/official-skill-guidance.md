# 官方 Skill 文档核查

查阅日期：2026-10-20（Asia/Singapore）。本记录来自官方网页正文的只读检索与打开，未执行网页示例、安装插件或运行模型。以下是设计依据及项目映射，不是 yaya 效果评测或官方认证。

## 实际读取的来源

| 编号 | 官方页面与 URL | 本次读取的相关部分 |
| --- | --- | --- |
| A | [Agent Skills — Specification](https://agentskills.io/specification) | `SKILL.md` 格式、可选目录、Progressive disclosure、File references、Validation |
| B | [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills) | 渐进加载、ChatGPT/Codex 的调用方式、描述边界、Best practices |
| C | [Anthropic — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Concise is key、Progressive disclosure patterns、Build evaluations first、Create verifiable intermediate outputs |
| D | [OpenAI — Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills) | 成功标准、显式/隐式调用与反例、确定性检查、基于 rubric 的定性评估 |

## 对当前 yaya 的五项映射

| 主题 | 文档依据 | yaya 的对应做法与保留边界 |
| --- | --- | --- |
| 入口清楚、简短 | A 要求 `name` 和描述用途/触发条件的 `description`；B 要求明确范围，并用请求测试触发行为。 | [SKILL.md](../../core/yaya/SKILL.md) 描述文字编辑任务，以表格选择正文、注释、提示词等指导。后续应按误触发或漏触发证据调整描述，不能只靠关键词数量判断质量。 |
| 按任务加载 | A、B、C 都区分元数据、激活后的主文件及按需资源；A、C 建议把详细材料移到独立文件，避免深层引用链。 | 主入口直接链接任务指南；再按语言选择 `PATTERNS.md` 或 `GUIDE.md`，只读取所需内容。语言包的独立安装与解析是 yaya 自己的实现，不是官方规定的分包方式。 |
| 脚本承担可确定的部分 | B 优先使用指令，仅在需要确定性行为或外部工具时增加脚本；A 要求脚本明确依赖、错误和边界。 | 本地脚本负责包校验及可机械比较的保护项。`check_rewrite.py` 和 `check_comments.py` 的通过结果不能替代语义判断；普通编辑仍由宿主模型完成。 |
| 文件修改保留可验证候选 | C 对复杂或高风险操作建议先生成可验证的中间结果，再执行并复核。 | [正文指南](../../core/yaya/references/text.md) 用原稿与候选做只读比较；[主入口](../../core/yaya/SKILL.md) 要求限定修改范围并保留可恢复原稿或 diff。此建议不要求每次普通润色都生成计划文件、审批或多稿。 |
| 分开评估行为与表达 | C 建议以代表性任务的无 Skill 表现为基线，按实际缺陷迭代；D 区分成功标准、运行记录、确定性检查和定性 rubric。 | [评测流程](../evals/README.md) 应分别报告任务完成、意义保留、表达质量及机械结果，保留输入、配置、输出和失败。格式合法、指令较短或脚本通过都不能单独证明编辑效果改善。 |

Agent Skills 的结构校验针对 Skill 元数据和命名；yaya 的 `format_version: 1` 是项目自己的语言包数据协议。两者不能混称。上述来源只支持这些设计选择；实际写作效果、跨模型稳定性及母语质量仍以对应运行和审阅证据为准。
