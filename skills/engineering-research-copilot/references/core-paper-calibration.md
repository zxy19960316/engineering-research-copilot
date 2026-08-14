# 论文校准状态契约

构建或修订一轮两阶段论文校准时，应用本文件。执行相应核验、证据图或反馈步骤前，从根 Skill 加载[引文完整性](core-citation-integrity.md)、[静态论文证据图](core-paper-map.md)和[反馈、检索历史与回滚](core-feedback-rollback.md)。

## 选择呈现模式

默认使用**对话模式**：用普通科研语言呈现研究简报、检索边界、已核验选择、证据缺口和反馈影响，把闭合状态对象保留在内部。

仅当用户要求机器可读的校准包、确定性复现或验证器兼容文件时，使用**制品模式**，并应用下述全部精确结构和终止状态规则。

编码状态流只用于制品模式。对话模式仍在内部执行相同门槛，但把停止解释为证据缺口以及可行的下一步。

## 检查证据充分性

把某个方向或方法表述为有证据支持前，检查当前问题是否具备足够的：

- **直接问题证据**，支持目标现象和工程需求；
- **方法证据**，支持拟议机制或技术；
- 跨领域、尺度、数据结构或工况时所需的**迁移或桥接证据**；
- 可能收窄或推翻建议的**反证或局限证据**；
- 每项重要来源经过核验的书目身份，以及明确的元数据级、摘要级或全文级依据；
- 可见的冲突、未成功检索边界、不可访问证据和未解决假设。

证据充分性相对于当前主张和决策，不意味着文献覆盖穷尽。缺少实质证据角色时，把结论标为暂定或证据不完整，说明缺失角色和已检索边界，并推荐最小后续检索或用户决策。不得用较弱或相邻记录填补，让组合看起来完整。

## 目录

- 选择呈现模式
- 检查证据充分性
- 遵循状态流
- 构建研究简报
- 规划检索
- 组装候选池
- 选择第一轮论文
- 应用反馈
- 选择第二轮论文
- 报告证据不完整
- 停在 M1 边界

## 遵循状态流

一个校准周期内保持同一 `branch_id` 和稳定候选 ID。反馈改变约束、偏好、开放问题或证据需求时，递增 `brief_version`。使用以下状态流：

```text
BUILDING_BRIEF
  -> PLANNING_ROUND_ONE
  -> VERIFYING_ROUND_ONE_CANDIDATES
     -> EVIDENCE_INCOMPLETE -> WAITING_FOR_EVIDENCE_DECISION
     -> ROUND_ONE_READY
  -> WAITING_FOR_FEEDBACK
  -> APPLYING_FEEDBACK
  -> PLANNING_ROUND_TWO
  -> VERIFYING_ROUND_TWO_CANDIDATES
     -> EVIDENCE_INCOMPLETE -> WAITING_FOR_EVIDENCE_DECISION
     -> ROUND_TWO_READY -> M1_COMPLETE
```

`EVIDENCE_INCOMPLETE` 和 `WAITING_FOR_EVIDENCE_DECISION` 都是结束当前尝试的非成功状态，不能转为 `M1_COMPLETE`。只有用户补充证据、改变要求或授权适当的有界后续检索后，才从受影响轮次恢复。

状态之间转换时不得跳过核验。保留研究简报、检索计划、候选池、选择结果、局限、缺口和反馈差异，使每次转换都可解释。只有两轮均通过所需证据门槛，并从 `ROUND_TWO_READY` 进入时，才能设置 `M1_COMPLETE`。

每个保存的校准包使用以下准确终止封装：

```yaml
schema_version: "m1.2"
terminal_state: "WAITING_FOR_EVIDENCE_DECISION" # 或 "M1_COMPLETE"
stopped_after_round: 1 # 或 2
outcome: "evidence_incomplete" # 或 "complete"
round1: {}
feedback_delta: {} # 仅 stopped_after_round 为 2 时必填
round2: {} # 仅 stopped_after_round 为 2 时必填
```

只允许以下一致组合：第一轮 `evidence_incomplete` 结束于 `WAITING_FOR_EVIDENCE_DECISION`；第二轮 `evidence_incomplete` 同样结束于该状态；第二轮 `complete` 结束于 `M1_COMPLETE`。`stopped_after_round` 为 `1` 时，省略 `feedback_delta` 和 `round2`，字段出现即拒绝；为 `2` 时，即使第二轮证据不完整，也必须保留二者。第一轮就绪且第二轮完成无缺口的合格选择之前，不得声称 `M1_COMPLETE`。

