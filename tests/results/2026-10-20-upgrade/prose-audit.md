# prose 工具独立正确性审查

结论：确认并反馈了 4 类初版缺陷，以及修复过程中出现的 1 类性能回归。工具修复代理已处理，最终独立 CLI 复验全部符合预期。审查代理未修改产品源码或原有测试。

- 范围：`prose_scan.py`、`check_rewrite.py`、`detect_tells.py`、`tell_rules.json`、对应两个测试模块。
- 未读取任何生成评测 outputs，未参与评分。
- 不将声明过的语义、数字归属、未列出单位、文档结构比较局限列作缺陷；不要求完整 CommonMark。
- 初版 `prose_scan.py` SHA-256：`d142d9f3fdb4ae5bf34c12be8a24adc70ff488e1e79102101c89a42986746faa`。
- 最终复验 `prose_scan.py` SHA-256：`273b5d879a909721f8bf6f914a3e9303dbf0b3f54b67567d00651e9ec74ea596`。
- 机器可读最终证据：`tests/runs/0.2-tools-audit/prose-audit-evidence.json`，包含 argv、输入字节数、退出码、JSON、stderr、耗时及四份源码哈希。

从仓库根目录复现全部检查：

```powershell
python -B tests/runs/0.2-tools-audit/prose_audit_repro.py
```

脚本仅向 `tests/runs/0.2-tools-audit` 内写入经过路径校验的复现输入和证据。

## 1. P1：重叠 span 导致外层保护静默丢失

初版 `add()` 遇到 occupied 区域返回 False；HTML comment、collapsed reference 和 shortcut reference 的调用方忽略返回值。结果是内层 inline code、fence 或 table 已保护，外层本应保留的内容却消失于检查项。

实际观察：

```text
BEFORE: <!-- note\n```\ncode\n```\n-->\n
AFTER:  <!-- EDIT\n```\ncode\n```\n-->\n
compare: {"status":"passed","changes":[]}

BEFORE: [A `x`][]\n\n[A `x`]: url\n
AFTER:  [B `x`][]\n\n[A `x`]: url\n
compare: {"status":"passed","changes":[]}
```

前者允许篡改受保护的 HTML 注释。后者改变 collapsed reference 的引用标签，原引用不再解析，却仍通过。`[A \`x\`]` shortcut reference 也有同类问题。注释内部表格之后出现 `Only time will tell.` 时，detector 还会对注释正文产生候选。

最终 CLI 复验：

```powershell
python -B core/yaya/scripts/check_rewrite.py tests/runs/0.2-tools-audit/html_comment_fence.before.md tests/runs/0.2-tools-audit/html_comment_fence.after.md
python -B core/yaya/scripts/check_rewrite.py tests/runs/0.2-tools-audit/collapsed_reference_code.before.md tests/runs/0.2-tools-audit/collapsed_reference_code.after.md
```

两项均退出 1、`status=failed`，分别报告 `html`、`link_targets`。table/comment 和 shortcut/code 变体也均 failed；注释检测为 `status=ok, findings=[]`。额外验证了 comment 位于单行/跨行 inline code 时仍由 `inline_code` 正确保留。

## 2. P2：单列表格完全落入可编辑正文

初版 `_table_separator()` 要求去除两端管线后存在至少两个 cell，因此合法的单列表格未进入 `tables`。

```text
BEFORE: | Name |\n| --- |\n| Alice |\n
AFTER:  | Name |\n| --- |\n| Bob |\n
初版:   {"status":"passed","changes":[]}
```

这与工具的表格整体保护承诺不符，普通名单、术语列表即可触发。

```powershell
python -B core/yaya/scripts/check_rewrite.py tests/runs/0.2-tools-audit/single_column_table.before.md tests/runs/0.2-tools-audit/single_column_table.after.md
```

最终退出 1、`status=failed`、违规分类 `tables`。

## 3. P2：URL 内的撇号被误判为链接标题开头

初版 inline link 扫描器把任意 `'` / `"` 当作标题引号，未区分 URL 内字符和空白之后的 title。正常 Wikipedia 链接原样比较就失败：

