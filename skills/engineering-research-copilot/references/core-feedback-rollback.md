# 反馈、检索历史与回滚

用户评价论文、改变约束、拒绝方向、质疑引文或要求重置时，应用本文件。

## 选择呈现模式

默认使用**对话模式**：展示继承、拒绝、重置和新增的约束，并说明它们如何改变下一行动；精确状态对象保留在内部。

仅当用户要求机器可读反馈差异、确定性复现或正式审计记录时，使用**制品模式**并应用下述全部精确结构。

编码状态流只用于制品模式。对话模式仍在内部保留相同回滚逻辑，并直接展示已变约束及其后果。

## 目录

- 维护带版本的研究简报
- 检索前诊断不满意原因
- 控制历史影响
- 生成准确反馈差异
- 把实质反馈落实到查询
- 检索前展示变更日志
- 遵循状态流
- 保留不确定性

## 维护带版本的研究简报

使用以下结构保存推理状态：

```yaml
brief_version: 3
branch_id: "branch-b"
confirmed_constraints: []
soft_preferences: []
positive_signals: []
negative_signals:
  - object: "论文、簇、方法或方向"
    reason: "过于理论化，而且没有可用实验数据"
rejected_items: []
open_questions: []
inherited_from_previous: []
reset_from_previous: []
```

保存拒绝理由，而不只是论文或方向 ID。理由适用于新候选时也要执行，不能只隐藏被拒项后再推荐近似重复项。

## 检索前诊断不满意原因

| 反馈 | 保留 | 重置 | 下一行动 |
|---|---|---|---|
| 接受方向，但拒绝论文 | 方向、硬约束、目标指标 | 论文排序与查询表达 | 在该方向内重新检索 |
| 认可论文，但拒绝方向 | 稳定资源约束和明确拒绝理由 | 方向得分与旧锚定 | 重构问题，创建新方向分支，再检索 |
| 质疑引文元数据 | 选题与方向约束 | 被质疑引文的状态 | 先审计和替换元数据，再考虑方向 |
| 新增资源、数据或时间约束 | 仍适用的偏好 | 被新约束推翻的证据与方向 | 修订简报，再选择局部或完整重检索 |
| 同时拒绝论文和方向 | 用户已确认的稳定约束 | 当前分支、排序和方向集 | 从第一轮创建新分支 |
| 要求完全重置 | 安全/合规规则及用户批准的稳定约束 | 语义偏好、负面反馈、得分和查询 | 启动独立分支 |

用户只说“不满意”时，先问一个简短诊断问题，不要盲目发起第三轮检索。

## 控制历史影响

默认使用以下查询/候选预算：

| 反馈状态 | 利用已确认信息 | 探索新空间 |
|---|---:|---:|
| 明确正向反馈 | 70% | 30% |
| 混合或中性反馈 | 50% | 50% |
| 接受方向、拒绝论文 | 30% | 70% |
| 拒绝方向、创建新分支 | 20% | 80% |
| 完全重置 | 0% | 100% |

这些是分配默认值，不是概率。允许用户要求更保守或更发散的检索。

## 生成准确反馈差异

第一轮到第二轮的每次转换都必须通过以下准确顶层字段暴露。不得改名、省略字段，也不得把额外转换状态藏在对象之外：

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

`to_brief_version` 必须大于 `from_brief_version`。每类列表使用闭合 schema：继承项恰含 `{object_id,value}`；拒绝项恰含 `{object_id,value,reason}`；重置项恰含 `{object_id,previous_value,reason}`；新增项恰含 `{object_id,value,reason}`。拒绝未知字段，所有值均为非空文本。继承约束与偏好放入 `inherited`，被拒对象放入 `rejected`，明确丢弃的假设或状态放入 `reset`，新约束或证据需求放入 `added`。硬排除由用户措辞决定时，保留用户原话；不要把含糊不满强化为硬约束。

`allocation.exploit` 和 `allocation.explore` 必须为总和恰好 100 的整数，表示第二轮查询与候选预算百分比，不是概率、置信度或证据权重。

## 把实质反馈落实到查询

拒绝理由、新约束或重置会改变纳入词、排除词、来源边界、时间边界、语言边界、预期证据角色、查询用途、查询文本，或查询的增删时，该反馈为实质反馈。

每项实质拒绝、新约束或重置至少对应一条 `query_changes`。每条查询变更都必须含非空 `cause_refs`，并且只能使用指向 `feedback_delta.rejected`、`feedback_delta.reset` 或 `feedback_delta.added` 的精确零基路径，例如 `feedback_delta.rejected[0]`；绝不能指向 `inherited`。

每个路径必须解析到现有条目，每项实质拒绝、重置和新增内容至少出现在一条查询变更的 `cause_refs` 中。一项反馈可影响多个查询，一项查询变更也可引用多个反馈。无法解析、指向继承项或存在未覆盖实质内容时均无效。

说明因果理由。修改查询时，保持一个稳定 `query_id`，且该 ID 在两轮中各恰好出现一次；`before` 只能等于第一轮对应的 `query_text`，`after` 只能等于第二轮对应的 `query_text`。新增查询的 ID 在第一轮不存在、第二轮恰好出现一次，且 `after` 等于其文本；删除查询反之，且 `before` 等于其文本。不得用 ID、用途、预期角色、术语或其他字段代替 `query_text`。

新增查询只允许 `before` 为空，删除查询只允许 `after` 为空，修改查询必须给出两个非空且不同的值。两个值不能同时为空。每个非空 `after` 必须与修订后的第二轮查询文本一致。如果现有查询已经执行某项反馈，无需修改，应把该影响明确标为非实质并说明原因，不能制造虚假查询变更。

实质反馈没有可追踪查询变更时视为无效。在修复差异或明确说明其为非实质反馈前，不进入第二轮选择。

## 检索前展示变更日志

始终展示：

```text
继承：已确认的约束和偏好
拒绝：被排除的对象及理由
重置：不再生效的得分、查询、假设或分支
新增：新约束或证据需求
检索分配：利用 / 探索
```

允许用户纠正摘要。方向被拒后，依据新简报重新计算方向得分，绝不能继承旧排序。

## 遵循状态流

使用以下逻辑流：

```text
CLARIFYING
  -> ROUND1_SEARCHING
  -> WAITING_FOR_FEEDBACK
  -> ROUND2_SEARCHING / DIRECTION_REFRAMING / CITATION_AUDIT / FULL_RESET
  -> WAITING_FOR_DIRECTION_CONFIRMATION
  -> ROUTE_PLANNING（仅在用户确认后）
```

把一个两轮序列视为一次校准周期。用户仍不满意时，根据诊断启动下一周期，不要向旧查询无限追加论文。

## 保留不确定性

- 说明哪些反馈改变了新检索。
- 弱负面反馈先标为软偏好，除非用户明确设为硬排除。
- 新证据实质改变被拒项状态前，不重新引入；发生例外时说明理由。
- 新方向仍继承旧语义约束时，不得宣称它完全独立。
- 不可用检索和未核验引文保持为可见缺口，不得静默删除。
