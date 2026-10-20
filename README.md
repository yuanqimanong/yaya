# yaya · 牙牙学语

[English](README.en.md) · [安装](INSTALL.md) · [贡献语言包](CONTRIBUTING.md) · [包规范](docs/language-pack-spec.md)

yaya 是一个编辑 Skill，使用你当前的 AI 工具，帮你删去空话、理清表达，也能整理代码注释、优化提示词和学习样稿风格。可以直接改写，也可以先审稿；编辑时保留原意、作者口吻和任务要求。

默认包含简体中文和英语，繁中、日语、韩语按需安装。普通编辑无需额外服务或模型 API。

## 直接这样用

```text
用 yaya 去掉这篇文章的 AI 味，保留作者口吻和有用细节。
只看看这段话哪里空泛，说明原因，先不要改。
用 yaya 以金融领域风格润色 report.md，普通读者也要看得懂。
用计算机领域风格重写这份代码的普通注释，保留代码和工具指令。
优化下面的提示词，去掉空泛表达，保留变量、输出格式和全部限制。
让这个提示词要求 AI 用普通读者能懂的语言回答。
学习下面这段话的风格，给我可复制的风格提示词和一个新例子。
用香港繁体中文润色这段说明，保留原有地区用语。
```

| 功能 | 能做什么 |
| --- | --- |
| 去 AI 味与审稿 | 找出空泛铺垫、宣传语、翻译腔和机械重复，结合语境决定是否修改。 |
| 正文与文件润色 | 按指定用途、读者和风格调整文字，保留事实、数字和不确定性。 |
| 代码注释 | 结合代码改写注释，保留程序和工具指令。 |
| 提示词优化 | 整理提示词的措辞和结构，保留变量、输出格式和执行要求。需要改变 AI 的回答风格时，在请求中说明。 |
| 学习样稿风格 | 提炼表达习惯，生成可复制的风格提示词与示例。需要保存时，在请求中指定。 |

说“改写”就得到修改后的文字，说“只检查”就得到问题和建议，说“修改这个文件”就编辑指定范围。原文已经合适时可以保留；要求换语气或重组时，按请求调整。学习样稿会提取表达习惯，不会把作者的身份、经历或观点带入新内容，也不涉及模型训练。

## 本地试用与开发

从 [GitHub 仓库](https://github.com/yuanqimanong/yaya) 获取源码：

```text
git clone https://github.com/yuanqimanong/yaya.git
cd yaya
```

临时试用时，让 AI 读取 [SKILL.md](core/yaya/SKILL.md)，再提交编辑请求。需要自动加载时，将完整的 `core/yaya/` 目录安装到所用 AI 工具的 Skill 目录，具体步骤见 [安装指南](INSTALL.md)。

当前版本为 **0.2.0**，尚未提供公开 Release 下载。可在仓库根目录测试并构建：

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
| 简体中文 `zh-Hans`、英语 `en` | 是 | `yaya-core-0.2.0.zip` |
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
```

| 工具 | 实际检查范围 |
| --- | --- |
| `detect_tells.py` | 仅支持 `en` 和 `zh-Hans`，扫描有限词句候选并输出位置和原因。命中需结合语境判断，不输出 AI 概率。 |
| `check_rewrite.py` | 比较支持的 Markdown 片段、链接目标、数字及已识别单位、占位符等。支持的成对引号内容需 `--protect-quotes`，其他指定原样片段需 `--protect-literal`。 |
| `check_comments.py` | Python `.py` / `.pyi` 普通 `#` 注释的修改边界，保护代码、字符串、行结构和已识别工具指令；不支持增删或移动注释行。 |

这些工具只读文件。前两个正文工具接受每份不超过 2 MiB 的 UTF-8 输入。检查通过后仍需核对语义：数字是否属于原来的对象，条件、否定和归因是否保留。数字检查比较未保护正文中数字与已识别单位的内容和出现次数，无法确认归属，也可能漏掉未列出的单位变化。

Markdown 扫描器支持有限语法；识别到缩进块、列表内围栏、脚注、多行链接或原始 HTML 块等结构时，会返回不支持。它无法识别所有超出范围的结构，请一并查看 JSON 中的 `limitations`。Python 源码须能被当前解释器解析；其他编程语言的注释需要宿主解析器或人工检查。

工具需要 **Python 3.10+**，仅使用标准库。二进制文档读取和版式处理使用宿主已有工具。

## 为你的语言贡献支持

从 [语言包模板](templates/language-pack/README.md) 开始，编写 `pack.json`、`GUIDE.md`、`examples.md` 和 `LICENSE`；需要专项规则时添加 `PATTERNS.md`。同时提供值得改写和应当保留的例子，通过校验后提交。新增语言沿用同一套加载和安装流程。

语言标识、版本、文件格式和审核要求见 [语言包规范](docs/language-pack-spec.md)。模板中的 `fr` 是法语编写示例，尚未作为支持包发布。

安装、升级和回滚见 [安装指南](INSTALL.md)；版本改动见 [0.2 升级说明](docs/upgrade-0.2.md)；设计和实测结果见 [设计说明](docs/design.md)、[验收记录](tests/README.md)。

[MIT License](LICENSE)
