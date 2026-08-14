# 方向决策与路线门槛

比较、修改、拒绝或确认研究方向时，应用本文件。对话模式只依据用户实际拥有的已核验证据和约束推理。只有某一论文校准分支达到 `M1_COMPLETE` 后，才使用正式决策包流程。

## 选择呈现模式

默认使用**对话模式**：给出紧凑的方向组合，并说明证据强度、可行性、风险、反迁移因素和最小判别检验；里程碑名和闭合状态对象保留在内部。

仅当用户要求机器可读决策包、确定性复现或验证器兼容文件时，使用**制品模式**。该模式必须接收已验收校准包，并执行下述每一项准确结构和状态转换。

编码状态流只用于制品模式。对话模式仍在内部执行相同证据与确认门槛，并用科研语言说明后果。

## 目录

- 选择呈现模式
- 遵循 M2 状态流
- 保留 M1 证据来源
- 返回有界方向组合
- 评分前通过硬门槛
- 分配迁移证据层级
- 执行预印本支持规则
- 沿实质轴区分方向
- 比较合格方向
- 定义最小判别检验
- 要求用户确认
- 确认后交接

## 遵循 M2 状态流

使用以下状态流：

```text
M1_COMPLETE
  -> BUILDING_DIRECTION_PORTFOLIO
  -> CHECKING_DIRECTION_HARD_GATES
     -> DIRECTION_EVIDENCE_INCOMPLETE
     -> DIRECTION_PORTFOLIO_READY
  -> WAITING_FOR_DIRECTION_CONFIRMATION
     -> DIRECTION_REJECTED
     -> DIRECTION_MODIFICATION_REQUESTED
     -> USER_CONFIRMED
  -> ROUTE_GATE_OPEN
```

`DIRECTION_EVIDENCE_INCOMPLETE`、`DIRECTION_REJECTED` 和 `DIRECTION_MODIFICATION_REQUESTED` 均关闭路线门槛。所有正式方向通过硬门槛后，才能进入 `WAITING_FOR_DIRECTION_CONFIRMATION`；只有从 `USER_CONFIRMED` 才能进入 `ROUTE_GATE_OPEN`，任何得分、置信度或系统建议都不能绕过该转换。

保存一个具有以下准确顶层结构的 M2 决策包：

```yaml
source_m1_bundle: {}
direction_portfolio: {}
direction_decision: {}
route_output: null
```

只有明确标注的离线契约 fixture 才可额外使用 `fixture_mode`、`evidence_class`、`proves` 和 `does_not_prove`。拒绝其他顶层字段。

## 保留 M1 证据来源

把完整的已验收 M1 包原样嵌入 `source_m1_bundle`；不得改变、删除或重新分类任何候选 ID、核验状态、推荐资格、证据层级、已核验记录或证据缺口。嵌入包必须同时满足：

- `schema_version` 为 `m1.2`；
- `terminal_state` 为 `M1_COMPLETE`；
- `stopped_after_round` 为 `2`；
- `outcome` 为 `complete`；
- M1 验证器返回 `valid`。

将嵌入包按键排序、紧凑分隔符、保留非 ASCII 字符的规范 UTF-8 JSON 编码后，计算小写 SHA-256 作为 `source_m1_bundle_hash`。调用方提供的哈希必须重新计算，不能直接信任。

所有 M2 证据引用必须解析到 `source_m1_bundle.round2.candidate_pool`。候选必须保留 M1 的 ID、核验状态、推荐资格和证据层级。拒绝未知、歧义、阻断候选，以及只存在于发现局限中的引用。即使有效 M2 来源没有未解决的第二轮选择缺口，也要保留 M1 证据缺口；不得把不完整 M1 包重新解释为完整方向证据。

## 返回有界方向组合

组合使用以下准确结构：

```yaml
direction_portfolio:
  schema_version: "m2.1.1"
  source_m1_terminal_state: "M1_COMPLETE"
  source_m1_bundle_hash: ""
  brief_version: 2
  branch_id: "branch-a"
  directions: []
  high_risk_ideas: []
  portfolio_status: "provisional"
```

`brief_version` 和 `branch_id` 必须与已验收 M1 第二轮研究简报及检索计划一致。组合就绪时，正式方向恰好三项：

1. 一个 `provisional_main`；
2. 一个 `adjacent_alternative`；
3. 一个 `transfer_exploration`。

