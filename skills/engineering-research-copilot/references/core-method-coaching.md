# 方法辅导

一般方法介绍或项目特定方法辅导均应用本协议。没有正式项目制品时仍可解释一般方法；正式方法卡只用于输入已经验证且用户明确确认的方向。

## 分开收敛与发散

使用**收敛通道**，根据纠正后的研究问题、约束、已有数据、资源边界和预期主张，比较有证据支持的方法选项。每个选项都说明适用性、假设、基线与对照、指标、不确定性处理、失效模式和最小判别检查。

只有替代机制或路径可能改善项目时，才使用**发散通道**。有意识地改变抽象层级、测量方式、表征、尺度、系统边界、控制策略或相邻领域类比。每个想法说明：

- 灵感来源和改变的设计维度；
- 相对目标领域直接验证的**证据距离**；
- 可能允许迁移的机制或结构相似性；
- **反迁移因素**和可能失效模式；
- 所需数据、方法和资源假设；
- 能够低成本否决该想法的**最小证伪检验**。

合格证据支持升级前，发散想法不得进入排序后的推荐，并始终标为假设而非发现。只有研究者看见替代项、反证和判别检验后再收敛；用户明确选择前，不把任何方向视为已确认。

用户要求来源，或项目特定建议依赖当前实证文献时，附上已核验论文。通过根 Skill 的论文校准与引文完整性流程返回；对每项重要来源展示核验状态、证据层级、支持内容、不支持内容、局限和反证。不得凭模型记忆引用方法论文。实质证据角色仍未解决时，建议保持暂定，并指出缺失证据，不得用看似合理的相邻论文填补。

## 选择呈现模式

默认使用**对话模式**：用普通科研语言说明方法匹配、假设、基线、检查、不确定性、失效模式和下一项判别检验。

仅当用户要求机器可读方法包、确定性复现或验证器兼容文件时，使用**制品模式**。该模式必须满足正式前提并应用下述全部精确结构。

编码状态流只用于制品模式。对话模式仍执行相同证据、兼容性和权限门槛，但不暴露状态码。

## 提供一般方法介绍

用户希望理解、比较或初步应用某种方法时，使用**一般方法介绍**。该模式不需要正式方向包。只加载适用的方法族参考，并区分一般工程知识、有来源支持的主张、项目假设和未知项。

覆盖适用性、最低输入与资源、可信基线、验证检查、不确定性处理、常见失效模式，以及最快暴露不匹配的最小检验。除非用户或合格证据给出来源，否则参数值和决策阈值保持暂定。该模式不得创建 M3 包。

## 目录

- 选择呈现模式
- 提供一般方法介绍
- 遵循 M3 状态流
- 推导可信 M2 上下文
- 选择辅导模式
- 返回闭合 M3 包
- 构建闭合方法卡
- 绑定资源与条件
- 维护类型化来源台账
- 添加领域叠加规则
- 遵守证据与权限边界

## 遵循 M3 状态流

使用以下准确状态流：

```text
M2_BUNDLE_VALID
  -> DIRECTION_USER_CONFIRMED
  -> SELECTED_DIRECTION_HASH_VALID
  -> ROUTE_ABSENT: BOUNDED_METHOD_COACHING
  -> ROUTE_PRESENT_AND_M3_COMPATIBLE: ROUTE_SPECIFIC_METHOD_CARD
  -> UNSUPPORTED_CONSTRAINT_APPROVAL: STOP_FOR_PROVENANCE_REPAIR
```

嵌入 M2 包无效、方向不是 `user_confirmed`、所选方向或包哈希过期，或者所选方向不能唯一解析到一个正式方向时，在方法卡处理前停止。

`route_output.approved_constraint_changes` 非空时，只返回 `unsupported_approved_constraint_change_provenance`。展示原所选方向的 `resource_limits`，不应用拟议变更，并要求修复来源。

## 推导可信 M2 上下文

