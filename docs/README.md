# 文档导航

[返回项目首页](../README.md) · [English / 技术说明](../README_EN.md)

不用按文件名挨个看。先选你现在要做的事。

## 认识和使用项目

| 文档 | 什么时候看 |
|---|---|
| [看懂这个仓库](看懂这个仓库.md) | 想知道界面上的按钮、数字和术语是什么意思 |
| [技术说明](../README_EN.md) | 安装、切换模型、运行命令 |
| [项目状态](../STATUS.md) | 查已完成和仍需人来做的事 |
| [系统设计](ARCHITECTURE.md) | 理解材料如何变成评分建议 |
| [隐私与使用边界](GOVERNANCE.md) | 了解材料处理、人工复核和模型局限 |

## 看结果：先读说明，再看数字

| 文档 | 是什么证据 |
|---|---|
| [当前开发实验解读](EVALUATION_dev_frozen_notes.md) | 先看这份：解释固定配置的 A / B2 / B3 对比 |
| [A：按相关性找证据](evaluation_dev_frozen/A.md) | 当前固定配置的开发集结果，真实本地模型 |
| [B3：提供全部证据](evaluation_dev_frozen/B3.md) | 对照实验；其余评分规则保持一致 |
| [实验协议](EVALUATION_PROTOCOL.md) | 指标怎么算、哪些比较成立 |
| [固定配置记录](FREEZE.md) | 模型、提示词、检索参数和文件校验值 |
| [干扰与顺序测试](robustness/RESULTS.md) | 诱导文本和段落顺序变化下的表现，含未达标项 |
| [安装与打包验证](validation/cleanroom_2026-10-07.md) | 2026-10-07 的软件检查记录，不代表评分准确率 |

`EVALUATION.md`、`EVALUATION_live_qwen7b.md` 和 10 月 4 日 smoke 文件是历史记录，不能混作当前配置的结果。Fixture 是测试替身；开发集不是独立最终测试；模型实验也不能代替真实用户计时。

## 写报告、分工和准备展示

| 文档 | 用途 |
|---|---|
| [最终报告草稿](FINAL_REPORT_DRAFT.md) | 报告工作稿，仍需补齐独立评价与贡献证据 |
| [小组分工](TEAM_DELIVERY.md) | 建议负责人、任务和交付物 |
| [实际贡献记录](CONTRIBUTIONS.md) | Git 历史支持的贡献记录 |
| [演示与问答准备](DEMO_SCRIPT.md) | 演示流程和需要讲清的问题 |
| [回应 proposal 反馈](MARKER_RESPONSE.md) | 评分意见对应哪些改进 |
| [相关工作](RELATED_WORK.md) | 与已有研究的重叠和差异 |
| [需求对应表](REQUIREMENTS_TRACEABILITY.md) | 每项需求对应的实现、测试和证据 |

## 参与人工评价

- [独立标注说明](../dataset/final_test/annotation/REGISTER.md)：两人分别完成标注后，再计算一致性与处理分歧。
- [使用者测试流程](MARKER_SESSIONS.md)：包含人工对照、计时和问卷。
- [贡献指南](../CONTRIBUTING.md)：分支、检查和 PR 审阅约定。
- [AI 使用声明](../AI_USE.md)：记录 AI 做过哪些工作，供提交前核对。
