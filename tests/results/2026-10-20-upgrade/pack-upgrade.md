# 语言包 v2 与构建验证

本次将核心与仓库内 5 个语言包、1 个贡献模板升级到 `0.2.0`。核心声明 `pack_format: 2`、`core_major: 0`，同时接受 format 1 和 2 的语言包。5 个语言包继续标记为 `experimental`。

## 兼容行为

| 输入 | 结果 |
| --- | --- |
| v1 包，只有原有文件 | 安装、解析、替换、卸载和回滚可用；`patterns: null` |
| v2 包，有 `PATTERNS.md` | 解析返回该文件的绝对路径 |
| v2 包，无 `PATTERNS.md` | 普通指南仍可用；`patterns: null` |
| v1 包混入 `PATTERNS.md` | 拒绝；替换失败时已安装包保持完整 |
| 未支持的 format 3 | 明确报告 `incompatible`，不静默回退到低优先级包 |
| 额外文件、重名/大小写冲突、链接或特殊 ZIP 成员 | 拒绝；不遗留安装暂存目录 |

`PATTERNS.md` 使用原有 UTF-8、非空、非二进制、文件与总尺寸限制。它是可选的编辑指南，不会注册或执行检测器规则。v1 schema 保留；新增独立 v2 schema。

升级和回滚移动完整的包目录。因此从 v2 回滚到 v1 时不会留下新版本的 `PATTERNS.md`，再次回滚也能恢复完整 v2 内容。

## 发布物

构建明确包含 `detect_tells.py`、`check_rewrite.py`、`prose_scan.py` 和 `tell_rules.json`。新增 `humanize.md` 由已有 references 收集规则纳入，两份内置和三份可选语言包的 patterns 随各自包分发。核心依旧只内置中英。

构建在创建输出目录之前检查全部必需运行文件；缺少规则数据等文件时直接失败。测试还验证了解压后的运行文件在含空格的新位置执行检测和改写检查，且数字变化使改写检查失败。

测试内生成两份独立发布物，验证所有字节相同、catalog 与 SHA-256 对应、可选包为平铺 ZIP、测试与模板文件未进入核心包。测试覆盖一个新第三方 reviewed v2 包不含 patterns，以及与 v2 同批构建的第三方 v1 包。

## 已执行检查

环境：Windows，CPython 3.13.5。此报告只覆盖语言包和构建子任务。

| 命令/检查 | 结果 |
| --- | --- |
| `python -m unittest discover -s tests -p test_packs.py -v` | 47 个测试方法，0 失败/错误，4 个目录链接测试因主机能力跳过；8.776 秒 |
| `python -m unittest discover -s tests -p test_release.py -v` | 最终一轮 14 个测试方法，0 失败/错误；1 个方法内的 3 个文件链接子用例因主机权限跳过；8.428 秒 |
| JSON Schema 2020-12 校验 | 两份 schema 自身有效；5 个实际包和 1 个模板通过 v2 校验；其旧版格式样本通过保留的 v1 schema |
| Python 3.10 grammar 解析 | 两个修改后的实现脚本与两个测试文件通过；不是 Python 3.10 解释器实跑 |

与升级前相比，新增 7 个包兼容/生命周期测试和 3 个发布测试，并扩展原有发布内容检查。本次构建验证使用测试临时目录，不发布、不上传、不修改用户全局语言包。

Linux、Python 3.10/3.14 实跑和远端 CI 不在本次子任务的已验证范围。语言质量也不能由包格式或构建测试证明。
