# E2：多类型原生决策训练（事前方案）

冻结于 2026-09-25；在读取 E2 开发集模型结果前写入。

目标：检验四类独立生成的有标签决策题能否改善 Laya 原生 `choice` 接口，并观察是否比 E1 单一 RuleTaker 训练更能迁移到 JevBench。

## 数据与比较

- `multitype-e2-v1`：policy、temporal、evidence、routing 各 2,400/480/480 条 train/dev/test；每类三标签严格均衡，候选选项次序逐题打乱。生成代码和哈希见 `scripts/generate_multitype_e2.py` 与 `data/multitype-e2/manifest.json`。
- 三组使用不同随机种子、实体名和问题措辞；没有调用或改写 JevBench 原题。共用生成逻辑，因此 E2 test 只检验该任务族的泛化，不能独立证明真实世界能力。
- 基线：原版 Laya 与 E1 RuleTaker 权重。E2 从原版 Laya 权重开始训练，避免把 E1 作为不可控初始化因素。
- 训练只读取 E2 train；每轮完整 E2 dev 准确率最高者为最佳 checkpoint，平手用较低 dev NLL。两轮训练、seed `20260925`、batch 8、累积 4、encoder LR `2e-5`、其他参数 LR `1e-4`、监督交叉熵。锁定 E2 test 在 checkpoint 选定后只评测一次。

## 预期与判定

主指标为 E2 锁定 test 准确率和四类分项；次要指标为损失、失败数与同机延迟。只有训练在 E2 dev 明显优于原版和 E1，才进行一次 E2 test。随后冻结 checkpoint，在 JevBench 公开 231 题做一次配对诊断，与原版及 E1 对照。JevBench 公开题不能用于选择轮次、配比、提示词或阈值。

若 E2 test 改善而 JevBench 不改善，结论限定为生成任务专项能力；下一步转向真实来源的混合数据和更强的独立验证，不扩大同类模板数据。若 JevBench 公开题有上涨，也只视为探索性信号，正式榜单仍需 sealed 评测。