读取任何 M2 字段前，使用 `validate_m2_direction_bundle.validate_bundle` 验证完整嵌入包。原样保留该包，不迁移、不规范化、不修复，也不写回。

推导下列值，不信任复制到 M3 的声明：

- 从 `direction_decision.selected_direction_id` 定位正式方向；
- 用规范 UTF-8 JSON 重新计算来源包和所选方向哈希；
- 从 `selected_direction.core_claims` 推导主张及类型；
- 从 `required_decision_metrics` 推导每项主张的指标 ID；
- 从 `minimum_decisive_test.claim_coverage` 推导每项主张的必要前提 ID；
- 从 `minimum_decisive_test.required_preconditions` 推导前提记录；
- 从 `selected_direction.resource_limits` 推导资源上限；
- 从 `source_m1_bundle.round2.candidate_pool` 推导合格来源记录；
- 保留所有上游证据缺口和核验限制。

路线特定辅导中，每个 `route_traceability.source_precondition_ids` 集合必须等于对应主张覆盖的前提集合。把每项主张的指标 ID 与 `route_output.go_conditions`、`stop_conditions`、`pivot_conditions` 中的指标 ID 相交，以推导实际推进、停止和转向覆盖。任何调用方声明的 `route_condition_types` 与推导集合不同都应拒绝。

## 选择辅导模式

只有研究者明确确认方向后，才使用**项目特定辅导**。用户要求制品模式时，还必须有经过验证的正式包并通过下述兼容性检查。

`route_output` 缺失时使用 `bounded`。说明适用方法、假设、基线、检查、不确定性处理、失效模式，以及绑定确认方向的数值停止或转向标准。不得制造完整路线、填补缺失可追踪性、扩大资源、执行路线或声称实证成功。

只有 `route_output` 存在、M2 验证器接受、M3 兼容性推导一致且已批准约束变更为空时，才使用 `route_specific`。依据所选主张、指标、前提、条件和原始资源限制实例化方法卡；路线叙述本身不是独立权威。

## 返回闭合 M3 包

只返回以下顶层字段：

```yaml
schema_version: "m3.1"
source_m2_bundle: {}
source_m2_bundle_hash: ""
selected_direction_id: "D1"
selected_direction_hash: ""
coaching_mode: "bounded|route_specific"
method_cards: []
domain_overlays: []
```

两个哈希都用重新计算的规范 SHA-256。拒绝未知顶层字段。至少需要一张有效方法卡；`domain_overlays` 可以为空列表。

## 构建闭合方法卡

方法族只能选择以下一种：

- `experiment_measurement_uq`；
- `modeling_simulation_vvuq`；
- `control_optimization_identification`；
- `signal_diagnostics`；
- `data_ml_hybrid`；
- `reliability_safety_risk`。

每张卡必须且只能含以下字段：

```yaml
schema_version: "m3.1"
card_id: "card:data-ml-hybrid:1"
method_family: "data_ml_hybrid"
applicability:
  supported_claim_types: []
  required_inputs: []
  incompatible_conditions: []
assumptions: []
minimum_resources: []
inherited_constraints: []
baselines: []
controls: []
procedure_outline: []
primary_metrics: []
uncertainty_handling: []
validation_checks: []
failure_modes: []
stop_conditions: []
pivot_conditions: []
safety_boundaries: []
source_ledger: []
```

拒绝未知字段和重复 `card_id`。所有列出字段均须非空。叙述列表使用非空文本行。`supported_claim_types` 只能使用所选方向的主张类型，`primary_metrics` 只能使用所选方向的指标 ID，且不得重复。必要输入和不兼容条件必须显式填写，不能从方法族叙述中推断。

## 绑定资源与条件

将 `selected_direction.resource_limits` 按原顺序和原值类型复制到每张卡的 `inherited_constraints`。最低资源行必须且只能含：

```yaml
resource: "CPU time"
required_value: 1
unit: "hours"
source_constraint_id: "R-CPU-HOURS"
```

