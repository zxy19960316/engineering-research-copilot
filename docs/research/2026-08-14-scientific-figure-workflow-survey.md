# 科研绘图能力与离线工作流调研

- 日期：2026-08-14（Asia/Shanghai）
- 状态：只读调研；未改动可安装 Skill，未下载论文 PDF，未复制任何论文图像或第三方数据
- 目标：为 Engineering Research Copilot 的“科研绘图”Skill 集群提供可落地的图种分类、数据契约、统计门槛、来源与许可、离线工作流和验收测试
- 证据边界：本报告给出能力设计依据，不授权读取未提供的数据、执行绘图、安装依赖、联网下载、上传材料或发表

## 1. 结论先行

建议把科研绘图能力设计成“主张—证据—数据—统计—图形—导出—审计”流水线，而不是图片风格库。MVP 应覆盖 11 类证据问题：回归诊断、方法一致性、概率校准、不确定性与区间、分布与估计、ROC/PR/决策曲线、生存/时间事件、敏感性/消融、多变量热图、网络图、场/多物理图。每类都应有：

1. 明确的科学问题和禁止替代项；
2. 最小数据模式与观测单位；
3. 统计前提、计算产物和失败门槛；
4. 静态投稿图；必要时另附自包含的交互 HTML；
5. 可追溯的转换记录、随机种子、软件版本和许可清单；
6. 用合成数据执行的确定性验收测试。

“素材包”不应抓取或收录论文图片。建议只收录经核验的论文身份、图号/图注锚点、图种语义、数据契约、合成测试数据、风格令牌、工作流脚本和上游许可链接。论文图仅作为设计观察的出处；任何复用都应回到原页面检查文章、图、补充材料和第三方内容各自的许可。

推荐以静态图为权威结果，以交互图为可选审阅伴侣。投稿用 SVG/PDF（矢量）或符合期刊要求的 TIFF/PNG；交互图不得依赖 CDN，并必须能退化到内容等价的静态图。Plotly 可以输出自包含 HTML，但文件通常更大；网络图和大热图可用专门工具交互探索，不能让交互状态成为唯一证据。

## 2. 调研方法与证据层级

### 2.1 发现与核验分离

- 发现：GitHub star、OpenAlex 被引数、搜索排序只用于找到候选，不用于证明图形正确、论文质量或方法适用。
- 身份核验：优先 DOI 落地页、PubMed、arXiv 摘要页、出版社文章页和项目官方仓库。
- 内容核验：优先官方 API/用户指南、出版社可访问 HTML 正文与图注；只看到摘要的来源只支持摘要层结论。
- 许可核验：软件许可取当前仓库的 LICENSE/DESCRIPTION；论文与图像许可取文章页面的 Rights and permissions 或开放许可声明。论文许可不能替代软件许可，软件许可也不能授权复制论文图。

本报告使用以下标签：

| 标签 | 可支持内容 | 不可越界 |
|---|---|---|
| `M` 元数据 | 标题、作者、期刊/仓库、DOI/arXiv ID、版本、许可标识 | 不推断图中结论 |
| `A` 摘要 | 摘要明确陈述的方法、用途和主要限制 | 不把摘要当完整方法或复现实证 |
| `C` 图注/上下文 | 图号、图注中明确的编码、样本、区间、比较对象 | 不推断未写出的统计流程 |
| `F` 全文/官方文档 | API 契约、完整方法说明、导出要求和已公开限制 | 仍需在目标数据上重新验证 |
| `U` 用户材料 | 用户提供的数据、计划、结果或草稿 | 仅在材料范围内陈述，不补造缺失数据 |

### 2.2 质量标准

一个“漂亮的图”不等于一个“有效的证据图”。本报告把以下项目作为更高优先级：观测单位、配对/重复测量、训练与评估拆分、区间含义、分箱和阈值、删失处理、参数独立性、聚类与归一化、布局随机性、场变量单位和共享色标。论文图注用于展示可取或需警惕的表达方式，不作为免检模板。

## 3. 可直接落地的图种分类

### 3.1 MVP 总表

| 图种 | 要回答的证据问题 | 最小数据模式 | MVP 输出 | 必须阻断的误用 |
|---|---|---|---|---|
| 回归与诊断 | 拟合关系是否合理，误差结构、异常点和影响点如何 | `obs_id, y_obs, y_fit, residual`；至少一个 `x`；可选 `weight, leverage, cooks_d, group, split` | 观测-拟合、残差-拟合、Q-Q/尺度位置、杠杆-Cook 四联图；测试集指标 | 只给拟合线或 R²；把训练集拟合当泛化；未说明残差定义 |
| 一致性/BA/一致相关 | 两种方法是否可互换，偏倚和一致性界限多大 | `subject_id, method_a, method_b`；重复测量需 `replicate/time` | Bland–Altman：均值-差值、偏倚、LoA 与区间；可选比例偏倚、CCC 数值 | 用 Pearson 相关替代一致性；忽略重复测量；异方差时仍用原尺度固定 LoA |
| 校准/可靠性 | 概率是否与事件频率一致，错误集中在哪个置信区间 | `obs_id, y_binary, p, split`；可选 `weight, subgroup` | reliability curve、每箱样本量/概率直方图、95% 区间、Brier/ECE 与分箱说明 | 在训练集校准；隐藏空箱/低样本箱；只报 ECE；比较时分箱规则不同 |
| 不确定性/区间 | 估计值有多大不确定性，区间含义是什么 | `estimate, lower, upper, interval_type, level, unit, group` | 点-区间/forest；原始点或后验分布可选；明确 SD/SE/CI/PI/HDI | 把 SD、SE、CI、PI 混用；隐藏多重比较/同时区间；轴截断夸大差异 |
| 分布与估计 | 数据形状、离群、样本量和效应量分别是什么 | `obs_id, value, group`；配对需 `subject_id, condition` | ECDF 或 raincloud/strip + 稳健摘要 + 效应量及区间；配对时连线 | 只画柱状均值；小样本核密度制造形状；未展示 n；伪重复 |
| ROC/PR/决策曲线 | 排序、精确率-召回、概率阈值临床效用分别如何 | `obs_id, y_binary, score_or_probability, split`；DCA 需阈值与效用语义 | ROC、PR（含 prevalence baseline）、阈值表；概率模型可加 DCA/net benefit | 类别极不平衡只看 ROC；阈值用测试集调优；AP 插值口径不清；DCA 无效用假设 |
| 生存/时间事件 | 随时间的事件自由概率、删失和组间差异如何 | `subject_id, duration, event_observed`；可选 `entry, stratum, weight, competing_event` | KM + 95% CI + 删失标记 + risk table；必要时 cumulative incidence/Cox forest | 把删失当事件；未定义时间原点；竞争风险仍用 1-KM；只给 log-rank P |
| 敏感性/消融 | 哪些参数/组件驱动结果，交互和不确定性如何 | 敏感性：`run_id, parameter*, output`；消融：`config, seed_or_fold, metric, split` | Sobol S1/ST + CI、必要时 S2；消融画相对完整模型的配对差值及区间 | 相关输入直接套独立 Sobol；OAT 声称全局敏感性；不同 seed/划分不配对 |
| 热图/多变量 | 高维模式、簇、注释和缺失结构是什么 | 长表 `row_id, col_id, value` + 行列注释；或带名称矩阵 | 颜色条、单位、缺失编码、聚类/排序规则、行列注释；大图可附交互 | 未声明标准化/距离/链接；彩虹色；缺失值当零；按结果手动排序后做显著性叙事 |
| 网络 | 实体和关系结构是什么，哪些视觉通道承载数据 | 节点表 `node_id, type, label, value*`；边表 `source, target, weight, type, directed` | 静态网络 + 图例 + 布局算法/seed；大图附过滤后的自包含交互版本 | 把空间距离当量值；hairball；边暗示因果；隐藏过滤和孤立节点 |
| 场/多物理 | 空间/时间场、流向、界面、误差和守恒是否一致 | `x,y[,z],time, field/component, value, unit`；可选 `mesh_id, boundary, reference, ensemble` | 等值/填色、矢量/流线、切片；同量共享尺度；模型-参考-差值；必要时不确定性/守恒残差 | 不等比例坐标；插值伪影；流线种子未说明；3D 遮挡；比较图色标不一致 |

