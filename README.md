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

## 下一实验门

先固定一套训练外开发集和锁定测试集、数据来源许可、重复/近重复检查、模型与脚本版本，再做小规模训练试验。训练素材不得包含 JevBench 公开题、近义改写或答案解析；JevBench 公开集不用于选 checkpoint 或调组合阈值。小试验需要同时报告独立测试准确率、校准、延迟、成本与能力回退。只有小试验证明增益，才扩大到 100k 训练方案。

外部规则与截图来源：[JevBench](https://github.com/fstandhartinger/jevbench/blob/main/README.md)；[NeoHorse 模型卡](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)。
