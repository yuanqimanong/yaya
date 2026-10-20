# 最终确定性验收

日期：2026-10-20。当前源代码在验收期间的 SHA-256 保持一致。

**结论：所有实际执行的检查通过；存在明确列出的环境跳过。**

| 检查 | 结果 |
| --- | --- |
| 全量 unittest | 83 个方法；77 个完整通过；0 失败；0 错误 |
| skip | 5 个完整方法；1 个方法部分跳过（3 个子用例）；共 8 条 |
| unittest 耗时 | 22.394 秒 |
| Skill quick_validate | 通过；使用 .tmp/validation-deps 提供 YAML 依赖 |
| JSON Schema | Draft 2020-12；5 个实际包 + 1 个模板，全部通过 |
| Python 3.10 grammar | 11 个文件通过；包含新 prepare/collect/summarize 和 test_evals.py |
| 发布构建 | dist/ 生成 core + ja/ko/zh-Hant 三个独立可选包 |
| 发布内容 | core 仅内置 en、zh-Hans；无 tests/evals 等开发资源；可选包为平面文件布局 |
| 发布完整性 | ZIP CRC、catalog 与 SHA256SUMS 的 SHA-256 和尺寸全部吻合 |

## 产物

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| yaya-core-0.1.0.zip | 27712 | 2a0c7b070af52abaf0bc1d483b354a8378fc1cd46a8458dc6cc8c2f778deb582 |
| yaya-lang-ja-0.1.0.zip | 4228 | fa8d7f67beda4fc72da1e94ca400d859a3607d9334b22ca403c9db1544e68a52 |
| yaya-lang-ko-0.1.0.zip | 4056 | b659d61b43f164b19bcd27e43bcc70a788852d0763d068f76486ba8d1fcd85fe |
| yaya-lang-zh-Hant-0.1.0.zip | 4074 | 1213a10c16b12781770047e82b2f1d4f6d86fc50078dbfbd795c5ed0047e3588 |

## 环境和限制

- 实际执行环境为 Windows / CPython 3.13.5。未执行 Python 3.10、Python 3.14、Linux 或远端 CI。3.14 的本机注册项指向不存在的解释器。
- 完整跳过：Python 3.14 t-string 用例 1 项；真实目录 symlink/junction 用例 4 项。部分跳过：输出文件 symlink 的 3 个子用例。不能将这些计为通过。
- t-string 保护已纳入源代码，版本条件回归已存在；真实 3.14 tokenizer 路径仍待支持该版本的环境验证。
- quick_validate 仅检查基础 frontmatter 和未完成占位符；Schema 不验证语言登记、许可证真实性、人工 review 真实性或写作质量。
- 新 eval 完整性单测使用合成结果验证收集和汇总约束，不是模型生成质量评测。
- 未测试恶意并发文件系统改写、强制终止进程和其他语言注释解析器；现有确定性文件操作故障注入仍在本次测试内。
- 仅构建本地发布产物，没有上传或发布。

机器可读结果及完整方法/skip 清单：[final-checks.json](final-checks.json)。原始输出：[final-checks.log](final-checks.log)。