正式方向使用以下准确结构：

```yaml
direction_id: "D1"
position: "provisional_main"
title: ""
evidence_tier: "transfer-supported"
claim_language: "Recommended for priority validation"
axis_profile:
  problem: ""
  method: ""
  data: ""
axis_changes: []
core_claims: []
resource_limits: []
hard_gates: []
transfer_case: {}
scorecard: {}
minimum_decisive_test: {}
supporting_candidate_ids: []
counter_candidate_ids: []
unknowns: []
confidence: "medium"
recommendation_status: "provisional"
```

每个方向使用唯一非空 ID 和题名。每个正式方向至少需要一个可推荐的 M1 支持候选和一个可推荐的反证或局限候选。即使硬门槛全部通过，系统建议仍保持 `provisional`。

`high_risk_ideas` 最多可放两项，且每项只能含 `direction_id`、`title`、`evidence_tier`、`claim_language`、`supporting_candidate_ids`、`unknowns` 和 `recommendation_status`。必须设置 `evidence_tier: speculative`、`claim_language: High-uncertainty idea` 和 `recommendation_status: unranked_high_risk`，不能纳入正式得分或位置。

三个正式方向均通过硬门槛并可比较时，`portfolio_status` 才能为 `provisional`。任一正式方向失败时，设为 `evidence_incomplete`；不得通过省略失败方向或提升高风险想法来掩盖停止。

## 评分前通过硬门槛

每个正式方向必须恰好包含以下硬门槛：

- `target_problem_evidence`；
- `data_availability`；
- `falsifiability`；
- `resource_feasibility`；
- `time_feasibility`；
- `safety_ethics_compliance`；
- `m1_citation_integrity`。

门槛使用以下准确结构：

```yaml
gate_id: "target_problem_evidence"
status: "pass"
evidence_candidate_ids: []
required_precondition_ids: []
rationale: ""
blockers: []
```

`status` 只能取 `pass` 或 `fail`，`rationale` 必须非空。目标问题与引文完整性门槛至少引用一个 M1 候选。所有未解决的资源、时间、安全、伦理、合规、数据或验证阻断项都写入 `blockers`，并让相应门槛失败。

任一门槛失败时，要求 `scorecard: null` 和 `recommendation_status: excluded`。不得计算、保留或展示该方向加权总分。组合状态设为 `evidence_incomplete`，决策状态设为 `direction_evidence_incomplete`，不得进入用户确认。

通过 `required_precondition_ids` 把每个门槛绑定到相关结构化前提。某项前提为 `unresolved` 且 `blocking_if_unresolved: true` 时，其命名门槛必须失败、方向得分卡必须为 `null`、推荐状态必须为 `excluded`，组合和决策均停在证据不完整状态。

## 分配迁移证据层级

只能使用以下闭合层级，并把允许措辞准确复制到 `claim_language`，不能改写成更强表述：

| 层级 | 必要依据 | 允许措辞与位置 |
|---|---|---|
| `established-in-target` | 存在目标领域直接验证或高度等价验证 | `Direct evidence supports applicability`；可作为主方向、相邻方向或迁移探索 |
| `transfer-supported` | 目标需求、来源成功、兼容性图、反迁移分析和判别检验均存在 | `Recommended for priority validation`；作为主方向时置信度最高为中等，也可作为相邻方向或迁移探索 |
| `mechanism-plausible` | 原理或数据兼容性合理，但桥接证据不完整 | `Divergent exploration suggestion`；只能作为迁移探索，不能作为主要结论 |
| `speculative` | 支持主要来自类比或创造性联想 | `High-uncertainty idea`；只能作为未排序的高风险想法 |

`transfer-supported` 不要求目标领域已有完全相同方法的成功先例。不得把名称、原理、机制或数据形态的兼容性升级为已确立的目标适用性。

## 执行预印本支持规则

支持类别只能从 `source_m1_bundle.round2.candidate_pool` 解析，使用真实 `verification_status` 和 `recommendation_eligible`；不得接受方向层自报来源类别。

- `verified_preprint` 可用于方法或探索支持。
- `provisional_main` 的支持 ID 中至少有一个可推荐的 `verified_primary` 或 `verified_registry` 候选。
- 带证据且通过的 `safety_ethics_compliance` 门槛至少有一个可推荐非预印本候选。
- 检查非预印本支持时忽略 `recommendation_eligible: false` 和阻断候选。
- 相应违规返回 `provisional_main_requires_non_preprint_support` 或 `safety_gate_requires_non_preprint_support`。