```text
[O'Brien](https://en.wikipedia.org/wiki/Tim_O'Brien)
初版: {"status":"unsupported","error":"Unclosed inline link."}
```

```powershell
python -B core/yaya/scripts/check_rewrite.py tests/runs/0.2-tools-audit/apostrophe_url.before.md tests/runs/0.2-tools-audit/apostrophe_url.after.md
```

最终退出 0、`status=passed`。另验证了真实 title 从 `'stable'` 改为 `'changed'` 仍被 `link_targets` 拒绝。

## 4. P2：正常硬换行引文和英寸符号令整篇检测 unsupported

初版 detector 无条件使用严格 quote protection。配对引文跨普通换行就报错；`6"` 的英寸符号也被当作未闭合引号。两者都会使后续普通正文失去检测结果。

实际输入：

```text
“Quoted text\ncontinued quote.”\nOnly time will tell.
He is 6" tall. Only time will tell.
```

初版结果均为 `unsupported`，错误为 `Unclosed or multiline quoted span under quote protection.`。这属于常见正文输入，与声明的 Markdown 不支持项无关。

```powershell
python -B core/yaya/scripts/detect_tells.py tests/runs/0.2-tools-audit/hard_wrapped_quote.before.md --language en
python -B core/yaya/scripts/detect_tells.py tests/runs/0.2-tools-audit/inch_mark.before.md --language en
```

最终两项均退出 0、`status=ok`，且各保留后续 `Only time will tell` 的 1 条候选。checker 显式 quote protection 仍采用严格模式。

## 5. P2：引号容错修复曾引入 O(n²)，已消除

这是修复中的回归，不存在于最初遇到首个未闭合引号便退出的实现。容错扫描曾对每个未配对 `“` 重新扫描剩余全文，输入远小于 2 MiB 也会显著阻塞。

实际 subprocess 计时，均设置 5 秒超时：

| 输入 | 字节数 | 修复中实现结果 |
| --- | ---: | --- |
| 1,000 个 `“` | 3,000 | 0.218 秒 |
| 2,000 个 `“` | 6,000 | 0.483 秒 |
| 4,000 个 `“` | 12,000 | 1.546 秒 |
| 12,000 个 `“` | 36,000 | 超过 5 秒，被测试脚本终止 |

原计时证据保存在 `tests/runs/0.2-tools-audit/quote-performance-evidence.json`。

```powershell
python -B core/yaya/scripts/detect_tells.py tests/runs/0.2-tools-audit/unmatched-quotes-12000.md --language en
```

最终相同规模输入为 `status=ok`，0.151 秒完成；最终证据中的用例名为 `perf_unmatched_quotes`。

## 数字、CLI 与性能边界复验

数字词边界观察：

- `2 seconds`、`2 minutes`、`2ms`、`30万元` 按完整已识别单位取词。
- `2 secondhand customers` 仅取数字 `2`，不会吞入 `s` / `second` 单位前缀。
- `256MiB`、`2MS` 不在已列举单位集合内；不将其作为此次缺陷，证据明确保留实际结果。
- 未要求验证数字与实体配对、否定含义或事实正确性。

以下 CLI 错误都输出有效 JSON、`status=error`、退出 2，stderr 为空：非法 UTF-8、NUL、孤立 CR、超过 2 MiB、非法 `--fail-on`、双方同时 stdin、缺少位置参数、输入文件不存在。

最终接近上限的只读 CLI 耗时：

| 用例 | 输入字节数 | 状态 | 秒 |
| --- | ---: | --- | ---: |
| 普通正文 | 1,860,000 | passed | 3.870 |
| 大量 inline code | 1,955,000 | passed | 4.718 |
| 长数字及尾随字母 | 2,000,001 | passed | 4.163 |
| 错误引用定义及大量空格 | 2,000,006 | unsupported | 0.920 |

前 3 项是 BEFORE/AFTER 双份输入的比较总耗时。此次选定边界输入未再发现超线性阻塞或结构化错误遗漏。
