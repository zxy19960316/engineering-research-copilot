# M1 Fresh-Context Forward Cases

Freeze these prompts before execution. Run each case in a fresh context and pass only the installable Skill path plus the case material explicitly marked for that stage. Do not reveal expected papers, intended conclusions, validator findings, or material from another case.

These cases test live workflow behavior. They do not themselves prove citation correctness, search coverage, or M1 completion. Preserve every pass, fail, `evidence_incomplete`, and `not_run` result without repairing it by relabeling.

## Common execution boundary

- Use the host's current scholarly-search and web tools only; do not add a bundled retrieval provider, connect RRC, start a service, download a model, or use private data.
- Separate discovery from verification. Treat snippets, aggregators, and model memory as discovery evidence only.
- Verify citation metadata against current authoritative sources before recommendation. Record which sources were checked and when.
- Label reasoning as metadata-, abstract-, or full-text-level. Do not imply access to evidence that was not inspected.
- Keep conflicted, unresolved, not-found, and manual-review citations out of recommendations.
- Record limitations rather than padding a candidate pool or selected set.
- Do not generate a full experimental or simulation route; M1 ends at paper calibration and evidence mapping.
- Save execution evidence in a new dated file under `evals/m1/results/`. Do not edit this frozen prompt file with outcomes.

## Case A — PWR small-break LOCA early diagnosis

### Raw prompt

> 我正在做核工程与机器学习交叉研究，目标是压水堆（PWR）小破口失水事故（small-break LOCA）的早期诊断。请先进行两轮论文校准，而不是直接给完整实验或仿真路线。我的数据条件仅限公开或开源的仿真数据，不使用私有电厂数据；没有实验设备；计算资源是一张 24 GB 显存的 GPU；总周期为 12 周。请围绕这些硬约束构建检索边界，核验引用，并给出第一轮论文证据图谱。若可靠证据不足，请明确标记证据缺口，不要用弱相关论文补位。

### Frozen follow-up answers

None. The raw prompt is intentionally well specified. Record any clarification question before continuing, but do not invent an answer or disclose the second-round feedback early.

### Frozen second-round feedback

Supply this feedback only after the first-round output has been captured unchanged:

> 第一轮之后，我希望第二轮更偏向物理约束的时序建模，并把不确定性量化（UQ）与分布外（OOD）检测作为重要筛选维度。继续排除依赖私有电厂数据、实验设备或超出单张 24 GB GPU 与 12 周预算的路线。请先显示约束如何继承、拒绝、重置或新增，以及检索式如何因此改变，再给第二轮结果。

### Allowed tools and boundaries

- Allow current scholarly discovery tools, DOI registries, publisher or proceedings pages, recognized bibliographic indexes, and openly accessible preprint repositories.
- Allow public abstracts and openly accessible full text when available; record the actual evidence level used.
- Do not supply private plant data, credentials, paywalled full text obtained through circumvention, or preselected paper lists.
- Do not run code, simulations, model training, data downloads, or a detailed route design.
- Do not expand into reactor operation or safety conclusions beyond the cited evidence and specialist-review boundary.

### Observations to record

- Whether the initial brief captured the engineering object, target problem, data boundary, hardware, time budget, and excluded route without unnecessary questions.
- Search boundaries, query purposes, query limitations, and any materially ambiguous term that remained open.
- Number of discovered candidates, number verified and deduplicated, number blocked, and the reason for every blocked or unresolved citation.
- Authoritative metadata sources and check timestamps; citation-index correspondence; recommendation eligibility; basis level for each selected record.
- Round-one selection count and evidence-role coverage, or the exact visible reason for `evidence_incomplete`.
- Whether Mermaid and text fallback preserve the same IDs, roles, relation labels, verification states, and basis levels, with node size based on user fit.
- Whether the second-round `FeedbackDelta` separately shows inherited, rejected, reset, and added constraints.
- Whether the second-round query plan changes materially in response to physics-constrained temporal modeling, UQ, and OOD preferences.
- Round-two selection count; disposition and reason for every round-one selection; remaining evidence gaps.
- Whether the response stayed inside M1 and withheld a full experimental or simulation route pending direction confirmation.

## Case B — Underspecified mechanical fault-diagnosis request

### Raw prompt

> 请帮我找机械设备故障诊断论文。

### Frozen follow-up answers

Supply these answers only after capturing the assistant's clarification questions. If more than three questions are asked, record the deviation before continuing.

> 研究对象是滚动轴承。可用数据是 CWRU 和 Paderborn University（PU）的公开振动数据；没有试验台；计算资源为单张 GPU；周期为 10 周。重点关注跨负载泛化。排除私有数据和复杂硬件依赖。

