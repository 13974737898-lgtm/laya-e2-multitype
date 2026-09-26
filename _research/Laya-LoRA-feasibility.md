# Laya 原生模型 LoRA 可行性检查

核对日期：2026-09-26。对象是 DGX 上现有英文 Laya 原生模型，而非两个 Qwen 模型。本次只做单样本结构和反向传播检查，没有运行训练、保存新 checkpoint 或测得准确率。

- Laya 的 `DecisionModel` 由双向编码器、类型嵌入、决策头、评分器和动作头组成。现有 E2 脚本对编码器和其余参数均做全量优化，**不是 LoRA**。
- DGX Laya 独立环境有 `peft==0.20.0`。编码器含 112 个线性模块，包括 `attn.Wqkv`、`attn.Wo`、`mlp.Wi`、`mlp.Wo`；可用 `LoraConfig(r=8, lora_alpha=16, target_modules="all-linear", lora_dropout=0.05, bias="none")` 包装 `agent.model.encoder`。
- 包装后模型总参数 424,892,163；可训练编码器 LoRA 参数 3,598,336，可训练的其他决策组件 26,512,131，合计 30,110,467（约 7.09%）。若只训练 LoRA 而冻结决策头，不能等同于本次验证的方案。
- DGX GB10 上单样本 `choice` 前向得到有限的二分类 logits；交叉熵反向后，LoRA 与决策组件均有梯度。未更新权重的 LoRA 合并回编码器前后，该样本 logits 最大绝对差为 0.0。这说明代码路径与合并接口可用，**不证明实际训练后精度或校准表现**。
- 原版 checkpoint 加载时有 choice 温度越界夹取警告。LoRA 不会自动修复该校准问题；如果形成新模型，仍须独立检查概率校准和 JevBench sealed 表现。

若要比较参数效率，应从同一原版 Laya 权重出发，用与 E2 相同的训练、开发和锁定测试协议，仅改变编码器优化方式；保留原生决策头训练，报告准确率、校准、延迟及公开 JevBench 诊断，不能用公开题选轮次或阈值。另起从 E2 checkpoint 继续 LoRA 属于不同问题，不能直接归因于 LoRA 优于 E2 全量微调。
