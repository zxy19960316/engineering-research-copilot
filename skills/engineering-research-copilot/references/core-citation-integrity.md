# 引文完整性

发现、推荐、引用、映射外部文献，或用文献论证研究方向时，均应用本文件。

## 目录

- 分开发现候选与已核验记录
- 使用当前权威来源核验
- 规范化但不臆造
- 比较元数据
- 分配唯一核验状态
- 判断推荐资格
- 应用预印本契约
- 确定性去重
- 处理版本关系
- 生成已核验论文记录
- 说明真实证据局限
- 执行硬门槛

## 分开发现候选与已核验记录

先创建发现记录。在权威来源完成检查前，其状态必须保持为 `unverified_candidate`。

发现输出使用以下结构：

```yaml
discovery_candidate:
  candidate_id: ""
  discovery_state: "unverified_candidate"
  supplied_title: ""
  supplied_authors: []
  supplied_identifier: null
  discovery_source_type: "search_snippet|aggregator|ordinary_web|user_supplied|model_memory"
  discovery_source: ""
```

把用户提供的字符串保留为未核验观察。不得修补标识符、补全作者列表，也不得把可能的题名转成书目事实。

搜索摘要、聚合器匹配、普通网页、用户陈述或模型记忆都不能设置已核验状态。发现记录不能直接进入推荐列表或论文图；只有完成下述核验对象后，才能提升为 `VerifiedPaperRecord`。

## 使用当前权威来源核验

按适用情况依次检查：

1. 用户提供 DOI 时，查询 DOI 注册机构记录。
2. 用户提供仓库标识符时，查询官方仓库记录和准确版本。
3. 生物医学交叉领域提供 PMID 时，查询 PubMed 官方记录。
4. 用出版商落地页交叉核对题名、作者、出版物、作品类型、日期、勘误和版本关系。
5. 结构化聚合器只用于发现候选或消歧；存在权威注册机构或官方仓库时，不能把聚合器作为唯一真相来源。

每项真实推荐都必须在当前校准轮次执行权威查询。记录所有尝试过的权威来源，包括冲突、不可访问和未找到结果。来源无法检查时记录局限，不得改用模型记忆或旧搜索摘要填补。

## 规范化但不臆造

- 从输入 DOI 中移除 `https://doi.org/`、`http://dx.doi.org/` 和 `doi:`。
- 去掉首尾空白和尾部引文标点，并将 DOI 转为小写。
- 完成上述规范化后，逐字保留用户提供的 DOI 主体。
- 不得改变 DOI 主体、推断缺失字符或根据题名相似度创建标识符。
- 不得把 arXiv ID、PMID、ISBN、报告编号或出版商 URL 当作 DOI。
- 官方替代标识符只按其所属机构规则规范化，并保留标识符类型和版本。
- 没有官方替代标识符时，将 `alternate_id` 设为 `null`；否则只能使用含 `authority` 与 `value` 两个非空字段的对象。拒绝裸字符串、空值、缺失字段和额外字段。
- 在线优先日期和卷期出版日期同时存在时分别保留。

## 比较元数据

至少比较：

- 完整题名；
- 有序作者列表；
- 在线日期和卷期日期；
- 期刊、会议、仓库或其他出版物；
- 出版类型或作品类型；
- 用户提供与权威来源中的规范化 DOI、官方替代标识符和规范标识符；
- 可获得时的勘误、撤稿和版本关系。

如果标识符能够解析，但 DOI、题名或作者身份存在实质不一致，将其标为 `conflicted`。两个被视为同一候选的记录含不同规范化 DOI 时，这是决定性的标识冲突；不得选择看似可信的一个，也不得用弱键覆盖冲突。

没有更强匹配键时，只能用规范化题名加第一作者寻找或复核候选。必须得到权威确认后，才能把这对值视为同一作品。不得仅靠模糊匹配分配 DOI 或替代标识符。

## 分配唯一核验状态

只能从以下闭合集合中选择一个状态：

| 状态 | 含义 | 推荐资格 |
|---|---|---|
| `verified_primary` | 注册机构或官方仓库与落地页元数据一致 | 没有阻断理由时可推荐 |
| `verified_registry` | 注册机构元数据一致，但当前无法检查出版商落地页 | 披露无法交叉核对后可推荐 |
| `verified_preprint` | 官方预印本 ID、准确版本、题名和作者一致 | 按预印本契约有条件推荐 |
| `partial` | 记录存在，但重要作者、日期、出版物或版本信息不完整 | 只能作为补充背景 |
| `conflicted` | 标识符解析到实质不同的元数据，或权威来源相互冲突 | 阻断 |
| `not_found` | 在声明的检索边界内没有找到权威记录 | 阻断 |
| `manual_needed` | 仍有多个可能候选，或身份/版本问题未解决 | 等待人工确认并阻断 |

