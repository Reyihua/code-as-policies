# code-as-policies

对本地论文 **Embodied Turing Machines: Stateful Code for Robot Recursive Self-Improvement**（COAP，arXiv:2610.12369v1，PDF 日期 2026-10-08）的独立算法原型。

**当前交付是可运行的核心机制复现，不是作者代码，也不是 RoboDojo 42 任务 / 70.24% 成绩复现。** 数值场景使用简化的三轴笛卡尔机械臂和理想接触规则，不能代表真实机器人成功率。没有训练模型，没有在线 LLM/VLM/VLA 调用。

## 运行

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python -m coap.evaluate --episodes 30 --seed 1000 --output results/numeric.json
```

Python >=3.9；本次验证环境 Python 3.9.13、NumPy 2.0.2、OpenCV 4.13.0、Windows。

## 论文与代码对应

| 论文 | 实现 | 验证范围 |
|---|---|---|
| §3.1 / 式1 显式环境、机器人、任务状态 | `coap/state.py`, `policy.py` | 位姿、误差代理、来源、时间、任务阶段和重试持久化 |
| §3.2 / 式2 RGB 几何感知 | `coap/perception.py` | 背景差分、已知颜色、连通域、标定射线平面交点、已知立方体位置/yaw 的粗细搜索与 IoU 拟合 |
| §3.2 遮挡记忆 | `WorldState.update` | 不可见对象保留最后测量；陈旧测量不会启动新抓取 |
| §3.3 分层共享库 | `motion.py`, `policy.py` | 两个对象共用抓取、提起、搬运、释放、复测流程 |
| §3.3 / 式3 兼容条件 | `coap/rsi.py` | 非目标任务轨迹保持一致 |
| §3.4 / 式5 离线筛选 | `coap/rsi.py` | 相同验证布局、正改进阈值、CPU 门槛、无回归、禁止 test 选择 |

环境内部坐标仅供渲染、理想接触与独立评分。策略只读取 RGB、固定相机/物体常量、机器人本体感知和给定目标，不读取 `scene.positions`。末端位置由简化运动学执行，物体位置从图片测量。抓持检测使用实际手指间距；这比论文列出的 gripper command echo 多一个观测，正式接入时需要用视觉验证替换。

`ObjectState.error` 是 IoU 推导的启发式值，不是经过标定的统计误差界。当前每种颜色只支持一个物体，yaw 搜索仅覆盖方形物体的对称区间。`robot_mask` 是可选接口，本原型未实现从真实机器人网格和关节角生成遮挡 mask。

## REA 使用

使用用户指定的 [morluto/rea](https://github.com/morluto/rea)，将源码克隆到被忽略的 `.tools/rea`，局部安装 `rea-agents@6.5.0`，实际执行 `inspect-artifact`。**REA 拒绝 PDF：`unsupported_target / unsupported binary format`**；对 Python 目录的尝试也未成功。原始错误保留于 `results/rea-paper-inspection.json` 和 `results/rea-code-inspection.json`。具体版本、命令及边界见 [docs/REA.md](docs/REA.md)。

REA 是软件/二进制逆向工具，工件检查不等于解析或复现论文算法；本次算法依据 PyMuPDF 提取的本地论文 §3.1–3.4 手动实现。未配置反编译器，未调用 REA 生成机器人策略。

## 尚未完成的官方复现

1. 获取可访问的官方 RoboDojo 源码、版本、资源与评测客户端，确认真实 observation/action schema。
2. 实现真实双臂 IK、网格碰撞检查、机械臂投影 mask、三相机标定和腕部精测。
3. 为 42 个任务实现物体几何、任务程序、记忆/语言/长时序操作。
4. 接入离线编码代理和 Git worktree 候选生成；目前只实现候选接受门槛，没有自动 RSI 搜索。
5. 按论文验证/测试划分和每任务 3 seeds × 50 layouts 运行官方判分，报告独立实测结果。

本仓库没有把论文报告的 70.24% 当作本项目成绩；`results/numeric.json` 仅记录数值场景结果。失败恢复覆盖一次抓持滑落；不包含真实接触动力学、倾倒、堆叠、杯下记忆或跨任务泛化实验。
