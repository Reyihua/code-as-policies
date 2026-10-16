# 实测验证

2026-10-16，Windows / Python 3.9.13。

- `python -m unittest discover -s tests -v`：5 项通过。
- `python -m coap.evaluate --episodes 30 --seed 1000 --output results/numeric.json`：30/30 数值场景成功，15 个场景注入一次滑落。
- RGB 定位测试：3 个不同布局，每个物体位置误差小于 12 mm（仅在该简化渲染器内）。
- REA PDF 和 Python 目录检查均失败，原始工具错误随仓库保留。

这些测试不包含 RoboDojo、真实机械臂动力学、真实相机或论文全量任务。100% 仅指本次数值场景成功率。