`required_value` 必须是有限、非布尔数值。`source_constraint_id` 解析到一个继承资源限制，并与其 `resource` 和 `unit` 完全一致。最低资源只能绑定到 `<` 或 `<=` 上限；值等于 `<` 上限或大于 `<=` 上限时拒绝。不得把下限重新解释为上限。

每个停止或转向条件必须且只能含：

```yaml
criterion_type: "stop|pivot"
metric_id: "M1"
operator: "<|<=|>|>="
value: 0.0
unit: "ratio"
```

`stop_conditions` 中只能使用 `stop`，`pivot_conditions` 中只能使用 `pivot`。`value` 必须是有限、非布尔数值；指标 ID 必须解析到所选方向，单位必须完全一致。

## 维护类型化来源台账

每个来源台账行必须且只能含：

```yaml
source_id: "source:P7"
candidate_id: "P7"
basis_level: "metadata|abstract|full_text"
support_types:
  - "bibliographic_identity|method|result|transfer|safety"
supports: []
does_not_support: []
limitations: []
```

每行使用唯一非空 `source_id`。`candidate_id` 必须解析到 `source_m2_bundle.source_m1_bundle.round2.candidate_pool` 中可推荐且状态允许的已核验候选。拒绝 `partial`、`conflicted`、`not_found`、`manual_needed`、未知、歧义或不可推荐候选。

证据层级只能按下表准确映射：

| M1 层级 | M3 层级 |
|---|---|
| `metadata_level` | `metadata` |
| `abstract_level` | `abstract` |
| `fulltext_level` | `full_text` |

`support_types` 是 `bibliographic_identity`、`method`、`result`、`transfer` 和 `safety` 的非空、无重复子集。仅元数据证据只能使用 `bibliographic_identity`，不能从自由文本推断支持类型。`supports`、`does_not_support` 和 `limitations` 均为非空显式文本列表。已核验预印本可支持方法或探索，但不能成为主方向或安全相关结论的唯一依据。

`fixture_only` 来源只用于明确标注的离线 fixture。不得把 fixture 验证表述成文献核验、方法表现、路线执行或实证证据。

## 添加领域叠加规则

领域叠加使用以下准确字段：

```yaml
schema_version: "m3.1"
overlay_id: "domain:nuclear-ml:1"
domain: "nuclear_engineering_ml"
base_card_ids: []
additional_assumptions: []
additional_failure_modes: []
additional_validation_checks: []
additional_stop_conditions: []
specialist_review_boundaries: []
transfer_status: "hypothesis"
source_ledger: []
```

拒绝未知字段和重复叠加 ID。每个唯一 `base_card_id` 必须解析到同一包中的方法卡。叠加只增加领域约束，不能替换基础卡假设、检查、失效模式、停止条件或安全边界。每个附加列表和叠加来源台账均须非空。`additional_stop_conditions` 使用与方法卡相同的闭合数值条件，并绑定所选方向指标。

`domain` 固定为 `nuclear_engineering_ml`，`transfer_status` 固定为 `hypothesis`。至少需要一条合格非预印本台账记录，且 `support_types` 包含 `safety`。运行、监管和安全结论均划为专家复核边界。

## 遵守证据与权限边界

- 分开发现与核验，不得虚构或推断题名、作者、发表状态、DOI 或其他标识符。
- 每项断言通过台账层级标为元数据级、摘要级或全文级。
- 冲突、未解决和不可推荐引文不得进入方法卡或领域叠加。
- 跨领域迁移在目标领域判别检验支持前保持为假设。
- 闭合包验证只是结构化、确定性、离线契约证据。
- 有效方法卡不能证明方法有效、仿真有效、迁移成功或安全。
- 方法辅导期间不得执行实验、仿真、训练、下载、上传、启动服务、部署、分配资源或写文件。
- 任何副作用都需要用户另行明确请求，并在执行前重新检查安全与资源边界。
