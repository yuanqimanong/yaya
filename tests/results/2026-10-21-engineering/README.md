# yaya 0.2.1：工程保真、验证与“这是 AI 吗”

核心已从 0.2.0 升级为 **0.2.1**，并同步到 `C:\Users\12761\.agents\skills\yaya`。维护源仍是 `D:\AIProjects\yaya\core\yaya`。两者是独立目录，任务开始时 26 个有效文件逐字一致，无额外安装定制；当前 31 个运行文件摘要全部一致，本轮同步 13 个文件。可选语言包仍为 0.2.0。

工作树开始时干净，Git 基线为 `ae2d17d642949ad21687bf7904688fd6aeaedf28`。修改前保存了当前工作树和安装副本，Git HEAD、状态、暂存/未暂存 diff 另外记录。未修改 finance-data-crawler 业务文件。

**可确认的提升是验证能力与编辑边界。当前定向样本没有证明模型语义保真显著提升，更没有测得作者来源分类准确率。**

## 实际修改与取舍

| 改动 | 实现与边界 |
| --- | --- |
| 编辑模式 | 纯润色、带证据编辑、只读审阅分别处理，沿用已有授权。普通编辑直接交付；没有固定诊断、评分或报告。 |
| 对象识别 | 普通注释、docstring、运行时说明字符串、数据库 comment 元数据、提示词分别识别；未授权对象只报告。 |
| 语义保真 | 对实际 diff 复核主体/对象、数量/单位/归属、条件/范围、否定/例外、确定性、时间、有效配置及完成状态。准确原文允许不改。 |
| 工程事实 | 先读局部代码，依赖覆盖、继承、调用链或接口契约时才扩展。修订以路径/符号/行号或样本支撑；保留缺陷可能性，不改业务代码来消除注释冲突。 |
| 普通注释验证 | 保留 `check_comments.py` 的严格模式、指令及示例保护；没有新增放行开关。 |
| docstring 验证 | 独立 `check_docstrings.py`；完整候选和具体节点/字面值摘要授权，保护其他字节、AST 结构及已识别示例。 |
| 具体授权 | `check_rewrite.py --allow FILE` 改为绑定原稿/候选摘要和具体差异的 JSON；拒绝旧式整类 `--allow numbers`。这是明确的兼容性变化。 |
| 批量证据 | `edit_evidence.py` 保存工作树原稿和独立 Git 基线；记录摘要、工具内容版本/依赖、命令、选项、Python 版本与 UTC 时间，识别过期报告并保留失败历史。 |
| “这是 AI 吗” | 独立只读路由，给出 AI 生成倾向、人工写作倾向或无法判断，并解释证据及替代解释；不编造概率、准确率或具体生成模型。 |
| 发布 | 构建器包含新增运行脚本与参考文件；核心 ZIP、catalog 和校验和已生成。 |

主 `SKILL.md` 为 **50 行**。专项内容放在 `references/engineering.md`、`comments.md`、`validation.md`、`authorship.md`；案例放在 `tests/evals/engineering.json`。没有追加禁用词表，词表零命中也不作为自然度、事实或来源证明。

用户可直接说：

```text
用 yaya 核对这份技术说明，结合配置和接口样本，只改已授权的文字。
只润色普通注释，保留 docstring、运行时字符串和数据库 comment。
这是 AI 吗？给出依据和不确定性，不要改写。
```

## 脚本与安装验收

技能升级的证据以 [unittest-final.json](unittest-final.json) 和 [原始验证归档](verification-raw.zip) 内的 `unittest-final.log` 为准，绑定当时的最终源码及测试摘要。随后整理 README、归档和 PR 时没有修改技能实现或测试代码。早期报告在 `history/`，不作为当前候选的验收证明。

| 检查 | 实际结果 |
| --- | --- |
| Python 3.13.5 全量 unittest | 运行 215 个测试；209 个完整方法成功；0 failure、0 error。 |
| 跳过 | 5 个完整方法跳过；另 1 个方法含 3 个子测试跳过，共 8 条跳过记录，均不计为成功。原因是 Python 3.14 t-string 或 Windows 链接权限。 |
| 代码输出机械边界 | 两版各 4 个候选，合计 passed 8、failed 0、unsupported 0；这是用新验证器检查两版产出，不代表旧版已有 docstring 工具。 |
| Skill 结构 | 使用现有带 PyYAML 的解释器执行 `quick_validate.py`，通过。默认及 bundled Python 缺少 PyYAML 的尝试未算通过，没有安装额外依赖。 |
| 发布构建 | 0.2.1 核心及 0.2.0 可选语言包构建成功，见 [build.json](build.json)。 |
| 安装 | 31 个运行文件与维护源 SHA-256 全部相同；安装后的普通注释、docstring 冒烟检查通过，见 [installation.json](installation.json)。 |
| diff 与回滚 | `git diff --check`、反向 patch 检查及两种回滚预演通过；隔离副本中实际恢复 20 个旧文件、移除 10 个新增文件，并验证拒绝覆盖后续编辑。 |

