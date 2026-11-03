# 测试

这里是本地脚本和发布构建的单元测试，不调用模型。从仓库根目录运行：

```text
python -m unittest discover -s tests -v
```

| 文件 | 覆盖内容 |
| --- | --- |
| `test_commands.py` | 命令解析、帮助、任务计划、目录（catalog）校验 |
| `test_check_rewrite.py` | 改稿前后的机械保护检查与显式授权 |
| `test_prose_scan.py` | 链接、公式、占位符、日期时间与数量的保护范围 |
| `test_detect_tells.py` | 本地措辞扫描、排除区域与规则文件校验 |
| `test_comments.py`、`test_docstrings.py` | Python 普通注释与 docstring 的修改边界 |
| `test_edit_evidence.py` | 批量编辑证据的快照与核对 |
| `test_packs.py` | 语言标签、包的解析、安装、替换、删除与回滚 |
| `test_doctor.py` | 安装诊断 |
| `test_release.py` | 发布包内容、校验和、可重复构建与迁移后的运行 |

文件操作都在临时目录中完成，测试结束后自动删除。每个命令行入口只保留一次子进程调用，其余输入变化在进程内检查。

测试通过只说明脚本行为符合预期。改稿是否忠实、自然，仍需人工阅读判断。
