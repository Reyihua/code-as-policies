# REA 实际使用记录

- 来源：https://github.com/morluto/rea
- 检查的源码提交：`180ba03bfddd5916251e81e97a500b1ede7a9eea`
- npm 包：`rea-agents@6.5.0`，局部安装于 `.tools/rea-cli`，不更改全局 agent/MCP 配置。
- 环境：Node.js v24.14.0，npm 11.9.0。

```powershell
git clone --depth 1 https://github.com/morluto/rea.git .tools/rea
npm install --prefix .tools/rea-cli rea-agents@6.5.0 --no-audit --no-fund
.tools/rea-cli/node_modules/.bin/rea.cmd inspect-artifact --help
.tools/rea-cli/node_modules/.bin/rea.cmd inspect-artifact 'E:/VLA文献阅读/一些有趣的论文/COAP.pdf' --format json |
    Out-File -Encoding utf8 results/rea-paper-inspection.json
```

实际结果：PDF 检查退出码 1，`target_unavailable` / `unsupported_target` / `unsupported binary format`。对 Python 包目录的补充检查也退出码 1，错误见 `results/rea-code-inspection.json`。因此本次没有通过 REA 成功解析算法，也不能称为 REA 驱动的复现。PDF 内容另以 PyMuPDF 读取，全文提取文件与原始 PDF 不上传。

本次也尝试访问 `https://github.com/XPolicyLab/RoboDojo.git`，Git 返回 Repository not found。这仅证明该猜测地址不可访问，不证明官方基准不存在。未猜测其 API 或伪造一个声称兼容的客户端。
