# 静态论文证据图

当已获得经过核验和去重的论文后，应用本文件。证据图帮助用户在阅读全文前快速定位，不得把它表现成交互式知识库或全文阅读替代品。

## 目录

- 按轮次选择合格论文
- 构建证据图
- 一致编码含义
- 标记证据层级
- 保持注释精简
- 提供稳健降级显示
- 使用规定数据结构
- 保证 Mermaid 与文本回退等价
- 接收对话反馈

## 按轮次选择合格论文

第一轮最多选择八篇可推荐论文，并固定分配为：

- 三篇 `direct_problem`；
- 两篇 `method`；
- 两篇 `transfer_bridge`；
- 一篇 `counter_limitation`。

只有在声明的证据层级得到支持且可推荐的已核验记录，才能占用角色位置。不得用较弱、已阻断、部分核验或仅发现的论文补位，也不得从其他角色借一篇合格论文制造完整数量。每个空缺角色及数量写入 `evidence_gaps`，将轮次结果设为 `evidence_incomplete`，位置保持为空，并按校准契约的非成功路径停止。

第二轮在可靠证据足够时默认展示五到六篇。默认情况下，包含它的第二轮包可以省略 `round_two_request`，或设置 `round_two_request.explicit_user_request: false` 且 `requested_count` 等于所选 ID 数量。

只有第二轮包同时记录 `round_two_request.explicit_user_request: true` 且 `round_two_request.requested_count` 等于所选 ID 数量时，才允许展示七到十篇。缺少授权、授权为假、数量不匹配或超过十篇均属无效。第一轮包不得包含 `round_two_request`。不要推断授权，也不要用弱证据填充第二轮。

## 构建证据图

1. 把当前研究问题或简报放在中心。
2. 建立二到四个方向、问题、方法或迁移簇。
3. 绘制论文节点前，先应用相应轮次选择规则。
4. 在整个校准周期保留每个候选的稳定 ID，并在图下方表格给出准确引文。
5. 每篇论文最多使用一到两条解释性边。

## 一致编码含义

- 论文节点大小表示相对当前 `ResearchBrief` 的匹配度，不能表示被引次数或一般声望。
- 论文节点颜色表示证据角色：直接问题、方法、迁移/桥接或反证/局限。
- 用边框或显式标记区分 `verified_primary`、`verified_registry` 和 `verified_preprint`；部分或阻断记录不得进入所选论文节点。
- 边关系只能使用 `same_problem`、`shared_method`、`transfer_bridge`、`claim_support`、`claim_tension` 或 `same_data_or_benchmark`。
- 线宽表示当前图中的关系强度。
- 虚线表示推断性迁移或证据不完整。
- 每条结论关系都用有范围的具体主张标记，不能笼统声称两篇论文整体一致。

## 标记证据层级

每条注释和每条边设置一个 `basis_level`：

- `metadata_level`：只依据书目元数据和关键词；
- `abstract_level`：依据已核验摘要；
- `fulltext_level`：依据已检查全文且有来源锚点。

不得把摘要级比较标为全文结论检查。全文不可获得时，在图例和论文索引中说明局限。

## 保持注释精简

每篇论文只显示：

- 短题名或紧凑标签；
- 年份；
- 一行相关性说明；
- 必要时的核验/证据层级标记。

图下方列出准确题名、有序作者、年份、出版物、DOI 或官方 ID、核验状态和一行角色说明。详细摘要不要放入图中。

## 提供稳健降级显示

1. 默认在 Markdown 中直接输出 Mermaid。
2. 不支持 Mermaid 时，输出具有相同论文标签、角色和关系的分组文本树。
3. 只有用户明确要求文件或参赛制品时，才导出静态 SVG。
4. 不创建交互式 HTML、点击处理器、图服务或新的网络依赖。

## 使用规定数据结构

每轮证据图都包含以下全部字段。`node_size_basis` 必须恰为 `user_fit`，不得省略，也不得改用被引次数、出版物声望或一般热度。