## 构建研究简报

提问前先提取用户已提供的事实。一次最多问三个短问题，并且只问会实质改变查询构造或推荐资格的缺失字段。未知内容保留为空值或写入 `open_questions`，不得推断。

使用以下准确结构：

```yaml
research_brief:
  brief_version: 1
  branch_id: "branch-a"
  engineering_object: ""
  target_problem: ""
  target_metric: ""
  available_data: []
  resources: []
  time_budget: ""
  preferred_routes: []
  excluded_routes: []
  hard_constraints: []
  soft_preferences: []
  open_questions: []
  evidence_needs: []
```

必须且只能使用这 14 个字段。`brief_version` 为正整数且不能是布尔值。`branch_id`、`engineering_object`、`target_problem`、`target_metric` 和 `time_budget` 必须是非空文本。其余所列集合字段即使为空也保持列表。硬约束与软偏好分开。缺失信息不妨碍有界检索时，写入 `open_questions`；只有答案会实质改变查询或让推荐资格无法判断时，才在检索前停止并提问。

## 规划检索

把当前简报转成目的和预期证据角色不同的查询，使用以下准确结构：

```yaml
search_plan:
  round: 1
  brief_version: 1
  branch_id: "branch-a"
  time_boundary: []
  language_boundary: []
  source_boundary: []
  queries:
    - query_id: "Q1"
      purpose: "direct_problem"
      query_text: ""
      expected_evidence_role: "direct_problem"
      inclusion_terms: []
      exclusion_terms: []
  limitations: []
```

计划必须且只能含八个字段，包括所有边界和 `limitations`；即使为空，也保持列表。`round` 与外层轮次一致，`brief_version` 和非空 `branch_id` 与当前简报一致。

每个查询必须且只能含六个字段。`query_id` 非空且在轮次内唯一，`query_text` 非空；`purpose` 和 `expected_evidence_role` 只能取 `direct_problem`、`method`、`transfer_bridge` 或 `counter_limitation`。`inclusion_terms` 和 `exclusion_terms` 保持列表。查询文本必须可追踪到简报，并显式展示排除条件。

报告检索边界及其局限。不得把有边界结果描述为穷尽、完整证明创新性，或证明既有研究不存在。

## 组装候选池

发现命中与候选池保持分开。只有应用[引文完整性](core-citation-integrity.md)后，记录才能进入 `candidate_pool`。条目使用以下契约：

```yaml
candidate_pool:
  - candidate_id: "P1"
    verification_status: ""
    recommendation_eligible: false
    evidence_roles: ["direct_problem"]
    selection_role: "direct_problem"
    basis_level: "metadata_level"
    verified_record: {}
```

每个候选在两轮中使用同一稳定 `candidate_id`。保留、降级或第二轮重审时不改 ID；不得用同一 ID 指向不同作品，也不得给同一沿用作品分配新 ID。

每项恰好包含一个已核验论文记录及当前核验状态。每项都必须有 `selection_role`，且只能取 `direct_problem`、`method`、`transfer_bridge` 或 `counter_limitation`；所选值必须出现在该项 `evidence_roles` 中。缺失、越界或不受支持的角色均无效。

选择前完成去重。未解决、冲突、未找到或需人工复核的记录不得进入推荐池，而应单独保存在局限或证据缺口中。

可靠证据存在时，第一轮组装 15–20 条经过核验和去重的候选，尽量覆盖直接问题、方法、迁移/桥接和反例/局限需求。不得为凑数而创建元数据、标识符、作者、题名、发表状态或证据角色。

## 选择第一轮论文

只有候选池支持固定分配“三篇 `direct_problem`、两篇 `method`、两篇 `transfer_bridge`、一篇 `counter_limitation`”时，才选择八条可推荐记录。严格按候选池项的 `selection_role` 计数，不得从证据图、自由文本或其他角色推断配额。`selected_ids` 中每一项必须唯一解析到一个候选池项和一个已核验记录；缺失、重复、歧义或阻断状态均拒绝。

任一角色不足时，不得用较弱、其他角色或不合格发现命中替代。空缺保持为空，把缺失角色和数量写入 `evidence_gaps`，设置 `evidence_incomplete`，并在 `WAITING_FOR_EVIDENCE_DECISION` 结束。

