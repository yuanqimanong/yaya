# 可选语言包实际安装与解析记录

- 运行日期：2026-10-19。
- 工作目录：`D:\AIProjects\yaya`。
- 使用 Skill：`core/yaya/SKILL.md`。
- 按任务需要读取：`references/language-packs.md`、`references/text.md`、`references/prompts.md`、`references/style-learning.md`。
- 使用现有 `dist/` ZIP 和 `dist/catalog.json`，未重新构建。
- 未读取 evals、tests 或其他模型输出；未修改源文件。
- 所有写入均在 `.tmp/language-smoke/` 内。安装数据目录为 `D:\AIProjects\yaya\.tmp\language-smoke\data`。
- Python 实际路径：`D:\env\miniconda3\python.exe`。

## 安装

每个 SHA-256 均从本地 `dist/catalog.json` 对应条目读取，传给实际执行的 `packs.py install`。三次命令退出码均为 `0`，stderr 均为空，返回 `status: installed`、`backup: null`。

| 包 | 归档文件 | SHA-256 | 状态 |
| --- | --- | --- | --- |
| zh-Hant | yaya-lang-zh-Hant-0.1.0.zip | 1213a10c16b12781770047e82b2f1d4f6d86fc50078dbfbd795c5ed0047e3588 | installed |
| ja | yaya-lang-ja-0.1.0.zip | fa8d7f67beda4fc72da1e94ca400d859a3607d9334b22ca403c9db1544e68a52 | installed |
| ko | yaya-lang-ko-0.1.0.zip | b659d61b43f164b19bcd27e43bcc70a788852d0763d068f76486ba8d1fcd85fe | installed |

命令模式（实际参数见 `install-results.json`）：

```powershell
python core/yaya/scripts/packs.py install dist/yaya-lang-zh-Hant-0.1.0.zip --data-dir .tmp/language-smoke/data --sha256 1213a10c16b12781770047e82b2f1d4f6d86fc50078dbfbd795c5ed0047e3588
python core/yaya/scripts/packs.py install dist/yaya-lang-ja-0.1.0.zip --data-dir .tmp/language-smoke/data --sha256 fa8d7f67beda4fc72da1e94ca400d859a3607d9334b22ca403c9db1544e68a52
python core/yaya/scripts/packs.py install dist/yaya-lang-ko-0.1.0.zip --data-dir .tmp/language-smoke/data --sha256 b659d61b43f164b19bcd27e43bcc70a788852d0763d068f76486ba8d1fcd85fe
```

## 解析

实际执行了以下四次解析，分别覆盖三个包及香港地区请求。命令退出码均为 `0`，stderr 均为空。

```powershell
python core/yaya/scripts/packs.py resolve --language zh-Hant --data-dir .tmp/language-smoke/data
python core/yaya/scripts/packs.py resolve --language zh-HK --data-dir .tmp/language-smoke/data
python core/yaya/scripts/packs.py resolve --language ja --data-dir .tmp/language-smoke/data
python core/yaya/scripts/packs.py resolve --language ko --data-dir .tmp/language-smoke/data
```

| requested | status | available | resolved | source | version | quality |
| --- | --- | --- | --- | --- | --- | --- |
| zh-Hant | ready | true | zh-Hant | user | 0.1.0 | experimental |
| zh-HK | ready | true | zh-Hant | user | 0.1.0 | experimental |
| ja | ready | true | ja | user | 0.1.0 | experimental |
| ko | ready | true | ko | user | 0.1.0 | experimental |

`source: user` 是 resolver 在指定 `--data-dir` 时返回的来源标签；实际位置均在本次隔离目录中。

依据返回的 `guide` 字段，实际读取了：

- `D:\AIProjects\yaya\.tmp\language-smoke\data\language-packs\zh-Hant\GUIDE.md`
- `D:\AIProjects\yaya\.tmp\language-smoke\data\language-packs\ja\GUIDE.md`
- `D:\AIProjects\yaya\.tmp\language-smoke\data\language-packs\ko\GUIDE.md`

返回的 `examples` 字段分别指向上述目录内的 `examples.md`；本次请求无需追加示例，因此未读取。

## 阻碍与限制

- 未遇到阻止安装、解析或生成输出的错误。
- PowerShell 每次启动会打印 `Attempting to perform the InitializeDefaultDrives operation on the 'FileSystem' provider failed.`；读取、安装和解析仍成功完成，进程退出码为 `0`。
- 三个包均标记为 `experimental`。GUIDE 说明尚未经过母语编辑审核；繁体包还说明未完整验证香港、台湾地区用法。安装及解析成功仅记录资源可用性，不构成语言质量验证。
- 本记录不对生成文本的语言质量作自评。

## 文件

- `outputs.md`：三个请求的实际处理结果。
- `install-results.json`：实际安装命令、校验值、退出码和原始 stdout/stderr。
- `resolve-results.json`：实际解析命令、退出码和完整解析结果。
- `data/language-packs/`：隔离安装的三个可选语言包。