```yaml
paper_map:
  round: 1
  node_size_basis: "user_fit"
  legend:
    evidence_roles: ["direct_problem", "method", "transfer_bridge", "counter_limitation"]
    basis_levels: ["metadata_level", "abstract_level", "fulltext_level"]
  nodes:
    - id: "P1"
      node_type: "paper"
      fit_score: 0.86
      evidence_role: "transfer_bridge"
      verification_status: "verified_primary"
      basis_level: "abstract_level"
      short_note: "来自相似数据条件的方法迁移证据"
    - id: "D2"
      node_type: "cluster"
      basis_level: "abstract_level"
      short_note: "公开仿真证据簇"
  edges:
    - source: "P1"
      target: "D2"
      relation: "transfer_bridge"
      strength: "medium"
      confidence: "medium"
      basis_level: "abstract_level"
      note: "机制相似，但边界条件仍需检验"
  text_fallback:
    - entry_type: "node"
      id: "P1"
      node_type: "paper"
      evidence_role: "transfer_bridge"
      verification_status: "verified_primary"
      basis_level: "abstract_level"
      text: "P1: 来自相似数据条件的方法迁移证据"
    - entry_type: "node"
      id: "D2"
      node_type: "cluster"
      basis_level: "abstract_level"
      text: "D2: 公开仿真证据簇"
    - entry_type: "edge"
      source: "P1"
      target: "D2"
      relation: "transfer_bridge"
      basis_level: "abstract_level"
      text: "P1 --transfer_bridge--> D2: 机制相似，但边界条件仍需检验"
  mermaid: |-
    flowchart TD
      n0["id=P1; type=paper; basis=abstract_level; role=transfer_bridge; status=verified_primary; fit=0.86; note=来自相似数据条件的方法迁移证据"]
      n1["id=D2; type=cluster; basis=abstract_level; note=公开仿真证据簇"]
      n0 -- "relation=transfer_bridge; basis=abstract_level; strength=medium; confidence=medium; note=机制相似，但边界条件仍需检验" --> n1
```

`paper_map` 的七个字段 `round`、`node_size_basis`、`legend`、`nodes`、`edges`、`text_fallback` 和 `mermaid` 均为闭合字段。`legend.evidence_roles` 和 `legend.basis_levels` 也是闭合列表，必须使用上述准确角色和层级标记。每个所选论文 ID 恰好出现为一个论文节点；未选、阻断、部分核验或未解决引文不得进入论文节点。

每个论文节点必须且只能含 `id`、`node_type`、`fit_score`、`evidence_role`、`verification_status`、`basis_level` 和 `short_note`。`fit_score` 必须是 0 到 1 之间的非布尔数值。每个簇节点必须且只能含 `id`、`node_type`、`basis_level` 和 `short_note`，不能含 `fit_score`、`evidence_role` 或 `verification_status`。每条边必须且只能含 `source`、`target`、`relation`、`strength`、`confidence`、`basis_level` 和 `note`。

## 保证 Mermaid 与文本回退等价

从同一组结构化 `nodes` 和 `edges` 生成 Mermaid 与 `text_fallback`，不得手工维护两套语义版本。

结构化节点和边完成后，从同一对象直接生成两种视图。保持原有顺序，不得排序。把 `nodes` 和 `edges` 作为唯一图事实；两种视图不完全一致时拒绝。节点回退文本严格渲染为 `{id}: {short_note}`，边回退文本严格渲染为 `{source} --{relation}--> {target}: {note}`。对 Mermaid 标签中的反斜线、引号、换行、方括号和竖线进行转义，防止用户文本改变图语法。

Mermaid 与文本回退必须原样保留：

- 每个节点 ID 和边端点；
- 每篇论文的证据角色；
- 每条边的关系标签；
- 每篇论文的核验状态；
- 每个节点和边的证据层级。

每个结构化节点恰好对应一条 `entry_type: node` 回退记录，每条结构化边恰好对应一条 `entry_type: edge` 回退记录。ID、角色、关系、核验状态和证据层级必须与结构记录及可见 Mermaid 标记一致。非论文的简报或簇节点只要出现在一种渲染中，就必须出现在两种渲染中。

ID、端点、角色、关系、核验状态或证据层级不一致时拒绝证据图。边声明的证据层级不得高于支持它的论文。缺失回退、不完整回退或按被引次数确定节点大小均视为无效，不能视为降级成功。

## 接收对话反馈

邀请用户给出简短自然语言反馈，例如：

```text
更聚焦 D2；保留 P1 和 P5；排除依赖私有数据的路线；
优先考虑可执行仿真；增加迁移方法的比例。
```

不要要求用户点击证据图、读完每篇论文或给每个节点打分。通过回滚协议应用反馈，并在再次检索前展示变更摘要。