每个正式方向使用以下准确迁移案例结构：

```yaml
target_problem_evidence: []
source_success_evidence: []
transfer_compatibility:
  concepts: []
  units: []
  scales: []
  boundary_conditions: []
  assumptions: []
anti_transfer_factors: []
```

两个证据列表都必须包含候选 ID。`transfer-supported`、`mechanism-plausible` 及 `transfer_exploration` 位置的每个兼容性维度和 `anti_transfer_factors` 至少有一条非空内容。真正直接且不涉及迁移的 `established-in-target` 方向，才能使用“因为……不适用”条目；不能用空列表暗示兼容。

## 沿实质轴区分方向

每个正式方向给出一个闭合 `axis_profile`，且恰含 `problem`、`method` 和 `data`。把暂定主方向视为共同基线，通过比较其他方向与基线推导 `axis_changes`，不能信任调用方声明。

实质变化使用以下对象：

```yaml
axis: "method"
from: ""
to: ""
```

`axis` 只能取 `problem`、`method` 或 `data`；`from` 与 `to` 必须非空且不同。暂定主方向没有轴变化，相邻方向恰有一个轴变化，迁移探索至少有两个不同轴变化。拒绝只改题名、同义表达但轴值相同、重复轴，以及问题—方法—数据组合相同的三张卡。

核心主张使用以下闭合结构：

```yaml
core_claims:
  - claim_id: "C1"
    claim: ""
    claim_type: "predictive_performance|uncertainty_quality|open_set_detection|data_availability|safety"
    evidence_candidate_ids: []
    required_decision_metrics:
      - metric_id: "M1"
        metric: ""
        metric_role: "predictive_performance|uncertainty_quality|open_set_detection|data_availability|safety"
        unit: ""
```

每个候选 ID 都要解析到合格 M1 记录。指标角色必须与主张类型对应；不确定性质量主张不能只靠预测误差指标，开放集主张不能只靠闭集准确率。

数值资源上限使用 `constraint_id`、`resource`、`operator`、有限 `value` 和 `unit`，运算符只能取 `>=`、`<=`、`>` 或 `<`。

## 比较合格方向

只对全部硬门槛通过的方向评分。所有已排序方向使用相同权重，且整数权重合计 100：

| 维度 | 默认权重 |
|---|---:|
| `engineering_value` | 15 |
| `gap_and_evidence_quality` | 15 |
| `data_and_resource_fit` | 20 |
| `validation_and_falsifiability` | 15 |
| `method_maturity` | 10 |
| `time_to_decisive_signal` | 10 |
| `interdisciplinary_interface_quality` | 10 |
| `safety_ethics_compliance` | 5 |

得分卡使用以下准确结构：

```yaml
dimensions:
  - dimension: "engineering_value"
    weight: 15
    score: 0
    evidence_candidate_ids: []
    evidence: ""
    confidence: "low"
    unknowns: []
    change_triggers: []
weighted_total: 0.0
```

`score` 是 0 至 5 的整数。将 `weighted_total` 重新计算为 `sum(score * weight / 5)`，不一致时拒绝。每个维度都需要非空证据、置信度、未知项和变化触发条件。总分只作决策辅助，不能覆盖硬门槛或用户确认门槛。

每个命名维度使用以下锚点：

| 得分 | 含义 |
|---:|---|
| 0 | 该维度失败或没有合格支持。 |
| 1 | 支持极弱，且存在主导性的实质阻断项。 |
| 2 | 支持偏弱或混合：强于 1，但不足以达到可辩护中点。 |
| 3 | 支持基本充分，但仍有实质不确定性。 |
| 4 | 支持较强：优于 3，但尚未全面到足以给 5。 |
| 5 | 在当前决策阶段，支持异常强、具体且充分说明局限。 |

解释必须使用该维度特有的证据、未知项和变化触发条件。候选 ID 可跨维度重复，但完整理由三元组的规范化重复必须拒绝。不得用开放式自然语言处理推断分数质量。

## 定义最小判别检验

每个正式方向使用以下准确对象：

