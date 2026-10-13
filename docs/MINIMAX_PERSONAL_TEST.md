# MiniMax：个人试用入口

这是 2026-10-13 新增的可选网页功能。
默认仍为 fixture；原 Qwen 接口、CLI、提示词、检索、validator、评分与导出规则均未修改。

## 启动与使用

在项目根目录执行（Windows PowerShell）：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

1. Example 选择 `s1_standard (S1 baseline)` 或 `s2_dispersed (S2 evidence spread out)`。
2. Gateway 选择 `MiniMax API (hosted)`。
3. 填入完整订阅 Key（截图中的省略形式不能使用），不要把 Key 发到聊天或提交到 Git。
4. 默认 base URL 为 `https://api.minimax.io/v1`。中国区账号可按其官方控制台说明改为
   `https://api.minimaxi.com/v1`；不会自动切换地区或替换 Key。
5. 默认模型 `MiniMax-M3.1-Flash-Preview`，可改为账号实际开放的模型名。
6. 点击 Run review，核对显示的 Model，并检查每项结果和证据，再人工确认、改分或拒绝。

密码输入只存在当前 Streamlit 会话内存中。API 请求仅发送到上述官方 HTTPS 地址；
评分依据会发往 MiniMax。密钥不会写入日志、导出文件或配置文件。
会话保留的模型对象使 B2 对照使用该次评分相同的模型配置。
日志启用时写入 `data/minimax_runs.jsonl`，不混入原 `data/runs.jsonl`。
原 Run log 页面仍读取原日志；个人 MiniMax 日志没有新增回放入口。

## 个人试用配置

- 当前 `assessment_v4` 提示词、BM25、K 滑块与原校验规则；网页 MiniMax 调用串行（workers=1）。
- Chat Completions、Bearer 认证、`max_completion_tokens=8192`、`reasoning_split=true`。
- 默认模型发送 `reasoning_effort=low`；其他模型不发送该字段。
- 不发送 temperature 或 response_format；由原提示词要求 JSON，再经原 parser 和 validator 检查。
- 只去除位于答案开头的完整 `<think>…</think>`，保留严格 JSON 校验。
- HTTP/服务错误、空答案、输出截断均不给分，不会自动改用 fixture。
- 原接口的 JSON 修复与 validator 纠正预算仍适用；失败结果需人工核对，不能直接接受。

401/403 时检查地区、Key 类型与权限；模型不可用时检查控制台模型名；429 时检查额度/限流。
达到输出上限时该结果会拒绝，不把不完整 JSON 当作有效评分。

## 证据边界

MiniMax 属于个人试用的新配置，
新增适配器并修改网页意味着当前源码不是历史 freeze 的逐文件副本；原 manifest 不更新。
正式任务 3 的模型方案需与负责人统一，测试全程保持一致。
本次自动验证使用 stub transport，没有真实 Key，未进行 MiniMax live smoke、用户研究或评分质量评价。

验证记录：82 项接入和原 UI/评分/校验相关测试通过，Ruff 通过。
完整回归使用 Python UTF-8 模式，145 项中 144 项通过；原
`test_manifest_covers_the_label_file_and_the_documents_it_names` 在 Windows 上因反斜杠路径与正斜杠断言不一致失败，未改动该测试或 campaign 实现。
不使用 UTF-8 模式时，另一个原评价测试用系统 GBK 读取 UTF-8 文件失败。
Freeze 脚本不能通过：原 manifest 的 40 个记录文件在本地是 CRLF；归一化为 LF 后 40/40 哈希匹配，说明本次没有修改这些原核心和实验输入文件。未重新生成 manifest 或覆盖历史结果。

官方依据（2026-10-13 查阅）：
- https://platform.minimax.io/docs/m-plan/other-tools
- https://platform.minimax.io/docs/api-reference/text-openai-api
- https://platform.minimax.io/docs/m-plan/faq
