# 临时目录清理后的证据归档

2026-10-20，在首次提交 GitHub 前，将报告引用但尚未归档的材料保存到这里，再清理
`.tmp/`、`tests/runs/`、编辑器配置与 Python 缓存。复制时逐文件校验大小和 SHA-256；
原路径、现路径及校验值见 [manifest.json](manifest.json)。原始文件内容未改。

| 目录 | 内容 |
| --- | --- |
| `pre-refinement/` | 最后两处指导修改前的核心 ZIP 与构建基线记录，仅用于历史核对 |
| `tool-audit/` | 正文工具审查的复现脚本、输出和小型输入 |
| `cli-failures/` | 三次早期运行的元数据、Skill 快照和全部已启动尝试，包括失败及未完成记录 |

已完成主对照、竞品对照、定向复测和下游运行的完整证据仍在各自的 `cli-evidence/`
目录。它们没有移到这里，也没有因清理而修改评分。

## 复现正文工具审查

原脚本检查自身位置，并把生成输入写入 `tests/runs/0.2-tools-audit/`。在仓库根目录
执行以下 Python 命令，再运行脚本：

```text
python -c "from pathlib import Path; import shutil; d=Path('tests/runs/0.2-tools-audit'); d.mkdir(parents=True, exist_ok=True); shutil.copyfile('tests/results/2026-10-20-upgrade/cleanup-archive/tool-audit/prose_audit_repro.py', d/'prose_audit_repro.py')"
python -B tests/runs/0.2-tools-audit/prose_audit_repro.py
```

八份大型性能输入没有重复归档；脚本包含其生成表达式，运行时会重新创建。历史耗时
保存在本目录的 JSON 中，新运行的耗时和结果可能不同。

## 核对旧版本

`pre-refinement/yaya-core-0.2.0.zip` 是历史评测版本，不能当作当前安装包。当前源码
生成的安装包位于 `dist/`。旧版两份指导也保存在
`../full/cli-evidence/snapshot/yaya/` 中。

早期报告中的 `.tmp/`、`tests/runs/` 和本机绝对路径描述的是当时运行位置；清理后可通过
本目录清单查找已迁移的材料。这些路径不属于安装前提。