### 3.2 图种卡与来源锚点

#### A. 回归与模型诊断

数据预检：确认观测单位、测试集、模型族、残差定义、是否有权重/层级/重复测量。OLS 的正态性和同方差诊断不能机械迁移到二项、计数或生存模型；诊断应采用该模型对应的残差和影响度量。

推荐流程：

1. 先画测试集观测值对预测值，给等值线，不用拟合线掩盖系统偏差；
2. 画残差对拟合值并给平滑趋势；
3. 对需要正态误差推断的模型给 Q-Q 与尺度位置图；
4. 画杠杆/Cook 距离，保留观测 ID 的可追踪性；
5. 分组、时间或空间数据再画残差对组/时间/坐标，不把结构性误差平均掉。

官方实现锚点：statsmodels 的 [`plot_regress_exog`](https://www.statsmodels.org/stable/generated/statsmodels.graphics.regressionplots.plot_regress_exog.html) 和 [`influence_plot`](https://www.statsmodels.org/stable/generated/statsmodels.graphics.regressionplots.influence_plot.html)（`F`）。Nature Methods 的 *Simple linear regression*（DOI [`10.1038/nmeth.3627`](https://www.nature.com/articles/nmeth.3627)，Fig. 1–3，`C/F`）展示了回归均值、散布与 regression-to-the-mean 的区别。Nature 文章 [`s41586-024-07354-8`](https://www.nature.com/articles/s41586-024-07354-8) 的 Extended Data Fig. 5–7（`C`）提供了残差-拟合、分组残差、杠杆/Cook 距离的完整图注锚点。arXiv [`2308.05964`](https://arxiv.org/abs/2308.05964)（`M/A`）可作为 residual lineup 的迁移探索来源，不应在未完成目标模型检验前成为强制流程。

#### B. 方法一致性、Bland–Altman 与一致相关

Bland–Altman 回答“差异是否在可接受范围内”，相关系数回答“是否共同变化”，两者不能替代。MVP 计算差值 `A-B` 和均值 `(A+B)/2`，画偏倚和一致性界限（LoA），并明确界限计算、区间、单位、方向和临床/工程可接受界限。异方差明显时，应评估对数/比值尺度或回归型 LoA。重复测量、多个读者或多个设备需要相应的方差模型，不能把所有点当独立。

原始方法身份与摘要：Bland & Altman, *Statistical methods for assessing agreement between two methods of clinical measurement*，PubMed [`PMID 2868172`](https://pubmed.ncbi.nlm.nih.gov/2868172/)（`M/A`）。官方实现：statsmodels [`mean_diff_plot`](https://www.statsmodels.org/stable/generated/statsmodels.graphics.agreement.mean_diff_plot.html)（`F`），但其基础图不能替代重复测量和 LoA 区间的统计扩展。Nature Communications [`s41467-022-32310-3`](https://www.nature.com/articles/s41467-022-32310-3) Fig. 6（`C`）明确画出方法差值对均值、平均差和 ±2 SD，是图注结构示例，不代表 ±2 SD 在所有设计下都足够。

一致相关系数（CCC）可作为数值补充，但必须与置信区间、量程和误差尺度共同解释；不能把一个高 CCC 当成方法可互换的证明。

#### C. 校准与可靠性

Reliability diagram 应把预测概率与同一分箱内的观察频率对应，同时显示箱内样本量或概率分布。至少记录 `n_bins`、分箱策略、空箱处理、区间方法、是否加权、校准与评估数据的拆分。Brier score 同时包含可靠性、分辨率和不可约不确定性，不能把其变化单独解释为“校准更好”。

官方契约：scikit-learn 的[校准用户指南](https://scikit-learn.org/stable/modules/calibration.html)和 [`calibration_curve`](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html)（`F`）说明二分类输入、分箱和空箱返回行为。Guo et al., *On Calibration of Modern Neural Networks*，arXiv [`1706.04599`](https://arxiv.org/abs/1706.04599)（`M/A`）是现代神经网络温度缩放与可靠性图的重要方法锚点。Nature Machine Intelligence [`s42256-024-00976-7`](https://www.nature.com/articles/s42256-024-00976-7) Fig. 3（`C`）同时给校准曲线、每箱直方图和 95% 区间，适合作为表达契约。arXiv [`2207.13770`](https://arxiv.org/abs/2207.13770)（`M/A`）提示分箱数量和策略会改变可靠性图/ECE，应纳入稳健性测试。

#### D. 不确定性与区间

任何误差条必须在图注和图内可辨认地写出：中心量、区间类型、置信/可信水平、样本量、重复层级和计算方法。点-区间图优先于重叠柱状图。后验区间可用 HDI，但需记录后验样本、区间概率和是否为多峰分布；频率学 CI、预测区间和 Bayesian credible/HDI 不可混称。

Nature Methods 的 *Error bars in experimental biology*（DOI [`10.1038/nmeth.2659`](https://www.nature.com/articles/nmeth.2659)，Fig. 1，`C/F`）展示不同误差条的宽度和间距含义。ArviZ [`plot_hdi`](https://python.arviz.org/en/v0.23.4/api/generated/arviz.plot_hdi.html) 与 [`plot_forest`](https://python.arviz.org/en/v0.12.1/api/generated/arviz.plot_forest.html)（`F`）可作为后验区间实现。MVP 默认需要 `interval_type` 与 `level` 字段；缺失时失败退出，不能猜测。

#### E. 分布与估计图

优先同时展示数据、分布和效应量：原始点/ECDF 提供观察层；箱线/稳健摘要提供结构；估计差及区间提供比较层。小样本不应画看似精细的 KDE/violin；核密度带宽必须可追踪。配对数据应保留 subject ID，并画斜率图或配对差。

Nature Methods 的 *Visualizing samples with box plots*（DOI [`10.1038/nmeth.2813`](https://www.nature.com/articles/nmeth.2813)，Fig. 2–4，`C/F`）强调极小样本、偏态和柱状图替代问题。DABEST 的 Nature Methods 论文（DOI [`10.1038/s41592-019-0470-3`](https://www.nature.com/articles/s41592-019-0470-3)，Fig. 1，`C/F`）与[官方教程](https://acclab.github.io/DABEST-python/tutorials/01-basics.html)（`F`）把原始分布、效应量和 BCa 区间组合为 Gardner–Altman/Cumming 图；[两组/配对教程](https://acclab.github.io/DABEST-python/tutorials/02-two_group.html)说明配对斜率图。Nature Communications [`s41467-021-22833-6`](https://www.nature.com/articles/s41467-021-22833-6) 的相关图注（`C`）明确 raincloud 中密度、散点和箱体各自承担的含义。

#### F. ROC、PR 与决策曲线

ROC 衡量不同阈值的 TPR/FPR；PR 更直接反映阳性类别的 precision/recall，尤其要给出数据中的阳性率基线。曲线必须来自未用于阈值选择的评估集；跨折/外部集应保留每折或每站点不确定性。Average precision 的计算方式、插值与阈值数组应采用库的明确定义。

scikit-learn 的 [`roc_curve`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html) 和 [`PrecisionRecallDisplay`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.PrecisionRecallDisplay.html)（`F`）给出二分类输入和非插值 AP 语义。Saito & Rehmsmeier, *The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets*，DOI [`10.1371/journal.pone.0118432`](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432)（`F`）是类别不平衡下 PR 的主要方法来源。npj Digital Medicine [`s41746-025-01529-x`](https://www.nature.com/articles/s41746-025-01529-x) Fig. 3–4（`C`）提供 ROC/PR/阈值共同报告的图注锚点。

决策曲线需要概率风险、阈值概率和“假阳性相对伤害”的含义，并与 treat-all/treat-none 比较。它回答效用，不等于判别或校准。可参考 `dcurves` 的 [Python 包页面](https://pypi.org/project/dcurves/)与 [R 参考手册](https://search.r-project.org/CRAN/refmans/dcurves/html/00Index.html)（`F`）。npj Digital Medicine [`s41746-025-02268-9`](https://www.nature.com/articles/s41746-025-02268-9) Fig. 3（`C`）把 ROC、校准/Brier、PR、decision curve、confusion 和 KM 放在同一评估链中；这是完整性观察，不是质量背书。

#### G. 生存与时间事件

KM 图必须定义时间原点、事件、删失和纳入风险集规则，显示删失标记、置信区间和 risk table。竞争风险下应优先 cumulative incidence，而非把 `1-KM` 直接解释为事件概率。多变量模型可用 Cox forest，但须另查比例风险、非线性和时间变化效应。

lifelines [`KaplanMeierFitter`](https://lifelines.readthedocs.io/en/stable/fitters/univariate/KaplanMeierFitter.html)（`F`）明确 `durations`、`event_observed`、延迟进入和 Greenwood log-log 区间。Nature Methods [`s41592-022-01563-7`](https://www.nature.com/articles/s41592-022-01563-7) Fig. 2–3（`C/F`）展示删失标记，并说明把删失当事件会产生偏差。Nature Communications [`s41467-021-24919-7`](https://www.nature.com/articles/s41467-021-24919-7) 的生存图（`C`）是 risk table、HR 与 log-rank 同时报告的图注锚点；实际使用仍应报告效应量区间而非只看 P 值。

#### H. 全局敏感性与消融

敏感性分析先声明输入分布、范围、相关结构、采样设计、模型失败运行和输出函数。Sobol S1/ST 与二阶项依赖方差分解的前提；输入相关时需要替代方法或明确限制。Morris 适合筛选，不能自动等同于精确归因。

[SALib 官方文档](https://salib.readthedocs.io/en/stable/index.html)（`F`）覆盖 Sobol、Morris、FAST 等流程。npj Digital Medicine [`s41746-022-00632-7`](https://www.nature.com/articles/s41746-022-00632-7) Fig. 3（`C`）展示 S1/ST 柱和二阶矩阵；Nature Communications [`s41467-022-31860-w`](https://www.nature.com/articles/s41467-022-31860-w) Fig. 3（`C`）展示 S1/ST 点和 95% 区间。

消融没有一个可替代实验设计的“标准图包”。MVP 要求所有配置使用相同 seed/fold/测试集，画相对完整模型的配对差值和区间，另给绝对性能作为尺度。arXiv [`1901.08644`](https://arxiv.org/abs/1901.08644)（`M/A`）只作为消融研究的发现入口；任何组件结论都必须回到目标实验设计核验。

#### I. 热图与多变量结构

先固定数据变换（原值、log、z-score、相对量）、缺失值、距离、链接方式、行列筛选和排序。聚类树是这些选择的结果，不是数据的唯一自然分组。颜色条必须写单位/变换，并给缺失值独立颜色。大矩阵应提供搜索、缩放或过滤，但正文静态图必须保留核心模式。

ComplexHeatmap 的[官方书](https://jokergoo.github.io/ComplexHeatmap-reference/book/)和[注释章节](https://jokergoo.github.io/ComplexHeatmap-reference/book/heatmap-annotations.html)（`F`）提供多热图、行列注释和复杂布局。论文 *Complex heatmaps reveal patterns and correlations in multidimensional genomic data*（[Bioinformatics 页面](https://academic.oup.com/bioinformatics/article/32/18/2847/1743594)，Fig. 1，`C/F`）展示并行注释热图和 OncoPrint。Scientific Data 的 Clustergrammer 论文（DOI [`10.1038/sdata.2017.151`](https://www.nature.com/articles/sdata2017151)，Fig. 1–2，`C/F`）明确缩放、平移、过滤、重排、树状图和注释等交互。Scientific Data [`s41597-022-01788-3`](https://www.nature.com/articles/s41597-022-01788-3) Fig. 3（`C`）是把聚合、颜色断点和截断规则写进图注的例子。

#### J. 网络图

先建立节点表和边表，禁止从显示位置反推关系强度。每个视觉通道（节点大小、颜色、形状；边宽、颜色、透明度、箭头）只能对应已定义字段。布局算法和随机种子必须记录；过滤规则、孤立节点和多重边处理必须可审计。若关系来自预测或相关性，边不能写成因果。

NetworkX [drawing 文档](https://networkx.org/documentation/stable/reference/drawing.html)（`F`）明确其绘图是基础能力，并建议复杂可视化导出 GraphML 到 Cytoscape、Gephi 或 Graphviz。Nature Microbiology [`s41564-023-01347-5`](https://www.nature.com/articles/s41564-023-01347-5) Fig. 3（`C`）给出节点形状/颜色/大小、边厚/深浅和验证边的清晰编码，同时正文提醒关系网络存在偏差、需要互补证据。Nature Communications [`s41467-025-67135-3`](https://www.nature.com/articles/s41467-025-67135-3) 的相关图注（`C`）明确节点大小、边颜色和传递约简。Nature Neuroscience [`s41593-025-02154-3`](https://www.nature.com/articles/s41593-025-02154-3) 的网络图注（`C`）明确说明力导向布局中的边长是任意的，可作为强制警示语模板。

#### K. 场图、矢量场与多物理比较

标量场要给坐标、单位、网格/插值、颜色范围和边界；矢量场要给分量、尺度、归一化、采样密度和流线种子；模型比较要使用同一坐标、时刻和色标，并把参考、预测、差值/相对误差并列。三维图必须考虑遮挡，核心定量结论应有切片、投影或剖面作静态证据。多物理结果还应画守恒残差、界面通量或边界条件违背，不只展示视觉平滑的场。

Matplotlib [`contourf`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.contourf.html)、[`streamplot`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.streamplot.html) 和 [`quiver`](https://matplotlib.org/stable/api/quiver_api.html)（`F`）给出网格、形状和流向的 API 契约；PyVista 的[三维流线](https://docs.pyvista.org/examples/01-filter/streamlines.html)、[二维流线](https://docs.pyvista.org/examples/01-filter/streamlines_2d)和[导出 HTML](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.plotter.export_html)（`F`）适合可选三维审阅伴侣。

Nature 的 Pangu-Weather 论文（DOI [`10.1038/s41586-023-06185-3`](https://www.nature.com/articles/s41586-023-06185-3)，Fig. 2–5，`C/F`）提供 RMSE/ACC、多变量场的模型-预报系统-再分析同时间比较、轨迹点和 ensemble spread–skill 的图注锚点。GraphCast 的 Science 论文身份可由 [DeepMind 官方出版页](https://deepmind.google/research/publications/22598/)和 DOI [`10.1126/science.adi2336`](https://doi.org/10.1126/science.adi2336)（`M`）核验；其作者稿注明个人使用/不可再分发，因此本素材包只保存链接和语义，不保存图。Crameri et al., *The misuse of colour in science communication*（DOI [`10.1038/s41467-020-19160-7`](https://www.nature.com/articles/s41467-020-19160-7)，Fig. 1, 3, 5, 6，`C/F`）支持感知均匀、避免彩虹和红绿冲突，并按 sequential/diverging/cyclic 数据选择颜色。

## 4. 可复用实现与许可清单

以下版本状态与仓库流行度在 2026-08-14 检查。许可应在真正打包时锁定到具体版本/commit 再复核；表中 star 只放在后面的“发现信号”部分。

| 组件 | 适用能力 | 当前许可/复用要求 | MVP 建议 |
|---|---|---|---|
| [Matplotlib](https://github.com/matplotlib/matplotlib) | 通用静态图、诊断、场图、矢量导出 | [Matplotlib License](https://github.com/matplotlib/matplotlib/blob/main/LICENSE/LICENSE)，与 PSF 风格兼容；保留许可文本 | Python 静态主后端 |
| [seaborn](https://github.com/mwaskom/seaborn) | 分布、分类、热图的高层语法 | BSD-3-Clause | Python 辅助层，不替代统计契约 |
| [statsmodels](https://github.com/statsmodels/statsmodels) | 回归诊断、均值-差图、统计模型 | BSD-3-Clause | 回归/BA 基础计算；重复测量另做门槛 |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | ROC、PR、校准、学习/验证曲线 | BSD-3-Clause | 分类评估计算权威实现之一 |
| [DABEST-python](https://github.com/ACCLAB/DABEST-python) | 估计图、BCa 区间、配对比较 | 当前仓库 [Apache-2.0](https://github.com/ACCLAB/DABEST-python/blob/master/LICENSE) | 可选 recipe；注意 2019 论文所述旧许可与当前仓库不同 |
| [ArviZ](https://github.com/arviz-devs/arviz) | Bayesian 后验、HDI、forest | Apache-2.0 | Bayesian 数据时加载 |
| [lifelines](https://github.com/CamDavidsonPilon/lifelines) | KM、Cox、删失数据 | MIT | Python 生存 recipe |
| [SALib](https://github.com/SALib/SALib) | Sobol/Morris/FAST | MIT | 全局敏感性 recipe；先验输入设计门槛 |
| [ggplot2](https://github.com/tidyverse/ggplot2) | R 通用静态图 | MIT；[`ggsave`](https://ggplot2.tidyverse.org/reference/ggsave.html) 支持显式尺寸、格式、dpi | R 静态主后端 |
| [patchwork](https://github.com/thomasp85/patchwork) | R 多面板排版 | MIT | R panel assembler |
| [ComplexHeatmap](https://github.com/jokergoo/ComplexHeatmap) | 注释热图、OncoPrint、多热图 | MIT + LICENSE 文件 | R 热图专用后端 |
| [NetworkX](https://github.com/networkx/networkx) | 网络数据、布局、GraphML 导出 | BSD-3-Clause | 数据/布局；复杂交互转专门工具 |
| [Clustergrammer](https://github.com/MaayanLab/clustergrammer) | 交互聚类热图 | MIT | 可选，不进入无依赖静态核心 |
| [Plotly.py](https://github.com/plotly/plotly.py) | 自包含交互 HTML、静态图 | MIT；[`write_html`](https://plotly.com/python/interactive-html-export/) 可内嵌 plotly.js | 交互伴侣；禁止 CDN；静态仍为权威 |
| [Altair](https://github.com/vega/altair) | 声明式统计与交互图 | BSD-3-Clause | 后续备选；MVP 不必双重实现 |
| [PyVista](https://github.com/pyvista/pyvista) | 网格、三维场、流线、HTML | MIT；HTML 依赖 trame | 多物理扩展；依赖不足时回退静态切片 |
| [Cytoscape](https://cytoscape.org/) | 大网络探索与布局 | 各组件许可需按打包范围核验 | 仅导出 GraphML/外部工作流建议，不捆绑桌面程序 |

许可策略：

- MVP 内不打包论文图片、截图、补充材料或出版社 CSS/字体；只保存链接、书目信息和自己的文字化图种卡。
- 合成 fixture 必须由项目自己生成并标注生成规则，不从论文 Source Data 截取。
- 如果复制上游脚本片段或主题文件，记录仓库、commit、路径、许可证和修改；优先调用依赖 API，避免复制代码。
- 开放获取论文也可能含第三方素材；必须检查图注中的 credit line。默认只链接。
- 当前许可证会变化。依赖锁定时重新抓取 LICENSE，生成 `THIRD_PARTY_NOTICES`，不能从论文中的旧许可描述推断当前仓库许可。

## 5. 建议的离线优先 Skill 集群

### 5.1 分工

```text
scientific-figure-orchestrator
├─ figure-intake-and-contract
├─ figure-selector
├─ regression-and-agreement
├─ calibration-and-classification
├─ uncertainty-and-estimation
├─ survival-and-sensitivity
├─ multivariate-and-network
├─ field-and-multiphysics
├─ interactive-companion        (可选)
└─ figure-qa-and-export
```

- `scientific-figure-orchestrator`：只判断就绪度、调度图种卡和汇总产物；不擅自运行。
- `figure-intake-and-contract`：把用户主张、观测单位、数据列、统计设计、目标期刊和授权写成 `figure-spec`。
- `figure-selector`：根据“证据问题”选图，不根据用户说“画得高级”选图；允许返回主图、相邻备选和最小证伪图。
- 专项 recipe：只读取对应数据模式和参考文件，避免一个巨型提示词承载全部统计细节。
- `interactive-companion`：仅在过滤、缩放、追踪 ID 或三维旋转确有价值时加载；输出自包含 HTML 和静态等价物。
- `figure-qa-and-export`：独立于绘图 recipe，执行证据、统计、可读性、无障碍、文件和许可审计。

### 5.2 `figure-spec` 最小字段

```yaml
claim:
  text: "作者希望该图支持的单一主张"
  evidence_level: U
  allowed_strength: descriptive|associational|predictive|causal
data:
  source_ids: []
  content_hashes: []
  unit_of_observation: ""
  columns: []
  units: {}
  pairing_or_hierarchy: null
  missingness: ""
  train_validation_test_split: null
statistics:
  estimand: ""
  center: null
  interval_type: null
  interval_level: null
  multiplicity: null
  assumptions: []
  diagnostics: []
plot:
  archetype: ""
  mappings: {}
  panels: []
  palette_semantics: sequential|diverging|cyclic|categorical
  interaction_needed: false
export:
  target_journal: null
  final_width_mm: 89|183
  max_height_mm: 170
  formats: [svg, png]
  static_is_authoritative: true
execution:
  backend: python|r
  seed: 0
  network_allowed: false
  user_authorized: false
provenance:
  transformations: []
  software_versions: {}
  license_manifest: []
```

若 `user_authorized=false`，只返回图形契约、数据准备清单和拟执行命令摘要，不读取/写回用户文件、不安装包、不运行。若用户授权绘图，则一次运行只选 Python 或 R 后端，避免跨后端产生不可比较的默认统计行为。

### 5.3 可装入素材包的资产

| 资产 | 内容 | 网络/版权策略 |
|---|---|---|
| `catalog/plot-archetypes.yaml` | 图种、证据问题、输入字段、门槛、备选图、来源 URL | 纯元数据，离线可读 |
| `schemas/figure-spec.schema.json` | 上述契约的机器校验 | 自有代码 |
| `references/<plot-type>.md` | 每类图的统计前提、失败模式、图注检查表 | 自有摘要，引用而不复制原文/图片 |
| `templates/caption-fields.yaml` | n、中心量、区间、检验、单位、分箱、删失等必填槽 | 自有模板 |
| `styles/journal-neutral.*` | 颜色、线宽、字体、版心令牌，不模仿某篇论文 | 自有主题；字体仅引用系统可用字体 |
| `fixtures/generated/*.csv` | 已知真值的回归、BA、校准、生存、Sobol、网络、场数据 | 本地确定性生成；不取论文数据 |
| `scripts/validate_figure_spec.*` | 模式与阻断条件 | 无网络 |
| `scripts/qa_export.*` | 尺寸、字体、裁切、透明度、颜色、静态/HTML审计 | 无网络 |
| `catalog/sources.yaml` | 身份、证据层、图号、检查日期、许可 URL、用途 | 只保存链接和核验记录 |

不应加入：论文 PDF、论文图截图、网页缓存、Source Data 副本、模型权重、字体文件、按 star 自动抓取的主题、需要 CDN 才能打开的 HTML、未核验 DOI/题名或“高引图”排行榜。

### 5.4 离线工作流

1. **接收与权限**：确认是概念草图、数据准备方案还是获授权的实际绘图；列出可读/可写文件和是否允许安装依赖。
2. **主张冻结**：为每个 panel 写一个主张、反例和证据层；超出数据设计的因果/外推主张降级或阻断。
3. **数据预检**：校验字段、单位、观测单位、配对/层级、缺失、拆分、删失、参数范围和坐标网格；记录 hash，不修改原数据。
4. **图种选择**：返回主图、相邻备选和最小证伪图；用户确认后才生成完整路线。
5. **统计计算**：固定 seed、算法、区间和版本；生成独立的 tidy statistics 表，图形只消费该表与明确允许的原始点。
6. **静态渲染**：在最终物理尺寸下渲染，先灰度/色觉检查，再排 panel；不在画布中手工改变数据。
7. **交互伴侣（可选）**：仅给网络、大热图或三维场；内嵌所有 JS，禁止外部请求，默认显示与静态图一致。
8. **对抗性 QA**：尝试找出会推翻主张的分组、尺度、阈值、异常点、删失、色标或布局选择；不静默修正数据。
9. **导出与清单**：输出静态图、可选 HTML、source-data 表、figure-spec、统计摘要、环境版本、QA 结果和许可清单。

## 6. 期刊、无障碍与导出要求

Nature Research Figure Guide 的[规格页](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)和[面板构建/导出页](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/)（`F`）给出一套可作为默认 profile、但提交时仍需复核目标期刊的要求：单栏约 89 mm、双栏约 183 mm、最大高度约 170 mm；最终尺寸下字体通常 5–7 pt；优先 Arial/Helvetica；RGB；照片至少 300 dpi、建议 450 dpi；矢量优先 PDF/EPS；嵌入字体，Matplotlib PDF 可设 `pdf.fonttype=42`。Nature 的[初投稿指南](https://www.nature.com/nature/for-authors/initial-submission)要求图注可独立理解并避免彩虹色表。Nature Methods [格式说明](https://www.nature.com/nmeth/submission-guidelines/aip-and-formatting)要求定义中心、误差条、n、检验和 P 值等语义。

这些数值应作为 `nature-default` profile，而不是所有期刊的硬编码。MVP 应支持 `journal-neutral` 和可版本化的期刊 profile。每次导出至少检查：

- 最终物理尺寸，不在查看器中靠放大弥补小字；
- 所有轴、颜色条、单位、panel 字母、图例可读且无裁切；
- 颜色不作为唯一编码，线型/符号/直接标签提供冗余；
- sequential/diverging/cyclic/categorical 色表与数据语义一致，diverging 中点有科学意义；
- 在常见色觉模拟和灰度中仍可区分；避免彩虹及红绿二元编码；
- 矢量文件文本保持文本/嵌入字体；密集散点或场栅格可局部 rasterize，标签保持矢量；
- 静态图与 source-data/统计表一致；图片调整只做全局、可追踪操作。Nature 的[图像完整性页](https://research-figure-guide.nature.com/figures/image-integrity/)明确反对选择性局部修改，并禁止生成式 AI 生成科研图像内容；该要求应成为阻断门槛。

## 7. MVP 验收测试

### 7.1 通用阻断测试

| ID | 测试 | 通过条件 |
|---|---|---|
| G-01 | 权限门 | 未明确授权时只产出契约/方案；不读取未指定文件、不安装、不联网、不写图 |
| G-02 | 证据追踪 | 每个 panel 可追到 source ID/hash、列、转换、统计表和主张；无孤立主张 |
| G-03 | 观测单位 | `unit_of_observation`、配对/层级、n 定义缺一即失败；技术重复不冒充生物/实验重复 |
| G-04 | 区间语义 | 所有误差条有中心、类型、水平、方法；未知时阻断而非猜测 |
| G-05 | 拆分与泄漏 | 预测图标记 train/validation/test；阈值、校准和模型选择不在同一测试集完成 |
| G-06 | 确定性 | 同一数据、spec、seed、版本产生相同统计表；允许的图文件元数据差异单列 |
| G-07 | 无障碍 | 色觉模拟、灰度、最终尺寸和非颜色冗余全部通过 |
| G-08 | 导出 | 89/183 mm profile 无裁切；字体/单位/panel 标签齐全；SVG/PDF 文本可选；位图 dpi 达标 |
| G-09 | 离线 | 断网环境完成静态生成；交互 HTML 不发外部请求且有静态等价图 |
| G-10 | 许可 | 第三方组件有版本、许可证 URL/文本；没有论文图片、PDF 或未授权数据进入包 |
| G-11 | 图注完整 | 图注模板能独立解释映射、n、中心/区间、检验、单位和必要预处理 |
| G-12 | 对抗检查 | 自动生成“最可能改变结论的尺度/分组/阈值/异常/布局选择”清单，并记录作者决定 |

### 7.2 图种特异的合成真值测试

| ID | Fixture | 通过条件 |
|---|---|---|
| P-REG | 已知线性趋势 + 异方差 + 一个高杠杆点 | 残差趋势和影响点被诊断图暴露；删除点不会静默发生 |
| P-BA | 已知固定偏倚与方差的成对测量 | 偏倚与 LoA 在预设容差内；交换 A/B 后差值符号按契约翻转 |
| P-BA-R | 同一 subject 多次测量 | 基础独立 LoA recipe 必须拒绝或切换重复测量方法 |
| P-CAL | 完美校准、过度自信、低样本箱三组概率 | 曲线区分三者；显示 bin count/区间；改变分箱时生成稳健性警告 |
| P-INT | 同一估计的 SD、SE、95% CI、PI | 图注和视觉不能把四者混为同一含义；缺 `interval_type` 时失败 |
| P-EST | 偏态、离群、小 n 和配对反转 | 原始点/ECDF 可见；小 n 禁止 KDE；配对方向不被组均值掩盖 |
| P-ROC | 高度不平衡二分类，已知排序 | PR 画阳性率基线；ROC/PR 数值与官方实现一致；阈值表来自独立评估集 |
| P-DCA | 已知风险与阈值效用 | net benefit 与手算值一致；缺效用语义时不画“临床有用”结论 |
| P-SURV | 已知事件、删失和延迟进入 | risk table 与手算一致；删失不计事件；交换编码触发失败 |
| P-SENS | Ishigami 等已知敏感性函数 | S1/ST 排序与置信区间在预设容差内；相关输入触发前提警告 |
| P-ABL | 同 seed/fold 的完整模型与消融 | 画配对 delta 与区间；seed 集不匹配时拒绝比较 |
| P-HEAT | 已知簇、缺失值和固定排序矩阵 | 缺失不变成零；变换/聚类关闭时保持输入顺序；开启时记录算法 |
| P-NET | 已知节点/边/权重的有向图 | 节点边计数和映射一致；布局 seed 可复现；几何距离警示存在 |
| P-FIELD | 解析标量场与恒定/旋转矢量场 | 坐标方向、单位、矢量方向、共享色标和差值正确；网格不单调时拒绝 |

### 7.3 人工审阅问题

1. 去掉标题后，图和图注是否仍能说明比较对象、单位和不确定性？
2. 有没有一个视觉通道没有数据字段，或一个字段被两种互相矛盾的视觉通道表达？
3. 换成合理的轴尺度、分箱、阈值、色标、带宽、聚类或网络布局，主结论是否消失？
4. 图中最醒目的对象是否真是最重要的证据，而不是样本最多或颜色最亮的对象？
5. 不查看交互层，静态图是否足以核验正文主张？
6. 审稿人能否从 source-data 表重算关键量？

## 8. 流行度与引文信号（仅用于发现）

以下是 2026-08-14 的快照，会随平台、去重和数据库覆盖变化，不能用于证明方法质量、复现性或适用性。

### 8.1 GitHub popularity/maintenance signal

| 仓库 | stars 快照 | 用途说明 |
|---|---:|---|
| [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) | 66,980 | 发现分类评估/校准实现 |
| [matplotlib/matplotlib](https://github.com/matplotlib/matplotlib) | 23,078 | 发现通用静态/场图实现 |
| [plotly/plotly.py](https://github.com/plotly/plotly.py) | 18,738 | 发现离线交互输出 |
| [networkx/networkx](https://github.com/networkx/networkx) | 17,193 | 发现网络数据与布局实现 |
| [seaborn/seaborn](https://github.com/mwaskom/seaborn) | 13,998 | 发现统计图高层接口 |
| [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | 11,573 | 发现统计诊断实现 |
| [vega/altair](https://github.com/vega/altair) | 10,452 | 发现声明式交互备选 |
| [tidyverse/ggplot2](https://github.com/tidyverse/ggplot2) | 6,979 | 发现 R 静态图生态 |
| [pyvista/pyvista](https://github.com/pyvista/pyvista) | 3,769 | 发现三维场/网格实现 |
| [CamDavidsonPilon/lifelines](https://github.com/CamDavidsonPilon/lifelines) | 2,604 | 发现生存分析实现 |
| [jokergoo/ComplexHeatmap](https://github.com/jokergoo/ComplexHeatmap) | 1,531 | 发现复杂热图实现 |
| [SALib/SALib](https://github.com/SALib/SALib) | 1,003 | 发现敏感性分析实现 |

stars 是可见度信号，会受项目年龄、社区规模和平台偏好影响。本表不设“高 star 才准入”门槛；准入仍由官方文档、许可、统计契约和本地测试决定。

### 8.2 OpenAlex citation/discovery signal

| 论文 | OpenAlex cited_by_count 快照 | 记录 |
|---|---:|---|
| Saito & Rehmsmeier, PR vs ROC, DOI 10.1371/journal.pone.0118432 | 4,903 | [OpenAlex work](https://openalex.org/W1966716734) |
| Ho et al., DABEST, DOI 10.1038/s41592-019-0470-3 | 1,948 | [OpenAlex work](https://openalex.org/W2952837230) |
| Herman & Usher, SALib, DOI 10.21105/joss.00097 | 1,521 | [OpenAlex work](https://openalex.org/W2569457803) |
| Lam et al., GraphCast, DOI 10.1126/science.adi2336 | 1,286 | [OpenAlex work](https://openalex.org/W4388654737) |
| Krzywinski & Altman, box plots, DOI 10.1038/nmeth.2813 | 592 | [OpenAlex work](https://openalex.org/W2017761002) |
| Krzywinski & Altman, error bars, DOI 10.1038/nmeth.2659 | 291 | [OpenAlex work](https://openalex.org/W1983075605) |
| Altman & Krzywinski, simple regression, DOI 10.1038/nmeth.3627 | 172 | [OpenAlex work](https://openalex.org/W1605498756) |
| Clark et al., survival analysis, DOI 10.1038/s41592-022-01563-7 | 29 | [OpenAlex work](https://openalex.org/W4289783327) |

不同索引与出版社页面的计数会不同。本表只用于记录候选发现过程覆盖了高可见度方法，不把被引数写进图形推荐评分，也不把新但低引的方法自动排除。

## 9. MVP 与后续阶段边界

MVP 应实现：11 类数据/统计契约；Python 或 R 单后端运行门；静态导出；网络/热图/场图的可选自包含 HTML；通用与图种特异测试；来源与许可目录；只读审计模式。

MVP 不应实现：

- 自动抓取 GitHub、arXiv、Nature 或 Science 图片并建立图像库；
- 根据被引数或 star 自动采纳绘图风格；
- 生成式 AI 创建、修补或美化科研数据图像；
- 自动下载 PDF、Source Data、模型或字体；
- 把浏览器交互状态当投稿证据；
- 未经用户确认直接修改数据、执行统计、运行仿真/训练或写回稿件；
- 把示例论文中的视觉选择当作跨领域统计标准；
- 在同一运行中混用 Python/R 默认值并声称结果等价。

后续阶段可评估：重复测量 Bland–Altman 的专用实现、竞争风险/时间依赖 ROC、层级 Bayesian forest、空间自相关诊断、并行坐标/降维稳定性、可视化语法的 JSON schema、出版社 profile 的版本化更新，以及交互图无障碍的键盘/屏幕阅读器测试。

## 10. 最终来源表

| 来源 | 证据层 | 本报告使用内容 | 许可/复用备注 |
|---|---|---|---|
| [Nature Research Figure Guide：规格](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/) | F | 尺寸、字体、色彩、分辨率、矢量和字体嵌入 | 规则可摘要；页面内容/素材仍受网站条款约束 |
| [Nature Research Figure Guide：面板与导出](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/) | F | 89/183 mm、170 mm、panel 排版 | 仅链接和规则摘要 |
| [Nature Research Figure Guide：图像完整性](https://research-figure-guide.nature.com/figures/image-integrity/) | F | 禁止选择性局部编辑与生成式 AI 图像内容 | 作为 QA 门槛；不复制页面图像 |
| [Nature 初投稿指南](https://www.nature.com/nature/for-authors/initial-submission) | F | 图注独立可懂、避免彩虹 | 提交时复核最新版 |
| [Nature Methods 格式说明](https://www.nature.com/nmeth/submission-guidelines/aip-and-formatting) | F | 中心、误差条、n、检验、P 值说明 | 提交时复核最新版 |
| [statsmodels graphics](https://www.statsmodels.org/stable/graphics.html) | F | 回归、影响和一致性图 API 入口 | BSD-3-Clause 软件 |
| [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) | F | calibration curve、Brier 分解注意事项 | BSD-3-Clause 软件 |
| [scikit-learn ROC API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html) | F | ROC 输入/阈值语义 | BSD-3-Clause 软件 |
| [scikit-learn PR display](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.PrecisionRecallDisplay.html) | F | PR、AP 和 prevalence baseline | BSD-3-Clause 软件 |
| [DABEST 教程](https://acclab.github.io/DABEST-python/tutorials/01-basics.html) | F | 估计图、BCa CI、原始数据+效应量 | 当前代码 Apache-2.0；文档另查站点许可 |
| [ArviZ HDI](https://python.arviz.org/en/v0.23.4/api/generated/arviz.plot_hdi.html) | F | 后验 HDI 绘图契约 | Apache-2.0 软件 |
| [lifelines KaplanMeierFitter](https://lifelines.readthedocs.io/en/stable/fitters/univariate/KaplanMeierFitter.html) | F | duration/event/entry 与 CI | MIT 软件 |
| [SALib 文档](https://salib.readthedocs.io/en/stable/index.html) | F | Sobol、Morris、FAST | MIT 软件 |
| [ComplexHeatmap 书](https://jokergoo.github.io/ComplexHeatmap-reference/book/) | F | 热图、注释与交互设计 | MIT 软件；书页内容仅摘要/链接 |
| [NetworkX drawing](https://networkx.org/documentation/stable/reference/drawing.html) | F | 基础绘图边界、GraphML/专用工具建议 | BSD-3-Clause 软件 |
| [Matplotlib contourf](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.contourf.html) | F | 标量场网格/形状/API | Matplotlib License |
| [Matplotlib streamplot](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.streamplot.html) | F | 二维流线输入和密度控制 | Matplotlib License |
| [PyVista streamlines](https://docs.pyvista.org/examples/01-filter/streamlines.html) | F | 三维场/流线 | MIT 软件；示例数据许可另核验，不打包 |
| [Plotly 自包含 HTML](https://plotly.com/python/interactive-html-export/) | F | `write_html`、内嵌 JS 与文件体积权衡 | MIT 软件；禁用 CDN 才能离线 |
| [ggplot2 ggsave](https://ggplot2.tidyverse.org/reference/ggsave.html) | F | 格式、尺寸、单位、dpi | MIT 软件 |
| [Bland & Altman, PMID 2868172](https://pubmed.ncbi.nlm.nih.gov/2868172/) | M/A | 一致性与相关的区别、原始方法身份 | 仅书目信息和摘要释义；不复制正文/图 |
| [Simple linear regression](https://www.nature.com/articles/nmeth.3627) | C/F | Fig. 1–3 回归解释锚点 | 按文章 Rights and permissions；默认仅链接 |
| [Error bars in experimental biology](https://www.nature.com/articles/nmeth.2659) | C/F | Fig. 1 误差条语义 | 按文章 Rights and permissions；默认仅链接 |
| [Visualizing samples with box plots](https://www.nature.com/articles/nmeth.2813) | C/F | Fig. 2–4 小样本、偏态、柱图对比 | 按文章 Rights and permissions；默认仅链接 |
| [DABEST Nature Methods](https://www.nature.com/articles/s41592-019-0470-3) | C/F | Fig. 1 估计图演化和方法依据 | 文章与当前软件许可分别核验；不复制图 |
| [Survival analysis: part I](https://www.nature.com/articles/s41592-022-01563-7) | C/F | Fig. 2–3 KM、删失误用 | 按文章开放许可/credit line；默认仅链接 |
| [Guo et al., arXiv 1706.04599](https://arxiv.org/abs/1706.04599) | M/A | 现代神经网络校准、温度缩放 | arXiv 页面/稿件许可需逐项检查；仅链接 |
| [Saito & Rehmsmeier, PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432) | F | 不平衡分类中 PR 相对 ROC 的解释 | PLOS 页面显示开放许可；复用仍需署名 |
| [Clustergrammer, Scientific Data](https://www.nature.com/articles/sdata2017151) | C/F | Fig. 1–2 交互热图能力 | 文章许可与 MIT 代码分别记录 |
| [ComplexHeatmap, Bioinformatics](https://academic.oup.com/bioinformatics/article/32/18/2847/1743594) | C/F | Fig. 1 多热图/注释/OncoPrint | 按文章许可；代码 MIT；默认仅链接 |
| [Crameri et al., colour misuse](https://www.nature.com/articles/s41467-020-19160-7) | C/F | 感知均匀色表和色觉/彩虹风险 | 文章为开放获取；第三方 credit line 仍需核验 |
| [Pangu-Weather, Nature](https://www.nature.com/articles/s41586-023-06185-3) | C/F | Fig. 2–5 评分、场、轨迹、ensemble 图注 | 按文章 Rights and permissions；默认仅链接 |
| [GraphCast, DeepMind publication page](https://deepmind.google/research/publications/22598/) | M | Science 身份与作者稿入口 | 作者稿标明个人使用/不可再分发；只保存链接 |
| [Nature Machine Intelligence calibration example](https://www.nature.com/articles/s42256-024-00976-7) | C | Fig. 3 分箱直方图和 95% CI | 示例锚点，不作为统计权威；默认仅链接 |
| [Nature Microbiology network example](https://www.nature.com/articles/s41564-023-01347-5) | C/F | Fig. 3 节点/边编码与偏差警示 | 示例锚点；按文章许可；默认仅链接 |
| [npj Digital Medicine sensitivity example](https://www.nature.com/articles/s41746-022-00632-7) | C | Fig. 3 S1/ST 与 S2 | 示例锚点，不替代 SALib 方法契约 |
| [Nature Communications sensitivity example](https://www.nature.com/articles/s41467-022-31860-w) | C | Fig. 3 S1/ST 和 95% CI | 示例锚点；默认仅链接 |

## 11. 推荐的下一步（不构成执行授权）

先做一个不依赖论文图像的 P0 素材包：`plot-archetypes.yaml`、`figure-spec.schema.json`、11 个 recipe 文档、14 个合成 fixture、通用 QA 清单和来源/许可目录。随后选 Python 或 R 作为首个实现后端，按第 7 节逐项通过测试；另一后端在统计表契约稳定后再加入。网络、热图和场图的交互只在静态证据链通过后进入 P1。

在进入实际开发前，应由维护者确认：首个后端、MVP 是否包含决策曲线与竞争风险、目标期刊 profile、允许的依赖列表、交互 HTML 是否属于交付范围，以及一次明确的文件写入/测试授权。