真实记录中不得引入其他核验状态。把不可用检查记录到 `checked_sources` 和局限中；不得把不完整核验重新标成成功。

核验状态与推荐资格必须分开。`verified_primary`、`verified_registry` 或 `verified_preprint` 只说明当前来源和身份闭合；仍可能因范围、角色、迁移、安全或预印本用途限制而设置 `recommendation_eligible: false`。此时保留核验状态，至少填写一个具体 `blocking_reasons`，并把记录排除在 `selected_ids` 和论文图论文节点之外。该记录仍可计入去重后的 15–20 篇已核验候选目标。

不得为了表达“不适合推荐”而把已核验记录降为 `partial`。`partial` 只表示当前核验或身份不完整。`partial`、`conflicted`、`not_found` 和 `manual_needed` 一律不能计入已核验候选目标。

## 判断推荐资格

只有同时满足以下条件，才设置 `recommendation_eligible: true`：

- `verification.status` 为 `verified_primary` 或 `verified_registry`，或者按预印本契约为 `verified_preprint`；
- 题名和作者核对均没有 `conflict`；
- 作品类型和版本身份足以支持预期用途；
- `blocking_reasons` 为空；
- 当前轮次真实执行了权威查询，而不是只依赖离线结构、发现元数据或模型记忆。

`partial` 必须不可推荐，只能作为明确标注的补充背景，并说明缺失核验。`conflicted`、`not_found` 和 `manual_needed` 必须不可推荐，并从推荐列表、所选 ID、论文图节点、方向支持和安全结论中排除。

已核验但不可推荐的记录必须有非空阻断理由，至少一项当前有效来源给出匹配且没有冲突或未找到结果，题名与作者身份已经解决，并且 `version_relation` 已闭合且不是 `unknown`。空理由、缺少当前来源或身份仍开放均属无效。不可推荐记录绝不能被选中。

## 应用预印本契约

- `verified_preprint` 只能用于方法或探索证据。
- 说明准确的已核验版本，并披露其可能尚未经过同行评审。
- 只有当它不是主方向或安全相关结论的唯一支持时，才可设置为可推荐。
- 只有权威证据确认关系后，才用 `preprint_of` 连接期刊版本。
- 内容或关系不清时，预印本与期刊记录保持分开。
- 同一主张有适用的已核验期刊记录时，优先使用期刊记录。

对 M2.1.1 包，从嵌入的 M1 候选台账执行本契约。`provisional_main` 至少需要一项可推荐的 `verified_primary` 或 `verified_registry` 支持，否则返回 `provisional_main_requires_non_preprint_support`。带证据且通过的安全相关硬门槛也至少需要一项非预印本支持，否则返回 `safety_gate_requires_non_preprint_support`。不可推荐或已阻断记录均不能计入，也不能用调用方声明的来源类别替代 M1 字段。

## 确定性去重

严格按以下顺序使用键；更强键已经产生匹配或不匹配后，不得回退：

1. 两条记录都有 DOI 时，比较规范化 DOI。相同值是可能重复，仍需核对元数据和版本；不同值是决定性不匹配，立即停止，不得再用替代标识符或题名加第一作者合并。
2. 至少一条记录没有 DOI 时，才比较官方替代标识符 `(authority, value)`。先验证每个非空 `alternate_id` 都是闭合的两字段对象。两条记录都有替代标识符时，相同键是可能重复；不同键（包括不同 `authority`）是决定性不匹配，不得回退到题名加第一作者。
3. 至少一条记录没有 DOI，并且至少一条也没有官方替代标识符时，才比较规范化题名加规范化第一作者，以触发候选复核。

第三个键只是复核触发器，不是身份事实。没有当前权威来源确认 `same_work` 时不得自动合并。后来找到更强标识符后，从 DOI 步骤重新开始。

相同 DOI 或官方替代标识符对应的题名、作者、作品类型或版本元数据冲突时，不得合并；按情况设为 `conflicted` 或 `manual_needed`，保留所有来源观察，并阻断推荐资格。

只有决定性身份字段全部一致后，才保留更完整的权威元数据。合并真正重复项时保留全部已查来源和标识符别名，不得静默合并冲突字段。

