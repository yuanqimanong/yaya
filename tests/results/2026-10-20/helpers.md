# Helper 测试记录

日期：2026-10-20。范围：`packs.py`、`check_comments.py`、`build_release.py` 与现有三个 `test_*.py`。

**结论：76 个测试方法执行完成，0 失败、0 错误。修复两类发布边界问题，新增 7 个回归方法。**

| 项目 | 实际结果 |
| --- | --- |
| 运行环境 | Windows；CPython 3.13.5；`D:\env\miniconda3\python.exe` |
| 基线 | 69 个方法；0 失败；0 错误；7 条 skip |
| 修复后全量 | 76 个方法；71 个方法完整通过；0 失败；0 错误 |
| skip 构成 | 4 个目录链接方法；1 个文件链接方法中的 3 个子用例 |
| 执行耗时 | 12.250 秒 |
| Python 3.10 | 三个脚本及三个测试文件的 3.10 grammar 检查通过；标准库 API 已静态检查；未运行 3.10 解释器 |
| Python 3.14 | 启动器只有失效注册项；对应可执行文件不存在，未实际运行 |

复现命令：

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

## 已复现并修复

1. **构建输出可进入 `core/` 源码父目录。** 原检查只阻止 `core/yaya/` 及其子目录。新增回归在隔离副本中复现构建成功且向 `core/` 写入发布资产。修复后整个 `core/` 子树都在输出前拒绝。
2. **核心版本元数据校验不严格。** `true`/`false` 与 `1`/`0`、`1.0`/`0.0` 的 Python 相等比较导致错误类型通过；重复 JSON key 被静默覆盖。缺少版本字段、`null` 版本、非对象 JSON 会产生未捕获的 `TypeError`/`KeyError`。新增回归先复现以上八种失败，再改为严格 JSON、必需字段、整数类型与 SemVer 校验。当前测试还覆盖非法 SemVer 和不兼容 major，均在创建输出目录前拒绝。

`packs.strict_json` 只新增可选文档名参数，供构建器输出正确的 `version.json` 错误信息；原有 `pack.json` 默认行为保持一致。

## 新增覆盖

- 独立发布者的 `reviewed` 标准包：新增 `sr-Latn-RS`，包含 `REVIEW.md`，使用 `9.8.7-rc.1+publisher.005`；可打包、按 SHA-256 安装，并由 `sr-Latn-RS-1994` 回退解析；无须改动 core。
- `es-419` 包在中文和空格路径下完成安装、幂等重装、替换、回滚、删除、恢复与清单查询。
- SemVer prerelease/build、数字前导零、空段、非 ASCII 数字等边界。
- 多行 Python 表达式允许普通注释改写，同时拒绝代码和缩进变化。
- 注释 doctest 输出仍受保护；空行之后的普通注释可改；不能把普通注释改成 doctest prompt。
- 发布包测试接受协议允许的可选 `REVIEW.md`，不再把所有包固定为四个文件。

## 未覆盖边界

- 当前 Windows 会话无法创建所需 symlink/junction。4 个真实目录链接测试及 3 个输出文件链接子用例跳过。已有模拟链接防护测试通过，但不等于真实链接集成测试通过。
- 未执行 Python 3.10、Python 3.14、Linux 或远端 CI；grammar/API 静态检查不等于运行时验证。
- 静态检查发现 Python 3.14 t-string 插值注释可能需要与 f-string 同等保护；缺少可运行的 3.14 解释器，本轮未验证或改动该分支。
- 并发恶意修改文件系统、进程被操作系统强制中断不在此确定性测试范围；已有重命名、恢复与清理失败注入测试。
- 包结构、元数据和安装通过不等于语言编辑质量通过。语言质量需独立评审。

## 回滚

可撤回 `build_release.py` 的两处检查变更，并将 `packs.strict_json` 恢复为固定 `pack.json` 文档名。新增测试和报告可独立保留。所有变更与生命周期验证都在临时数据目录中完成，没有改动真实用户语言包。

完整方法清单、skip 原因及机器可读结果见 [helpers.json](helpers.json)，原始测试输出见 [helpers.log](helpers.log)。