```yaml
scope: "minimum_decisive_test"
hypothesis: ""
inputs: []
baseline: ""
steps:
  - step_id: "S1"
    action: ""
    bounded_output: ""
primary_metric_id: "M1"
claim_coverage:
  - claim_id: "C1"
    metric_ids: ["M1"]
    decision_criteria:
      - criterion_type: "success"
        metric_id: "M1"
        operator: ">="
        value: 0.0
        unit: ""
    required_precondition_ids: []
required_preconditions:
  - precondition_id: "P1"
    description: ""
    gate_id: "data_availability"
    status: "verified"
    evidence_candidate_ids: []
    blocking_if_unresolved: true
    preflight_check: ""
    stop_condition:
      metric: ""
      operator: "<"
      value: 0.0
      unit: ""
expected_time: ""
required_resources: []
```

要求非空且可证伪的假设、输入、基线、主指标 ID、预期时间、资源，以及恰好二到四个闭合步骤对象。每个步骤字段和整个序列化对象必须在验证器限制内；通过闭合结构与大小限制拒绝嵌套路线对象、长路线载荷、训练矩阵、部署阶段、下载计划、服务拓扑或完整资源日程。

每项核心主张恰好覆盖一次。每个主张指标都需要带明确单位的有限数值成功、停止、转向或证伪标准。数据可用性主张必须绑定结构化前提。所有重要输入、标签、划分、样本量、采样率和时间范围标为 `verified`、`bounded_testable` 或 `unresolved`，并要求有界预检与数值停止条件。无法给出可辩护数值标准时，在 `DIRECTION_EVIDENCE_INCOMPLETE` 停止，不能用“有意义的改善”替代。

## 要求用户确认

使用以下准确决策结构：

```yaml
direction_decision:
  selected_direction_id: null
  status: "waiting_for_user_confirmation"
  permitted_next_actions:
    - confirm
    - modify
    - reject
  confirmation_event: null
```

只允许以下一致组合：

| 状态 | 所选 ID | 允许的下一行动 | 路线输出 |
|---|---|---|---|
| `direction_evidence_incomplete` | `null` | `modify`、`reject` | `null` |
| `waiting_for_user_confirmation` | `null` | `confirm`、`modify`、`reject` | `null` |
| `modification_requested` | `null` | `modify`、`reject` | `null` |
| `rejected` | `null` | `modify` | `null` |
| `user_confirmed` | 一个正式方向 ID | `modify`、`reject`、`generate_route` | `null` 或一个有效路线对象 |

自然语言中的热情、得分、已接受论文图或系统建议都不构成确认。必须由用户明确选择一个正式方向 ID。修改或拒绝时，应用反馈与回滚协议并保留旧包，不得静默变异。

所有未确认状态必须设置 `confirmation_event: null`。`user_confirmed` 需要以下闭合事件：

```yaml
confirmation_event:
  actor_role: "user"
  selected_direction_id: "D1"
  source_message_id: ""
  source_message_excerpt: ""
  source_message_sha256: ""
  previous_bundle_hash: ""
```

摘录必须明确包含所选正式方向 ID，并对其准确 UTF-8 文本计算哈希。重建等待确认的前一版包，重新计算规范 SHA-256，并匹配 `previous_bundle_hash`。事件 ID 与 `direction_decision.selected_direction_id` 必须一致。缺失事件、非用户角色、高风险或未知 ID、过期包哈希，以及把确认事件附在未确认状态上，均拒绝。该契约只能证明内部来源一致性，不能验证宿主系统中的用户身份。

进入 `user_confirmed` 前，拒绝 M2 包任意位置出现完整实验步骤、完整仿真路线、训练计划、模型下载、服务部署或大规模资源执行。未知嵌套路由字段无效。最小判别检验只是有界方向门槛制品，不是完整路线。

## 确认后交接

确认后允许 `route_output` 保持 `null`。用户要求生成路线时，返回根路由并应用研究路线规划。交接时继续以已确认方向、确认来源、证据缺口、指标、前提和资源限制为权威。确认只开启路线规划，不自动生成或执行路线。

## 记录 m2.1.1 兼容性边界

把 m2.1.1 视为破坏性验证修订。新增必填字段包括确认来源、轴描述、核心主张、资源限制、结构化前提与主张覆盖，以及路线哈希和可追踪性。不得把这些字段视为可选项，从而将 m2.1 包当作 m2.1.1 接受。旧 fixture 只能由冻结的 m2.1 验证器或明确迁移工具读取。规范 JSON 和 CLI 状态/退出码规则保持兼容。