机械测试覆盖工具指令、未授权字符串/元数据/docstring、具体授权、示例转义绕过、UTF-8/BOM/CRLF、不支持语言/语法、旧摘要、工具变化、未执行检查、失败修复/排除及已有未提交修改。另有测试明确演示：**错误事实的授权 docstring 也可能机械通过**，因此 AST 通过不能当作事实正确或行为完全不变。

## 同模型旧版对照

使用任务开始时的实际 0.2.0 副本，与新版任务相关指导进行对照。16 个预设案例，每题两版输入、原始代码/配置/样本和目标模型设置相同，仅技能指导不同。生成者未见预期结果；每题使用独立 CLI 上下文。已加载指导的摘要均与实际交付内容一致，见 [guidance-current.json](semantic/guidance-current.json)。

目标为现有宿主配置的 `gpt-6.1-sol` / `max`，未切换模型、reasoning 或采样配置。CLI 为 `0.163.0-alpha.11`；精确服务端修订、随机种子不可得。有效矩阵为 32 份回答；一次容量错误后，仅对该案例补跑一次完整旧/新版对，原始失败和被替代的旧版成功回答均保留。

| 口径 | 旧版 | 新版 | 偏好 |
| --- | --- | --- | --- |
| 匿名模型原始判断 | 硬项通过 15/16，1 uncertain | 硬项通过 16/16 | 新版 2、旧版 0、平 14 |
| 主代理结合源码复核 | 硬项通过 16/16 | 硬项通过 16/16 | 新版 1、旧版 0、平 15 |

原始 uncertain 在 ENG09：旧版 notes 说旧注释检查器不验证 docstring 修改。匿名评审未获得该工具上下文；[旧版 comments.md 第 9 行](semantic/old-comments.md) 明确支持这句话，两版代码修改也相同。主代理据此解决该不确定项，原始判断没有覆盖。详见 [源码复核](semantic/source-review.json)。这不是独立人工校准，不能将该差异算作新版语义提升。

剩余的一项新版偏好在 ENG11：同样正确的状态统计，新版直接汇总 `unverified=2`，更容易核对，属于呈现差异。4 个“这是 AI 吗”案例中，两版均保持了适当的不确定性或流程证据判断；这些案例没有真实作者标签，**不能换算成分类准确率**。

| 案例 | 预设验收关系 |
| --- | --- |
| ENG01 | 首个非 None，保留 False、0、空值，区别于任一为真。 |
| ENG02 | 字符串 `"false"` 的 Python truthiness 与认证协议冲突；保留代码缺陷可能性。 |
| ENG03 | 默认/本地 HTTP_TUNNEL 与生产有效 HTTP_FIXED 分开。 |
| ENG04 | 90 天属于数据库留存，7 天属于看板默认查询窗口。 |
| ENG05 | 00…06 含首尾共七个阶段。 |
| ENG06 | 作者来自搜索 API，摘要来自详情 API。 |
| ENG07 | “可以正常”不能升级成“属正常”，保留全版本未确认。 |
| ENG08、ENG09 | 普通注释、授权 docstring、示例与元数据字符串分别保护。 |
| ENG10 | 已清晰准确的原文保持不变。 |
| ENG11 | failed、unsupported、人工核对、过期与未执行分别统计；失败不自动关闭。 |
| ENG12 | 计划上线不等于已经上线；默认值不等于生产有效配置。 |
| AI01…AI04 | 短文本、套话、嵌入指令、未经核验的人机协作记录；避免无证据来源鉴定。 |

完整 [输入与预期](semantic/cases.json)、[两版回答](semantic/outputs.json)、[原始判断](semantic/judgments.json)、[机械检查](semantic/mechanical-boundaries.json) 和 [原始统计](semantic/summary.json) 均保留。[原始证据归档](semantic/evidence.zip) 含冻结指导、当时运行器、命令、时间、事件、usage、摘要及失败日志；每个成员的原始摘要记录在 [归档索引](archive-index.json)，压缩前后已逐字节核对。模型没有执行指导包中的脚本；脚本验收另以最终源码的 unittest 和安装后检查为准。

