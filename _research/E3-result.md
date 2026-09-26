# E3：跨来源公开题诊断结果

日期：2026-09-26。事前方案见 `_research/E3-plan.md`；运行清单见 `runs/E3/20260926T090500/run-manifest.json`。本轮冻结原版 Laya 与 E2 第二轮权重，没有训练、提示选择或阈值调整。BoolQ 与 ARC-Challenge 的固定修订、抽样种子和文件哈希见 `data/crosssource-e3/manifest.json`。

## 主要结果

| 来源 | 题数 | 原版 Laya | E2 | 配对增益与逐题 bootstrap 95% 区间 | 简单多数标签基线 |
|---|---:|---:|---:|---:|---:|
| BoolQ validation 固定抽样 | 400 | 303/400，75.75% | 317/400，79.25% | +3.50 pp，+1.00 至 +6.00 pp | 全选 yes：63.75% |
| ARC-Challenge validation 全部 | 299 | 81/299，27.09% | 87/299，29.10% | +2.01 pp，−1.67 至 +5.69 pp | 全选 D：27.42% |
| 两来源等权平均 | 699 | 51.42% | 54.17% | +2.75 pp，分层逐题 bootstrap +0.58 至 +4.97 pp | 不适用 |

两组模型各 699/699 题有效，零推理错误。BoolQ 各有 2 道原文 passage 被 512-token 上限截断；ARC 无截断。BoolQ 的 14 道净增题全部来自原标签为 no 的题：yes 题两组都答对 236 道，no 题由 67 道增至 81 道。因此一个直接解释是 E2 减少了原版偏向 yes 的倾向，而不是已证明复杂证据推理全面提升。ARC 净增 6 道、18 道错转对、12 道对转错；绝对准确率仅略高于全选 D 的简单基线。逐题预测、截断标记和对照结果见 `results/crosssource-e3/`。

## 判断与限制

E2 在两种不同来源的公开题上方向一致，等权配对区间排除零，提供了比同生成器 E2 test 更有价值的**探索性跨来源改善信号**。该判断仍须收窄：ARC 单来源区间跨零、成绩接近常数标签基线；BoolQ 收益集中于 no 标签；两种任务分别是自然问答和科学选择题，并非 JevBench 的真实决策分布。逐题 bootstrap 未处理可能的共同来源聚类，也未修正多个已观察公开基准带来的选择效应。两个公开验证集可能出现在 Laya 预训练中，不能视为 sealed 新题。

因此 E3 不改变“目前尚无可信榜单领先证据”的结论，也不应拿本轮题目继续选择新模型。下一步应优先获得正式榜单的隐藏评测或建立真正未见过、许可清楚、与榜单任务形态接近的独立人工题集；先固定规则与样本，再评测单一候选。

## 2026-09-26 榜单版本核对

JevBench 官方仓库当前显示 v1.4.2。其正式分数包括旧版 534 题及新的 308 道 sealed 题，综合 Intelligence、Calibration、Speed、Cost 四轴；本项目先前的 231 道公开题准确率**不是**当前正式榜单分数。官方对原版 Laya 的 v1.4 通知称其 sealed 准确率 30.8%、公开切片 58.4%，触发超过 25 个百分点的 gap 调整。这个现象支持继续把 E2/E3 视为公开诊断，而不能从 E2 的 59.74% 推断 sealed 或正式名次。参见 [v1.4 方法](https://github.com/fstandhartinger/jevbench/blob/main/docs/METHOD-v1.4.md)、[v1.4.2 发布说明](https://github.com/fstandhartinger/jevbench/blob/main/docs/RELEASE-v1.4.2.md)及[对 Laya 的结果通知](https://github.com/NandhaKishorM/laya/issues/252)。