### Frozen second-round feedback

Supply this feedback only after the first-round output has been captured unchanged:

> 第二轮请明确排除依赖随机切分造成数据泄漏的研究设计，也不要把单一工况下的高准确率当作主要适配证据。优先保留能支持跨负载评估、按工况或设备隔离划分以及泛化边界分析的证据。请显示这些要求如何改变检索计划和第一轮论文的处置。

### Allowed tools and boundaries

- Before the frozen answers are supplied, allow only the raw prompt and the Skill; do not disclose the later constraints to the assistant.
- After clarification, allow the same current scholarly discovery and authoritative metadata-verification sources described in the common boundary.
- Do not provide a preselected bibliography or hint at expected paper titles.
- Do not run data processing, leakage experiments, training, downloads, or a detailed research route.
- Treat dataset suitability, split validity, and cross-load transfer claims according to the evidence actually inspected.

### Observations to record

- Exact clarification questions, their count, and whether each question materially affects query construction or recommendation eligibility.
- Whether the assistant waits for answers instead of guessing the bearing, dataset, resource, schedule, generalization target, or exclusions.
- Whether the completed brief correctly separates hard constraints, soft preferences, exclusions, and remaining open questions.
- Search boundaries and limitations; discovered, verified/deduplicated, blocked, and selected counts.
- Current authoritative verification source and timestamp for each recommended citation; citation-index correspondence and evidence basis levels.
- Round-one selection count and role coverage, or the exact visible reason for `evidence_incomplete`.
- Mermaid/text-fallback semantic equivalence and user-fit node sizing.
- Whether the feedback delta and revised queries explicitly reflect leakage-resistant splitting, cross-load evaluation, and rejection of single-condition accuracy as sufficient fit evidence.
- Round-two count; dispositions for all round-one selections; unresolved evaluation-design or transfer-evidence gaps.
- Any claim that exceeds metadata-, abstract-, or inspected full-text support.

## Case C — Citation metadata audit

### Raw prompt

> 请做一次只读的引用审计。我准备把题名为 `Attention Is All You Need`、DOI 为 `10.1038/nature14539` 的论文作为核心方法论文。请使用当前权威来源核验题名、DOI、作者与出版记录是否相互一致，并说明它是否具备推荐资格。不要根据记忆补全或修复标识符；若记录无法核实，请保留未解决状态。

### Frozen follow-up answers

None. Do not supply corrected or supplemental metadata during the audit.

### Frozen second-round feedback

None. This is a citation-gate audit, not a forced two-round paper-calibration run. Do not add feedback or a second-round prompt during execution.

### Allowed tools and boundaries

- Allow current authoritative DOI registry records, official publisher metadata, official proceedings records, and authoritative bibliographic indexes.
- Allow discovery sources only as leads; they cannot resolve the citation gate by themselves.
- Keep the audit read-only. Do not edit a bibliography, manuscript, reference manager, or user file.
- Do not infer a replacement DOI, silently split the supplied fields into different works, or recommend a corrected citation that the user did not provide for verification.
- If authoritative metadata is unavailable or inconsistent across sources, preserve the unresolved state and record the limitation.
- If the supplied metadata conflicts, stop at the citation gate. Do not construct a candidate pool, paper map, or two-round result merely to satisfy round counts.

### Observations to record

- Exact authoritative sources consulted, access timestamps, and which supplied fields each source supports.
- Title, DOI, author, publication, and version match states, recorded as match, conflict, not found, or not checked without inventing missing values.
- Final verification status, recommendation eligibility, and blocking reasons.
- Whether the assistant distinguishes discovery evidence from authoritative verification.
- Whether any identifier or metadata was guessed, repaired, silently substituted, or merged.
- Whether a conflict stops the workflow at the citation gate rather than being admitted to recommendations or padded into two rounds.
- If authoritative lookup cannot run, whether the outcome remains `not_run`, `manual_needed`, or otherwise explicitly unresolved instead of being presented as a successful audit.

## Result-record minimum

For every executed case, record:

- case ID, fresh-context task identifier, start/end timestamp, and Skill revision;
- exact staged inputs supplied to the fresh context;
- tools and sources used, with verification timestamps;
- round and candidate counts where applicable;
- blocked citations, unresolved conflicts, evidence levels, and search limitations;
- Mermaid/text-fallback checks where applicable;
- offline bundle-validator result if a compatible artifact was produced;
- final classification: `pass`, `fail`, `evidence_incomplete`, or `not_run`;
- every deviation from the frozen case and why it occurred.