比较候选池内每一对记录，包括未选记录。兼容记录使用不同 `candidate_id` 时，拒绝为 `duplicate_candidate_identity`；相同 DOI 或替代标识身份却有不兼容题名、作者、出版类型或版本关系时，拒绝为 `candidate_identity_conflict`；题名加第一作者匹配但缺少决定性标识符时，标为 `candidate_identity_manual_review`，不得自动合并，相关记录若被选中则阻断。

跨轮次保持同一 `candidate_id` 指向同一作品。DOI、替代标识符或身份元数据发生不兼容变化时，拒绝为 `stable_candidate_identity_changed`。只有两轮具有相同规范化替代标识符时，才允许新增 DOI；否则报告 `stable_candidate_identity_unresolved`，不能根据题名和第一作者推断连续性。

## 处理版本关系

`version_relation` 只能取 `same_work`、`preprint_of`、`distinct` 或 `unknown`。

- 普通单篇论文中，发现候选与当前权威记录一致，且没有单独预印本、版本、勘误或其他版本关系时，使用 `same_work`；不能仅因只识别到一个版本而用 `unknown`。
- `same_work` 只有在权威元数据和作品类型一致后才能合并重复观察。
- `preprint_of` 保留独立的预印本与正式出版记录并建立关系，不能把两个标识符互换。
- `distinct` 即使题名相似也保留独立记录。
- `unknown` 必须对应真实未解决的身份或版本歧义；不要合并，并只在歧义影响身份或推荐资格时使用 `manual_needed`。
- 作品类型冲突或预印本—正式发表关系未解决时，记录保持分开且阻断，直至权威来源或人工确认解决。

## 生成已核验论文记录

核验对象及其全部字段必须使用以下结构：

```yaml
verification:
  status: "verified_primary"
  checked_sources:
    - source_type: "doi_registry"
      canonical_record: ""
      checked_at: "ISO-8601"
      result: "match"
  title_match: "exact|normalized|conflict|not_checked"
  author_match: "exact|compatible|conflict|not_checked"
  version_relation: "same_work|preprint_of|distinct|unknown"
  recommendation_eligible: true
  blocking_reasons: []
```

`source_type` 只能取 `doi_registry`、`official_repository`、`pubmed` 和 `publisher_landing`；`result` 只能取 `match`、`conflict`、`not_found` 和 `unavailable`。每次检查都记录带时区的 ISO-8601 `checked_at` 和可解析的 `canonical_record`；未实际检查时不得虚构二者。

外层 `VerifiedPaperRecord` 使用以下结构。缺失标识符保持为 null；所有书目值只能来自已检查元数据：

```yaml
verified_paper_record:
  paper_id: ""
  title: ""
  authors: []
  year_online: null
  year_issue: null
  venue: ""
  publication_type: ""
  doi: null
  canonical_url: ""
  alternate_id: null
  verification: {}
  evidence_role: ""
  supports: ""
  does_not_support: ""
  basis_level: "metadata_level|abstract_level|fulltext_level"
```

没有替代标识符时，`alternate_id` 必须恰为 `null`；存在时，只能换成前述含 `authority` 与 `value` 的对象，不能使用裸字符串或残缺对象。

校准候选的摘要字段必须原样镜像 `verification.status` 和 `verification.recommendation_eligible`；摘要与嵌套对象不一致时拒绝候选。

向用户展示已核验的准确题名、作者、年份、出版物、可点击规范记录、核验状态、核验时间、证据角色、支持内容、局限和推理层级。

## 说明真实证据局限

离线 schema、fixture 和结构验证只能检查契约：必填字段、闭合状态、去重行为和资格门槛。它们不能证明 DOI 或其他引文标识符真实存在，不能证明元数据正确，也不能证明实时学术核验成功。

每项真实推荐都需要当前权威查询及记录来源。无法完成查询时，记录保持部分或阻断，并报告 `evidence_incomplete`；不得把离线有效对象提升为真实已核验引文。

## 执行硬门槛

- DOI、作者、题名、发表状态、URL 和标识符的虚构数量必须为零。
- 核验来源缺失、不是当前轮次、内部不一致或只基于发现来源的记录必须阻断推荐。
- 没有明确检索边界时，不得宣称创新性、优先权或不存在相关研究。
- 不得用被引次数判断真伪、质量或适用性。
- 明确标注元数据级、摘要级和全文级推理。
- 证据为部分、仅预印本、仅摘要或仅迁移时，降低结论强度。