## 失败和修订记录

- 新测试最初使用沙箱默认临时目录时遭遇权限错误；改为项目内夹具后重跑，没有删除断言或放宽保护。
- 首次 CLI 因状态目录权限无法初始化，记录保存在 [启动记录归档](history/cli-bootstrap.zip) 的 `engineering-paired-01/` 中；获准执行后的一题试跑不计入最终矩阵。
- 主生成的新版 AI04 遇到服务端容量错误。原记录仍为 failed，独立补跑完整对照后才获得有效样本，未换模型。
- 第二批 8 对评审输出后 CLI 超时，仍记 failed，未接受其输出。另发现收集器遗漏了 ENG09 明确要求的 notes，导致“未交验证说明”的误判。已修复收集器并增加回归测试；用原有答案、完整交付说明分为两批重审，均成功。原超时和错误材料仍保留。
- 匿名评审还受工具上下文缺失影响；ENG09 的旧版能力声明经源码证据确认。原判和主代理复核分别记录，不选择性丢弃不利结果。

详见 [execution-history.json](execution-history.json)。failed 的原记录不会改写成 passed；有效替代结果单列。unsupported、人工/代理复核和未验证也不会进入机械 passed 计数。原始 unittest 日志和补丁也按字节归档到 `verification-raw.zip`，保留原有空白与摘要，不为通过源码格式检查而改写取证内容。

## 未覆盖边界与下一阶段

- **语言/语法**：普通注释检查仍只支持当前解释器可解析的 Python；其他语言返回 unsupported。实际替代需记录宿主解析器、diff 检查和项目测试，未执行时保持未验证。本轮没有宣称完成 JS/TS 或数据库迁移验收。
- **docstring**：UTF-8、既有节点、单 STRING token、保持行结构；隐式拼接、重新折行、示例编辑不在放行范围。未标记示例及项目自定义文档语法仍需具体保护和复核。`__doc__` 会改变，依赖反射、帮助文字或文档生成的集成需要项目测试。
- **批量范围**：快照工具处理显式计划的既有文件；新增/删除、普通注释与 docstring 混合改动链需要单独记录和复核。不会为覆盖这些场景而降低现有模式的保护。
- **模型证据**：简中合成定向回归、每条件单次有效输出，规则与案例共享部分概念；不是隐藏测试、跨模型重复实验或母语人工评审。CLI 沿用宿主配置，工具未物理移除，合格日志仅能说明未观察到工具活动。
- **作者来源**：未建立经同意且具有真实来源标签、跨作者/题材/模型的校准语料；误报率与准确率未知。下一阶段应先建设这种数据和混写/润色控制，再决定是否提供数值分类器；当前版本不伪造该能力。
- **后续工程支持**：如需 docstring reflow、多 token、任意示例或其他语言，先增加具体语法支持和对抗用例，再启用；本轮以明确 unsupported/独立复核交付。

## 回滚

恢复材料：[完整恢复包](yaya-0.2.1-recovery.zip)、[原始补丁归档](verification-raw.zip) 内的 `upgrade.patch`。恢复包也包含相同 diff，以及本次升级前源码、完整旧安装、副本摘要、候选摘要和恢复脚本。临时运行目录已在后续 README/PR 整理中清理；正式验收证据和恢复包保留。

从项目根目录将恢复包解压到一个尚不存在的目录：

```powershell
Expand-Archive -LiteralPath '.\tests\results\2026-10-21-engineering\yaya-0.2.1-recovery.zip' -DestinationPath '.\.tmp\yaya-0.2.1-recovery'
```

先预演，确认范围后再添加 `--apply`：

```powershell
python D:\AIProjects\yaya\.tmp\yaya-0.2.1-recovery\restore.py --scope installed
python D:\AIProjects\yaya\.tmp\yaya-0.2.1-recovery\restore.py --scope source

python D:\AIProjects\yaya\.tmp\yaya-0.2.1-recovery\restore.py --scope installed --apply
python D:\AIProjects\yaya\.tmp\yaya-0.2.1-recovery\restore.py --scope source --apply
```

两种范围可分别恢复。恢复包绑定本轮技能升级时的文件；随后新增的 README 安装说明属于后续编辑，源码范围会拒绝覆盖这些变化，需要先保留并手动合并。安装副本可单独恢复。恢复过程不使用 `git reset`，保留验收历史。隔离回滚与后续编辑保护的实际结果见 [recovery-test.json](recovery-test.json)。