按[静态论文证据图](core-paper-map.md)生成面向用户的图及等价文本回退。每项图中主张不得超过其元数据、摘要或全文证据层级。

轮次包使用以下准确结构：

```yaml
round_bundle:
  schema_version: "m1.2"
  round: 1
  research_brief: {}
  search_plan: {}
  candidate_pool: []
  selected_ids: []
  paper_map: {}
  evidence_gaps: []
  search_limitations: []
```

`research_brief` 与 `search_plan` 必须放完整对象，不得使用摘要。未解决证据需求复制到 `evidence_gaps`；工具、来源、时间、语言、访问和全文限制复制到 `search_limitations`。

## 应用反馈

接受普通对话反馈。用户拒绝论文、质疑引文、改变约束或方向、要求重置时，应用[反馈、检索历史与回滚](core-feedback-rollback.md)诊断。

用以下契约暴露转换：

```yaml
feedback_delta:
  from_brief_version: 1
  to_brief_version: 2
  inherited:
    - object_id: "public-data-only"
      value: "仅使用公开数据"
  rejected:
    - object_id: "random-split-dependent-designs"
      value: "把同一物理来源混入训练集和测试集的设计"
      reason: "这会通过泄漏夸大评估"
  reset:
    - object_id: "round-one-title-level-fit"
      previous_value: "题名相关性曾被视为初步匹配"
      reason: "题名证据不能证明隔离或抗泄漏性"
  added:
    - object_id: "cross-load-evaluation-priority"
      value: "优先评估跨负载或未见工况"
      reason: "用户把这类证据提升为主要筛选条件"
  allocation:
    exploit: 30
    explore: 70
  query_changes:
    - query_id: "Q-STABLE"
      reason: "排除私有数据路线并扩大公开仿真证据"
      cause_refs:
        - "feedback_delta.rejected[0]"
        - "feedback_delta.reset[0]"
        - "feedback_delta.added[0]"
      before: "使用专有工业数据的数据驱动控制"
      after: "使用公开仿真数据且排除专有数据的数据驱动控制"
```

`feedback_delta` 只能包含上述顶层字段。每类条目 schema 均闭合：继承项恰为 `{object_id,value}`，拒绝项恰为 `{object_id,value,reason}`，重置项恰为 `{object_id,previous_value,reason}`，新增项恰为 `{object_id,value,reason}`。拒绝未知字段，每个字段值均须为非空文本。规划下一检索分支前，展示继承、拒绝、重置和新增约束。`allocation` 使用整数且合计 100，表示查询与候选预算，不是概率。

第二轮前创建新的简报版本，并让第二轮计划匹配新版本。M1.2 没有分支变更对象，因此两轮 ResearchBrief 和两轮 SearchPlan 必须共享同一非空 `branch_id`。拒绝理由、新约束或重置实质改变检索时，至少加入一条 `query_changes`。

每项查询变更必须有非空 `cause_refs`，准确指向现有 `feedback_delta.rejected`、`feedback_delta.reset` 或 `feedback_delta.added` 条目，绝不能指向 `inherited`。每项实质拒绝、重置或新增内容至少被一条路径覆盖；路径无法解析或实质内容未覆盖时拒绝。

修改查询时，同一 `query_id` 在两轮各恰好出现一次；`before` 只能等于第一轮该查询的 `query_text`，`after` 只能等于第二轮该查询的 `query_text`。新增查询的 ID 第一轮不存在、第二轮恰好出现一次，且 `after` 等于其文本；删除查询反之，且 `before` 等于其文本。不能用 ID、用途、角色或术语代替 `query_text`。

新增查询只允许 `before` 为空，删除查询只允许 `after` 为空，修改查询必须给出两个非空且不同的值。修订计划必须落实每个非空 `after`。不得在计划不变且没有说明时声称反馈已经应用。

## 选择第二轮论文

构建 `round: 2` 的第二轮 `RoundBundle`，包含修订简报、修订检索计划和用于选择的已核验候选状态。沿用记录保持候选 ID，新作品才分配新 ID。

可靠证据存在时，默认返回五到六篇可推荐论文。缺失的角色覆盖和检索限制保持可见，不得用弱记录补位。

`round_two_request` 只能出现在第二轮包中。例如，用户明确要求八篇时使用：

