# Laya 开源决策模型冲榜实验

目标：在可复现、可公开的条件下，提高 Laya 决策能力，并比较纯 Laya 与 Laya 加开源推理模型的系统方案。DGX Spark 是计算现场；本目录保存研究状态、实验约定和紧凑证据。

## 已确认的基线（2026-09-25）

- DGX 项目：`/home/maolinqi/mlq/laya-jevbench-baseline`；Laya 代码：`/home/maolinqi/mlq/laya`。沿用后者 `.venv`，不安装全局依赖。
- JevBench 公开 231 题，英文 Laya：`max_len=512, head_max_len=192` 为 134/231，58.01%；改为 `head_max_len=384` 仍为 134/231，231 题的预测选项完全相同。H384 有一题概率值变化，零失败。
- 原版英文 Laya 延长 context 至 1024/2048/4096 后分别为 54.55%/55.41%/55.84%；typed-decisions 权重的 1024/256 配置为 53.68%。这些是公开题本地诊断，不是官方排名。
- 独立 Banking77 实验中，77 选项、3080 条测试样本，head budget 192→384 使准确率 44.68%→54.74%。这个效果没有在 JevBench 公开题上复现。
- DGX 还已有 **Banking77 专项微调**：保留 Laya ModernBERT 编码器、换用 77 类分类头；三模型 ensemble 在公开测试集记录 94.35% 准确率。它不是 Laya 原生 typed decision 模型，公开测试也已用于多轮观察。证据在 `results/banking77-existing/`，判断边界和下一实验见 `_research/next-experiment.md`。

证据：`results/H384/` 保存完整逐题记录和配置；`results/B0-summary.json` 保存对照摘要。远端原始记录仍在 `runs/B0` 与 `runs/H384`。两次运行使用相同 JevBench checkout、Laya 权重和 DGX GPU。

## 研究判断

截图中的 NeoHorse 77.70 是作者定义的六组文本任务等权平均，不是 JevBench 官方总榜分。不能据此宣称 Laya 通过选题或限定词已接近榜首。公开题可用于诊断，但最终主张必须经过独立锁定测试和榜单的 sealed 评测。

当前主假设：通过独立来源的决策训练样本改善 Laya 的陷阱、证据不足、多跳及长规则判断；在必要时用开源推理模型处理难例，可以得到更好的质量、延迟、成本折中。纯 Laya 与组合系统分别评测，组合系统计入所有调用。

## E1 阶段结果（2026-09-25）

RuleTaker 固定、去重的 8,750/1,750/1,750 训练／开发／锁定测试试验已完成。Laya 原生 choice 决策头经两轮小规模训练，在 RuleTaker 锁定测试上从 50.74% 提升至 87.14%；但在 JevBench 公开 231 题上从 58.01% 变为 56.28%，没有通用迁移收益证据。完整数据边界、结果和权重索引见 `_research/E1-result.md`。下一轮需改变训练任务的覆盖面，不能用这 231 题筛选新方案。

## E2、E3 与提交准备（2026-09-26）

E2 四类自编任务训练使同生成器锁定测试由 37.55% 提至 98.54%；JevBench 旧公开 231 题仅由 58.01% 至 59.74%，配对区间跨零。E3 冻结 E2 后在外部公开来源上，BoolQ 400 题由 75.75% 至 79.25%，ARC-Challenge 299 题由 27.09% 至 29.10%。两来源等权平均提高 2.75 个百分点，但 ARC 的绝对成绩仍低，且两数据集是公开题。完整判断见 `_research/E2-result.md` 与 `_research/E3-result.md`。

JevBench 当前 v1.4.2 官方分数包含旧版 534 题、新的 308 道 sealed 题，以及 Intelligence、Calibration、Speed、Cost 四轴。上述 231 题诊断不能换算成现行榜单名次。E2 还没有 sealed 结果；运行库会对该权重部分温度参数进行夹取，概率校准需要单独审视。

`submission/` 提供固定 E2 权重的 Jev 兼容服务和模型卡。自包含权重已在 [v0.1.0 发布页](https://github.com/13974737898-lgtm/laya-e2-multitype/releases/tag/v0.1.0)公开；JevBench 自带 TypeSafe 适配器通过 choice、noul、score 三类真实 HTTP 请求，并与直接加载权重的概率一致。已发送 [JevBench 评测申请 #103](https://github.com/fstandhartinger/jevbench/issues/103)，披露研发中观察过公开题。目前仍只有本机接口验收，没有 sealed 成绩或正式名次。

外部规则与截图来源：[JevBench](https://github.com/fstandhartinger/jevbench/blob/main/README.md)；[NeoHorse 模型卡](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)。
