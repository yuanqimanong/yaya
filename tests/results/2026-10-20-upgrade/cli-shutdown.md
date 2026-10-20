# CLI 结束阶段超时记录

2026-10-20，Windows / CPython 3.13.5。以下为旧运行停止后的只读核查，原有输出和完成状态均未修改。计数以 `started.json` 与 `completion.json` 为准；文件中出现答案不等于运行验收成功。

| 运行 | 已开始 | 已完成 | timeout | 无 completion | 其他失败 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `2026-10-20-v02-current` | 16 | 0 | 8 | 8 | 0 |
| `2026-10-20-v02-competitor` | 4 | 0 | 0 | 4 | 0 |

两次运行均没有发布 `outputs.json`。current 的 8 条 timeout 记录都包含 `turn.completed`；另外 8 条无 completion 记录中，6 条已有 `final.json`。competitor 的 4 条无 completion 记录均已有 `final.json`，但仍属于未完成。

此前的 `2026-10-20-v02-full` 另有 2 条已开始、0 条已完成、0 条 timeout、0 条无 completion、2 条其他失败。那两次 CLI 返回码为 0，但被当时的事件检查拒绝，不能计为本次管道超时。

逐条路径、完成记录哈希和计数时间见 [cli-shutdown-counts.json](cli-shutdown-counts.json)。

## 可以确认

- current 的 `baseline/batch-001/cli-attempt-01` 有完整 `agent_message`、一个 `turn.completed` 和 `final.json`。其记录为 `timeout_seconds: 180`、实际耗时约 **313.3 秒**、`returncode: null`、`status: failed`。
- 该运行器使用 `subprocess.run(..., capture_output=True, timeout=...)`，把 stdout/stderr 接到 PIPE。
- 本机 Python 的 `subprocess.run` 在 Windows 超时后先 `process.kill()`，再调用**不带 timeout 的 `process.communicate()`**收集 PIPE 输出。后代进程若仍持有写端，输出读取线程就可能继续等待。因此配置的 timeout 不保证整个 `subprocess.run` 在该时限内返回。
- stderr 存在 `js-reverse` MCP 启动握手失败和关闭阶段初始化失败日志。只读取配置中的 server 名称，确认名称为 `js-reverse`、`node_repl`；未输出其他配置内容。

## 仍不能确认

没有在现场记录 PIPE 句柄归属、CLI 主进程退出时点或后代进程树。因此，“某个 MCP 子进程继承 PIPE 并保持打开”是与证据一致的解释，尚不能指定具体进程为根因；也不能仅凭 `turn.completed` 推定 CLI 已以 0 退出。

## 修复方向与证据处理

将 stdout/stderr 直接写入每次 attempt 的真实文件，退出或超时后读取原始日志并沿用现有事件、返回码、schema 校验，可消除等待 stdout/stderr PIPE EOF 的这类阻塞。不要先捕获再覆盖原始日志；超时仍记失败，缺 completion 仍记未完成。

本轮先只改变日志收集方式，避免同时改变多个因素；不禁用 MCP，也不修改认证、配置目录、规则、hooks、sandbox 或模型。修复后的独立新运行应重新检验正常完成与超时边界，保留本记录中的失败及未完成材料。
