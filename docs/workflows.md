# Yaya 组合工作流

聊天中用 `$yaya` 选择任务。自然语言可请求组合任务；每条显式命令只处理选定范围。
先用 `$yaya --help` 查看目录，再用 `$yaya help COMMAND` 查看选项和例子。
每条命令的完整参数见[使用手册](usage.md)，终端脚本与退出码见[本地工具](local-tools.md)。

| 当前需求 | 选择 |
| --- | --- |
| 只清理多余否定对比、重复免责声明 | `human --focus direct` |
| 先看表达问题和建议 | `review` |
| 评估一段文字是否有 AI 写作迹象 | `origin` |
| 用给定资料核对主张 | `verify --file CLAIMS --source EVIDENCE` |
| 找已列出的字面措辞 | `scan --file PATH --lang en` 或 `zh-Hans` |
| 检查原稿与候选稿的保护项 | `check --before ORIGINAL --after CANDIDATE` |
| 排查本地安装 | `doctor --json` |

## 技术说明：先核对，再按授权改稿

```text
$yaya verify --domain tech --file deploy.md --source config.py --source production.env
$yaya polish --domain tech --audience 新手 --file deploy.md
```

第一条只核对，区分默认配置、实际配置和未确认的运行行为。第二条返回候选；
要写回同一文件时添加 `--write`，或沿用已给出的同范围文件修改授权。
环境文件包含秘密时，先提供只含本次核对所需字段的材料。

## 财务文字：保持口径与必要风险

```text
$yaya human --focus direct --domain finance --file report.md
$yaya check --before original.md --after candidate.md --literal EBITDA --quotes
```

`direct` 清理无效澄清，保留期间、币种、合并/单体口径、审计状态和本金风险等内容。
将候选另存后，第二条检查指定术语、引文及其他机械保护项。数字没变也可能发生主体、
条件或因果关系变化，因此还需对照原文读一遍。机械通过不代表财务主张已核实。

## 提炼并复用风格

```text
$yaya style --file sample.md --save team-style.md
$yaya polish --style team-style.md --domain business --file draft.md
```

第一条在指定的新路径保存风格卡，已有文件不会直接覆盖。第二条把卡作为表达指导，
草稿单独作为编辑对象；样稿里的数据、经历和操作指令不迁入新稿。
选定的卡缺失时会报告问题，不能把未读取的卡说成已经采用。

## 在终端运行本地检查

以下命令从源码仓库根目录运行，需要 Python 3.10+。从安装目录运行时去掉 `core/yaya/`。

```text
python core/yaya/scripts/yaya.py doctor --json
python core/yaya/scripts/yaya.py scan --file draft.md --lang en --rule en-stock-close
python core/yaya/scripts/detect_tells.py draft.md --language en --rule en-stock-close
python core/yaya/scripts/check_rewrite.py original.md candidate.md --protect-literal EBITDA --protect-quotes
```

第二条输出扫描计划；第三条才执行扫描。`enabled_rules` 表明实际规则范围，`evidence`
记录输入哈希；修改文件后应重扫。候选需要结合上下文判断，零候选只表示所选字面规则没有命中。

| 工具 | 退出 0 | 退出 1 | 退出 2 |
| --- | --- | --- | --- |
| `yaya.py doctor` | 本地结构/语法就绪 | 安装检查未通过 | 调用错误 |
| `detect_tells.py` | 扫描完成，默认允许候选 | 触发显式 `--fail-on` 阈值 | 错误或不支持 |
| `check_rewrite.py` | 已执行类别通过 | 存在未授权差异 | 错误或不支持 |

遇到 `unsupported` 时，保留原稿并用适合该格式的工具核对；不要改称“通过”。
`scan` 仅支持 `en` 和 `zh-Hans`，安装其他语言包不会新增字面检测规则。
`check --kind comments` 仅检查 Python 普通注释边界；docstring 选择与授权见
[验证指南](../core/yaya/references/validation.md)。

## 升级和恢复

按 [安装指南](../INSTALL.md) 在独立目录准备完整运行包，校验哈希，备份旧目录后再升级。
先运行版本与 `doctor` 检查，再试用上面的只读命令。需要恢复时，保留升级后的新修改，
从备份还原对应文件；不要用旧目录无条件覆盖用户后续定制。