```yaml
round_bundle:
  schema_version: "m1.2"
  round: 2
  research_brief: {}
  search_plan: {}
  candidate_pool: []
  selected_ids: ["P1", "P2", "P4", "P5", "P9", "P16", "P17", "P18"]
  round_two_request:
    explicit_user_request: true
    requested_count: 8
  paper_map: {}
  round_one_dispositions: []
  evidence_gaps: []
  search_limitations: []
```

默认五到六篇时，省略 `round_two_request` 或设 `explicit_user_request: false`；对象存在时，整数 `requested_count` 必须等于第二轮 `selected_ids` 数量。只有明确请求为真且数量一致时，才允许七到十篇。未经授权的七到十篇、数量不匹配、超过十篇，或第一轮出现该字段均无效。不得从旧简报、分配比例或助手建议中推断扩展授权。

第二轮包必须带 `round_one_dispositions`，结构如下：

```yaml
round_one_dispositions:
  - round_one_id: "P3"
    disposition: "removed"
    round_two_id: null
    reason: "依赖无法访问的专有数据"
    cause_type: "feedback_delta"
    cause_ref: "feedback_delta.rejected[0]"
```

第一轮每个 `selected_id` 必须且只能对应一项处置，未选 ID 不能出现。`disposition` 只能取 `retained`、`replaced`、`downgraded` 或 `removed`：

- `retained`：同一稳定候选仍在第二轮被选，`round_two_id` 等于原 ID；
- `replaced`：第一轮候选退出，由新纳入或新优先候选替代，`round_two_id` 指向该已选替代项；
- `downgraded`：新核验或推理证据降低资格、角色或层级。只有仍可推荐且被选时，`round_two_id` 才等于原 ID；否则为 null，并在 `selected_ids` 外保留标记后的补充或阻断记录；
- `removed`：退出且没有一对一替代，`round_two_id` 为 null。

每项处置需要非空 `reason`。`cause_type` 只能取 `feedback_delta` 或 `new_evidence`。反馈原因只能指向准确存在的 `rejected`、`reset` 或 `added` 条目，不能指向 `inherited`；新证据原因必须指向确切的新核验来源或证据记录，不能指向模糊叙述、模型记忆或未核验发现。

第二轮就绪前，处置项必须准确覆盖第一轮选择一次。被替代项不得留在第二轮选择中；其非空 `round_two_id` 必须解析到一个合格的已选记录。保留项必须继续位于第二轮选择中。

替代目标必须一对一。每个 `replaced.round_two_id` 在处置列表中唯一，不能与另一个替代项共享，也不能等于保留或降级项声明的 `round_two_id`。缺失、为空、重复、共享、冲突或其他不可追踪处置均无效。

## 报告证据不完整

已核验候选池、选择数量、角色覆盖、来源访问或推理层级不足以支持完整轮次时，设置 `evidence_incomplete`。`selected_ids` 只能含合格记录，缺失位置保持为空。

当前尝试在 `WAITING_FOR_EVIDENCE_DECISION` 结束，M1 保持未完成；不得把可见缺口重新解释为成功。

第一轮发生缺口时，只保存根终止字段和 `round1`，不得虚构反馈或空第二轮。第二轮发生缺口时，保留已应用的 `feedback_delta`、尝试过的 `round2`、处置、局限和准确缺口。

报告：

- 已完成的检查及其证据层级；
- 准确缺少的数量、角色、来源或核验步骤；
- 导致缺口的边界和局限；
- 继续所需的用户决定或额外证据。

不得把发现命中、部分元数据、仅摘要检查、fixture 或离线结构验证转成真实引文核验证明。不得削弱门槛或虚构记录，以生成看似完整的包。

## 停在 M1 边界

报告现有论文校准状态、证据图、反馈影响、缺口和局限后结束当前输出。只有完整的 `ROUND_TWO_READY` 路径成功时，才把两轮流程标为 `M1_COMPLETE`；结果为 `evidence_incomplete` 时，在 `WAITING_FOR_EVIDENCE_DECISION` 结束，M1 保持未完成。

此处 `M1_COMPLETE` 只是工作流成功状态，不是在外部验收门槛通过前关闭仓库里程碑的权限。不得在此阶段排序研究方向、生成方向卡、选择主方向、创建完整实验或仿真路线、构建方法语料库、连接 RRC、增加检索服务、下载模型、部署运行时或开始平台集成。

后续工作会越过该边界时，明确询问用户下一方向。审计保持只读；没有用户明确请求时，不写入用户文件。
