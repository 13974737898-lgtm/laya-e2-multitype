# 下一轮实验：原生 Laya 决策头的独立迁移检验

日期：2026-09-25。状态：方案固定前的数据审查阶段，尚未启动本轮训练。

## 两条成果线

1. **专项意图分类**：DGX 已有 Banking77 实验，使用 Laya 的 ModernBERT 编码器、CLS/mean pooling 和新建的 77 类线性头。最终三模型 ensemble 在公开 3,080 条测试集上记录 94.35% accuracy、94.34% macro-F1。源训练集经规范化文本去重、移除与测试集重叠的 25 条及冲突标签 2 条。开发集、校准集、最终重训计划和结果已保存。由于此前多个 checkpoint 的公开测试结果已被观察，不能称最后 94.35% 为首次盲测。它也不是原生 Laya 通用决策头的成绩。详见 `results/banking77-existing/`。
2. **通用决策冲榜**：保留 Laya 原生的 typed choice/noul/score 接口，训练时只用 JevBench 外部数据；开发集负责选择训练轮次和阈值，JevBench 公开 231 题仅用于冻结后的诊断，正式结论依赖 sealed 评测。

## 主假设与最小试验

假设：独立规则推理数据上的原生 Laya 训练，可提高规则条件翻转、多跳和信息不足判断，同时保持快速单次前向。首个候选数据是 RuleTaker：其公开镜像标注 Apache-2.0，含 train/dev/test 三个划分；其样本是 context、question、label。先核对镜像与原始来源、标签语义、重复与近重复、数据生成模板跨划分共享情况，再决定是否用作训练。RuleTaker 的同源测试可用于验证训练机制，但不能单独证明 JevBench 迁移。

执行门：

- 冻结数据版本、哈希、train/dev/test 划分；只从 train 训练，只从 dev 选 checkpoint 与温度；test 在选择结束后一次性评估。
- 与原版 Laya、相同训练数据的简单双类头、以及不训练的提示词/配置基线作配对比较。若原生头的训练无法稳定收敛，先修实现而非扩大数据。
- 主要结果：锁定测试准确率与按推理深度/否定条件分层准确率；次要结果：ECE、Brier、p50/p95 延迟、吞吐、显存、无效输出和不同选项顺序的波动。报告至少三个种子或说明资源不足。
- 判定是否扩大到多源 100k：独立测试相对原版有明确收益，且 JevBench 公开题无明显退化；否则保留负结果并调整数据机制。公开 JevBench 结果不能用于模型选择。

组合系统在纯 Laya 模型稳定后再做：用 dev 集确定 Laya 置信度升级阈值；相同固定样本上报告升级率、总准确率、端到端延迟、每千决策成本，并与开源模型全量处理比较。榜单若不对组合系统给名次，明确作为系统评测发表。

来源：[RuleTaker 数据卡](https://huggingface.co/datasets/tasksource/ruletaker)；[RuleTaker 原始项目](https://github.com/allenai/ruletaker)；[JevBench 官方仓库](https://github.com/fstandhartinger/jevbench)。
