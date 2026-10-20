# 测试与评测

yaya 的脚本测试、编辑评测、参考项目调研和运行证据均存放于此。

| 位置 | 内容 |
| --- | --- |
| `test_*.py` | 包安装、解析、回滚、注释与正文保护、候选检测、评测协议和发布构建的确定性测试 |
| `evals/` | 编辑请求、原文、评审条件，以及准备和收集结果的脚本 |
| `research/` | 参考项目的评测方法与源码证据 |
| `results/` | 已完成运行的原始输出、问题记录和报告 |
| `runs/` | 隔离的运行目录、Skill 快照和临时文件，Git 忽略 |

在项目根目录运行脚本测试：

```text
python -m unittest discover -s tests -v
```

脚本测试不调用模型。编辑评测需要实际模型执行，步骤见 [evals/README.md](evals/README.md)；
表达质量、事实保真和任务完成分别评审。

0.1 记录：[2026-10-20 全量测试与迭代](results/2026-10-20/README.md)。
包含脚本回归、34 组有无 Skill 对照、文件操作和提示词执行测试；限制和跳过项单独列出。

0.2 结果见 [升级验收](results/2026-10-20-upgrade/README.md)，专项记录包括：

- [正文工具及性能](results/2026-10-20-upgrade/prose-tools.md)
- [独立工具审查](results/2026-10-20-upgrade/prose-audit.md)
- [单一语言包规范](results/2026-10-20-upgrade/pack-single-format.md)
- [真实文件操作](results/2026-10-20-upgrade/file-integration.md)
- [CLI 执行问题与保留的失败](results/2026-10-20-upgrade/cli-shutdown.md)

默认主矩阵为 112 条，另有定向控制例和下游执行用例。
各报告保留实际运行、失败与复测结果。整理后可删除已归档的临时运行目录；
复现时重新准备运行，不依赖原机器的 `runs/` 内容。

参考方法：[同类项目的评测实现](research/reference-evaluations.md)。
历史记录：[2026-10-19 初次验收](results/2026-10-19/validation.md)。
