# Engineering Research Workbench S1 Agent Host Compatibility Survey

- 调查日期：2026-08-14（Asia/Shanghai）
- 调查对象：S1 的一个 umbrella Skill 与八个 focused Skills
- 目标宿主：Claude Code、OpenCode、Hermes Agent、OpenClaw
- 稳定版边界：Claude Code v2.1.232、OpenCode v1.18.18；OpenCode V2 beta 不纳入本次稳定适配合同
- 证据边界：只使用 Agent Skills 官方规范、各宿主官方文档、官方仓库源码与官方发布页；未使用博客、论坛、聚合站或二手教程
- 本报告性质：只读兼容性调查与实现建议；不是安装、下载、运行、发布、推送或合并授权

## 1. 结论

当前 S1 **不能以“原样目录、原样正文、原样激活效果”在四个宿主中无损共用**。它已经具备很好的 Agent Skills 公共格式基础，但仍有两个阻断项：

1. 八个 focused Skills 都通过 `../engineering-research-copilot/references/...` 跨出自身 Skill 根目录读取共享规范。Agent Skills 的可移植资源模型以 Skill 根目录内的相对路径为基准；Hermes 的 `skill_view(..., file_path=...)` 更明确拒绝任何 `..` 路径。因此，Hermes 下这些共享规范无法通过原生渐进加载器读取。
2. 当前九个 `description` 长度为 350–403 字符，而 Hermes 在系统提示中的 Skill 描述硬截断为 60 个字符。虽然完整 `SKILL.md` 激活后仍可加载，但其隐式路由会丢失 60 字符之后的触发语义；当前中文触发词大多位于后段。

Hermes 的路径失败可由固定源码直接判定；Claude Code、OpenCode、OpenClaw 对这些跨 sibling references 的实际加载尚未做真实宿主验证，所以只能标为未确认，不能把“普通文件工具可能读到”替代宿主 Skill loader 证据。

可行目标是：**保留一个规范源集群，生成确定性、可追溯、权限不扩张的宿主投影**。公共源继续只使用 Agent Skills 标准字段；每个投影让每个 focused Skill 自包含共享合同，或在宿主明确支持时使用宿主根变量；Hermes 投影还需将最关键的“做什么/何时用”压到前 60 字符。这样可以达到工作流语义等价，但不是逐字节相同，也不能抹平宿主自身的命令命名、权限和会话加载差异。

## 2. 证据标签

| 标签 | 含义 |
| --- | --- |
| **已确认** | 官方公开规范或官方产品文档明确写出，属于可依赖的外部合同。 |
| **源码推断** | 官方仓库截至检查日的固定版本/提交源码明确实现，但公开文档未承诺；升级后必须重验。 |
| **未确认** | 官方资料没有明确承诺，或资料之间不足以证明；本报告不据此猜测路径或能力。 |
| **本地事实** | 对本仓库当前文件的只读检查结果，不等同于宿主运行验证。 |

## 3. 当前 S1 基线

截至检查日，本仓库 `skills/` 下共有九个直接 sibling Skills：

1. `engineering-research-copilot`（umbrella）
2. `research-direction-evidence`
3. `research-literature-evidence`
4. `research-method-transfer`
5. `research-manuscript`
6. `research-cross-review`
7. `research-data-comparison`
8. `research-evidence-adversary`
9. `research-figure-workflow`

本地只读检查得到：

- 九个目录名都与各自 frontmatter `name` 相同。
- 九个 Skill 当前都只使用 `name` 和 `description` 两个 frontmatter 字段，属于 Agent Skills 最小公共子集。
- `description` 长度依次落在 350–403 字符范围内。
- 每个 focused Skill 的 `SKILL.md` 都有一处指向 `../engineering-research-copilot/references/...` 的跨 sibling 引用；umbrella 自身没有该类引用。
- 仓库根已有 `.codex-plugin/plugin.json`，其中 `skills` 指向 `./skills/`；没有 `.claude-plugin/plugin.json` 或 `openclaw.plugin.json`。

这些事实只说明格式与目录现状，没有替代四个宿主上的 fresh-context 运行验证。

## 4. 一页兼容矩阵

| 宿主 | 项目级位置 | 用户/共享位置 | 显式与隐式调用 | 多 sibling/递归发现 | 宿主元数据 | 当前 S1 原样结论 |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code | **已确认** `.claude/skills/<name>/SKILL.md`；插件为 `<plugin>/skills/<name>/SKILL.md` | **已确认** `~/.claude/skills/<name>/SKILL.md`；Windows 的 `~/.claude` 为 `%USERPROFILE%\.claude` | **已确认** 隐式按描述；显式 `/skill-name`；插件形式主命令 `/plugin:skill`，新版本在无冲突时也接受 bare name | **已确认** 同一 `skills/` 根下多个直接子 Skill；项目父目录/按需嵌套 `.claude/skills`；任意 `skills/group/name` 深层递归 **未确认** | **已确认** 支持调用控制、模型、子代理、hooks、paths、shell 等 Claude 专用顶层字段 | 公共 frontmatter 可读；当前跨 sibling 引用不属于最稳妥自包含模型。Claude 插件可用 `${CLAUDE_PLUGIN_ROOT}` 明确访问插件共享资源，但需要投影改写链接。 |
| OpenCode v1.18.18 | **已确认** `.opencode/skills/<name>/SKILL.md`、`.claude/skills/...`、`.agents/skills/...` | **已确认** `~/.config/opencode/skills/...`、`~/.claude/skills/...`、`~/.agents/skills/...` | **已确认** 模型通过原生 `skill({name})` 按需加载；**源码推断** v1.18.18 把 Skill 注册为同名 slash command（同名既有 command 优先） | 文档 **已确认** 直接子级；v1.18.18 源码 `**/SKILL.md` 表明递归发现，属 **源码推断** | **已确认** 只识别标准的 `name`、`description`、`license`、`compatibility`、`metadata`；未知字段忽略 | 公共 frontmatter 可读，九个直接 sibling 可发现；加载提示只把 Skill 自身目录声明为 base，跨 sibling 资源读取 **未确认**，不能宣称无损。 |
| Hermes Agent | 专用自动项目目录 **未确认**；可在 profile 配置 `skills.external_dirs` 指向仓库或投影目录 | **已确认** `$HERMES_HOME/skills`，Linux/WSL 默认 `~/.hermes/skills`；原生 Windows 默认 `%LOCALAPPDATA%\hermes\skills` | **已确认** `/skill-name`、自然语言请求、`skills_list`/`skill_view`；一条消息最多叠加 5 个 leading skills | 文档展示分组目录；官方源码 `os.walk` 表明递归，属 **源码推断** | **已确认** `version`、`platforms`、`required_environment_variables` 与 `metadata.hermes` 的工具/配置门控 | **不无损**：60 字符提示截断降低隐式触发；`skill_view` 明确拒绝 `..`，八个共享引用无法原样渐进读取。必须生成自包含投影。 |
| OpenClaw | **已确认** `<workspace>/skills`、`<workspace>/.agents/skills` | **已确认** `~/.agents/skills`（默认 state）、`<state-dir>/skills`（默认 `~/.openclaw/skills`）、`skills.load.extraDirs` | **已确认** 模型可按描述选择；授权发送者可用 `$skill-name`（每条消息最多 8 个）或独立 `/skill-name ...` | **已确认** 配置根下递归最多 6 层 | **已确认** `user-invocable`、`disable-model-invocation`、直接工具派发及 `metadata.openclaw` 门控 | 九个 Skill 可发现；现有 `.codex-plugin/plugin.json` + `skills/` 符合 OpenClaw 的 Codex bundle 检测形状。跨 sibling 正文链接仍非其 `{baseDir}` 自包含合同，故 bundle 可安装不等于内容无损。 |

矩阵依据均检查于 2026-08-14： [Claude Code Skills](https://code.claude.com/docs/en/skills)、[Claude Code settings](https://code.claude.com/docs/en/settings)、[OpenCode Agent Skills](https://opencode.ai/docs/skills)、[OpenCode v1.18.18 Skill discovery source](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/skill/index.ts)、[OpenCode v1.18.18 command source](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/command/index.ts)、[Hermes Skills System](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/features/skills.md)、[Hermes skill loader](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/agent/skill_utils.py)、[Hermes skill tool](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/tools/skills_tool.py)、[OpenClaw Skills](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/tools/skills.md)、[OpenClaw bundle compatibility](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/plugins/bundles.md)。

## 5. 公共规范基线

### 5.1 目录与 frontmatter

**已确认。** Agent Skills 规定每个 Skill 是一个至少含 `SKILL.md` 的目录；`scripts/`、`references/`、`assets/` 等为可选资源。`SKILL.md` 必须含 YAML frontmatter 与 Markdown 正文。标准字段如下：

- 必需：`name`（1–64，英文小写字母/数字/单连字符，不能首尾连字符或连续连字符，且与父目录同名）、`description`（1–1024，说明做什么和何时用）。
- 可选：`license`、`compatibility`（最多 500 字符）、`metadata`（string-to-string map）、实验性 `allowed-tools`。
- 文件引用应从 Skill 根目录使用相对路径，建议只深入一层；完整 `SKILL.md` 激活时加载，资源按需加载。

来源（检查日期 2026-08-14）：[Agent Skills specification，固定提交 `69ef37e`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx)。

### 5.2 对 S1 的直接含义

- 当前九个 `name`/目录关系与 `description` 长度符合公共格式。
- `metadata` 的规范类型只是 string-to-string map。Hermes/OpenClaw 文档展示的嵌套厂商对象虽各自可解析，但不应直接写回公共源；OpenCode 明确只承诺 string-to-string，Claude 的上传/打包路径也只接受规范字段集合。
- 跨 sibling 的 `../engineering-research-copilot/references/...` 不在规范展示的 Skill 自包含资源形态内。即使某个宿主的普通文件读取工具偶然可以打开，也不能据此宣布跨宿主兼容。
- 公共源不应添加 `allowed-tools` 来“提高适配度”：该字段仍属实验性，而且各宿主的预授权含义不同；S1 的只读默认和分离授权应继续由规范正文与宿主外层权限共同约束。

## 6. Claude Code

### 6.1 安装与发现

**已确认。** Claude Code 的 Skill 位置为：

- 项目：`.claude/skills/<skill-name>/SKILL.md`
- 用户：`~/.claude/skills/<skill-name>/SKILL.md`
- 插件：`<plugin>/skills/<skill-name>/SKILL.md`

项目扫描从启动目录向父目录直到仓库根；启动目录以下的嵌套 `.claude/skills` 不在启动时加载，而是在 Claude 首次读取或编辑对应子目录文件后加入会话。`--add-dir`/`/add-dir` 会额外加载所给目录中的 `.claude/skills`。Skill 目录符号链接受支持，同一真实目标只载入一次。

九个 S1 Skills 作为 `.claude/skills/` 或插件 `skills/` 的九个直接子目录，属于文档明确的布局。对 `skills/group/name/SKILL.md` 这种在同一 Skill 根下任意加深的递归扫描，官方文档未给出保证；S1 不需要依赖它。

来源（检查日期 2026-08-14）：[Claude Code Skills：位置、父目录与附加目录发现](https://code.claude.com/docs/en/skills)、[Claude plugin Skills reference](https://code.claude.com/docs/en/plugins-reference#skills)。

### 6.2 调用与元数据

**已确认。** Claude 根据 `description`/`when_to_use` 隐式加载，也接受 `/skill-name` 显式调用。项目/个人 Skill 的命令名来自目录；插件 Skill 以 `/plugin-name:skill-name` 命名，当前版本在无同名命令冲突时也接受 bare name。默认用户和模型均可调用；`disable-model-invocation: true` 关闭模型自动调用，`user-invocable: false` 隐藏用户命令。

Claude Code 在标准字段外支持 `when_to_use`、`argument-hint`、`arguments`、`disable-model-invocation`、`user-invocable`、`disallowed-tools`、`model`、`effort`、`context: fork`、`agent`、`background`、`hooks`、`paths`、`shell` 等。它还支持 `${CLAUDE_SKILL_DIR}`；插件 Skill 可通过 `${CLAUDE_PLUGIN_ROOT}` 引用插件内由多个 Skills 共享的资源。

这些扩展不应进入 S1 公共 frontmatter。特别是 `context: fork`、`allowed-tools`、`model` 会改变上下文、权限或模型选择，不是格式适配的中性操作。

来源（检查日期 2026-08-14）：[Claude Skills frontmatter、调用控制与路径变量](https://code.claude.com/docs/en/skills)。

### 6.3 Windows

**已确认。** 官方设置文档明确说 Windows 上 `~/.claude` 解析为 `%USERPROFILE%\.claude`。因此用户级目标是 `%USERPROFILE%\.claude\skills\<name>\SKILL.md`；项目路径仍是仓库内 `.claude\skills\...`。Claude 支持 Git Bash，也能在相关版本/配置下以 PowerShell 执行 Skill 内联 shell；S1 当前不应为适配而新增任何内联执行。

符号链接虽然被 Claude Skill 文档支持，但 Windows 创建目录链接可能受 Developer Mode/权限及插件根边界约束。生产投影应默认复制并校验哈希，符号链接只作为本地开发优化。

来源（检查日期 2026-08-14）：[Claude settings scopes 的 Windows 路径说明](https://code.claude.com/docs/en/settings#what-uses-scopes)、[Claude Skills 的 `shell` 与符号链接规则](https://code.claude.com/docs/en/skills)。

### 6.4 S1 投影判断

- **项目投影：** 把九个自包含 Skill 复制到 `.claude/skills/`；命令保持 bare name。
- **插件投影：** Claude 可消费默认插件布局；为了固定插件身份、版本和 namespace，建议另加 Claude 自己的 `.claude-plugin/plugin.json`。现有 `.codex-plugin/plugin.json` 不是 Claude 清单，不能冒充。插件可保留一个共享合同副本并把 focused links 改写为 `${CLAUDE_PLUGIN_ROOT}/...`，但这会成为 Claude 专用正文投影。
- **当前原样：** 发现可行；共享引用的跨 sibling 普通 Markdown 跳转能否始终被安全、自动读取没有官方合同。结论为“可发现，未证明内容无损”。

## 7. OpenCode

### 7.1 安装与发现

**已确认。** OpenCode 官方文档列出六个位置：

- 项目：`.opencode/skills/<name>/SKILL.md`、`.claude/skills/<name>/SKILL.md`、`.agents/skills/<name>/SKILL.md`
- 用户：`~/.config/opencode/skills/<name>/SKILL.md`、`~/.claude/skills/<name>/SKILL.md`、`~/.agents/skills/<name>/SKILL.md`

项目级扫描从当前目录向上直到 Git worktree，文档合同写的是各根下的直接 `skills/*/SKILL.md`。

**已确认/源码推断。** 官方配置 schema 暴露 `skills.paths`；v1.18.18 固定版本源码实际使用 `skills/**/SKILL.md`、`{skill,skills}/**/SKILL.md` 与额外根的 `**/SKILL.md`，并设置 `symlink: true`。因此当前实现可递归找到更深分组，并把 `skills.paths` 的相对路径按当前工作目录解析、绝对路径直接使用。配置键存在是 schema 合同；递归深度与解析细节属于版本绑定源码行为，不作为永续合同。

来源（检查日期 2026-08-14）：[OpenCode Agent Skills](https://opencode.ai/docs/skills)、[OpenCode config schema](https://opencode.ai/config.json)、[OpenCode v1.18.18 固定发布](https://github.com/anomalyco/opencode/releases/tag/v1.18.18)、[v1.18.18 `skill/index.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/skill/index.ts)。

### 7.2 调用与元数据

**已确认。** 官方文档保证：可用 Skills 的 name/description 会出现在原生 `skill` 工具描述中，模型按需调用 `skill({name})`。权限可按 Skill 名设 `allow`、`ask`、`deny`，也可对某个 agent 关闭整个 `skill` 工具。这只控制 Skill 加载，不是对写文件、shell、网络等能力的替代授权。

**源码推断。** v1.18.18 的 command registry 会遍历 `skill.all()`，把不存在同名既有 command 的每个 Skill 注册为同名、`source: "skill"` 的 command。因此当前稳定版可通过 `/skill-name` 进入；若名称与内建、自定义或 MCP command 冲突，既有 command 优先。公开 Skills 页面没有把 slash 形式写成稳定合同，升级后应重验。

OpenCode 文档明确只识别标准 `name`、`description`、`license`、`compatibility`、`metadata`，未知 frontmatter 字段被忽略。它没有当前稳定文档承诺的 OpenCode 专用 Skill frontmatter。因此，任何在预览页或未来分支看到的自动调用字段都不能写入本次兼容合同。

**版本边界。** OpenCode V2 在检查日仍有独立 beta 文档和迁移路径；其中出现的 V2 Skill metadata 或 slash/autoinvoke 语义不属于 v1.18.18 稳定合同，本次 adapter 不应提前采用。

来源（检查日期 2026-08-14）：[OpenCode Skills 的加载、frontmatter 与权限](https://opencode.ai/docs/skills)、[v1.18.18 `command/index.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/command/index.ts)、[OpenCode V2 migration guide](https://opencode.ai/v2/docs/migrate-v1)。

### 7.3 Windows

**已确认。** OpenCode 可原生运行 Windows，但官方建议 WSL；Windows 盘在 WSL 映射为 `/mnt/c`、`/mnt/d` 等。本仓库在 WSL 中应写成 `/mnt/d/engineering-research-copilot`，不能把 `D:\...` 原样填进 WSL 配置。WSL 的 `~/.config/opencode`、`~/.agents` 属于 WSL 用户 home，与 Windows 用户目录不是同一位置。

**未确认。** 官方 Skills 页面没有把原生 Windows 上 `~/.config/opencode` 精确展开成某个固定 `%APPDATA%` 路径，因此本报告不猜。**源码推断** v1.18.18 提供 `opencode debug paths` 打印实际 data/config/cache/state 根；原生 Windows 安装应先读取该输出再落盘。

来源（检查日期 2026-08-14）：[OpenCode Windows/WSL](https://opencode.ai/docs/windows-wsl/)、[v1.18.18 `debug paths` 源码](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/cli/cmd/debug/index.ts)。

### 7.4 S1 投影判断

- 最稳的项目级公共落点是 `.agents/skills/`：OpenCode 文档支持，OpenClaw 也原生支持。
- 当前实现也可在 `opencode.json` 用 `skills.paths: ["./skills"]` 零复制发现九个 Skills，但这属于源码推断，不能替代文档化的发布投影。
- `skill` 工具加载结果把 Skill 自身目录声明为 base，并只枚举其目录内的 supporting files。普通工具是否会跟随 `../` 读取 sibling 不是 Skill 加载合同，所以当前集群只能判定“发现兼容，资源无损未确认”。

来源（检查日期 2026-08-14）：[v1.18.18 `tool/skill.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/tool/skill.ts)。

## 8. Hermes Agent

### 8.1 安装与发现

**已确认。** Hermes 声明兼容 agentskills.io；主目录是 `$HERMES_HOME/skills`，Linux/WSL 默认 `~/.hermes/skills`。它支持在 `$HERMES_HOME/config.yaml` 的 `skills.external_dirs` 添加其他根，支持 `~` 与 `${VAR}` 展开；本地同名 Skill 优先。外部目录中的 Skills 完整进入系统提示索引、`skills_list`、`skill_view` 与 slash commands。

没有在官方文档中发现类似 `.claude/skills` 或 `<workspace>/skills` 的自动项目级约定，故项目级目录记为 **未确认**。需要项目隔离时，应配置一个明确的 `external_dirs` 绝对路径或使用专用 profile，不能猜测隐藏目录。

**源码推断。** 固定提交的 `iter_skill_index_files()` 使用 `os.walk(..., followlinks=True)`，排除 `.git`、依赖/缓存目录及已经位于 Skill 下的 supporting directories，但没有通用深度上限。因此分组与多个 sibling Skills 可递归发现。相对 `external_dirs` 按 `$HERMES_HOME` 而非当前工作目录解析。

来源（检查日期 2026-08-14）：[Hermes Skills System](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/features/skills.md)、[固定提交的 `agent/skill_utils.py`](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/agent/skill_utils.py)。

### 8.2 调用与元数据

**已确认。** 每个安装 Skill 自动成为 `/skill-name`；用户也可自然语言询问或要求使用某 Skill。`skills_list()` 提供索引，`skill_view(name)` 加载正文，`skill_view(name, file_path)` 加载资源。一条消息开头可叠加最多 5 个 Skill。Hermes 的 bundle YAML 可把常用组合映射为一个命令，但 bundle 只分组，不安装 Skills。

Hermes 扩展支持顶层 `version`、`platforms`、`required_environment_variables`，以及 `metadata.hermes` 下的 tags/category、工具集和工具可用性门控、配置提示等。这些是 Hermes 专用能力，不应写进公共源 frontmatter。

来源（检查日期 2026-08-14）：[Hermes Skills：调用、渐进加载、格式与 bundles](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/features/skills.md)。

### 8.3 两个确定的 S1 阻断项

1. **源码推断，描述截断。** `SKILL_PROMPT_DESC_LIMIT = 60`，超过时只把前 57 个字符加 `...` 放入系统提示索引。S1 九个描述均超过 60，因此虽然格式有效，隐式选择得到的信息并不等价。
2. **源码推断，路径阻断。** `skill_view` 在 `file_path` 含 `..` 时返回 `Path traversal ('..') is not allowed`，并要求目标保持在 `skill_root` 内。因此八个 focused Skills 的跨 sibling shared-contract 链接不能通过 Hermes 原生渐进加载器访问。这不是概率性风险，而是固定源码中的显式拒绝。

来源（检查日期 2026-08-14）：[Hermes 描述截断源码](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/agent/skill_utils.py#L758-L780)、[Hermes `skill_view` 路径校验源码](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/tools/skills_tool.py#L847-L858)。

### 8.4 Windows 与只读边界

**已确认。** 原生 Windows 安装器设置 `HERMES_HOME=%LOCALAPPDATA%\hermes`，数据根中的 `skills\` 即用户级 Skill 目录；终端工具使用 Git Bash，并在入口设置 UTF-8。WSL 则使用自己的 `~/.hermes`。本仓库的 native external path 是 `D:\engineering-research-copilot\...`，WSL path 是 `/mnt/d/engineering-research-copilot/...`，二者不可混用。Skill/YAML 文件应保存为 UTF-8 无 BOM；官方文档明确警告 folded YAML scalar 中的 BOM 可破坏解析。

Hermes 文档还明确说明 `external_dirs` **不是写保护边界**：如果进程有写权限，用户指示下的 `skill_manage` 可以修改外部目录。S1 的审计只读默认必须通过文件系统权限、专用 profile/toolset 或 `skills.write_approval` 等外层控制保留，不能仅凭“external”一词推断只读。

来源（检查日期 2026-08-14）：[Hermes Native Windows Guide](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/windows-native.md)、[Hermes external directories](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/features/skills.md#external-skill-directories)。

### 8.5 S1 投影判断

Hermes 必须使用生成式自包含投影：把每个 focused Skill 所需的共享合同复制到其自身 `references/shared/`，改写为根内链接，并为 prompt index 生成不超过 60 字符、把核心触发词放在最前的描述。仅把当前 `skills/` 加到 `external_dirs` 会发现九个名称，却无法完成共享合同加载，不能验收。

## 9. OpenClaw

### 9.1 安装、优先级与多智能体可见性

**已确认。** OpenClaw 按以下优先级加载 Skills：

1. `<workspace>/skills`
2. `<workspace>/.agents/skills`
3. `~/.agents/skills`（仅默认 state）
4. `<state-dir>/skills`（默认 `~/.openclaw/skills`）
5. bundled Skills
6. `skills.load.extraDirs` 与 plugin Skills

同一配置根下递归发现 `SKILL.md`，深度最多 6 层。多智能体环境中，每个 agent 有自己的 workspace；`<workspace>/skills` 与 `<workspace>/.agents/skills` 只对该 workspace 的 agent 可见，state Skills/extra dirs 可共享，再由 `agents.defaults.skills` 或 `agents.entries.*.skills` 收窄。文档明确提醒 Skill allowlist 不是宿主 shell 授权边界。

若 OpenClaw workspace 就是本仓库根，当前 `skills/` 已处于最高优先级项目位置，九个直接 sibling 可发现。若要避免把开发仓库当运行 workspace，可生成到 `.agents/skills/` 或由 `extraDirs` 指向只读投影。

来源（检查日期 2026-08-14）：[OpenClaw Skills：加载顺序、递归与 agent allowlists](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/tools/skills.md)。

### 9.2 调用与元数据

**已确认。** Eligible Skills 的 name/description/location 被放入紧凑系统提示，模型可自行选择。授权发送者可在 Control UI 或任何 channel 中用 `$skill-name` 显式引用，一条消息最多 8 个；独立 `/skill-name ...` 仍可用。默认 `user-invocable: true`、`disable-model-invocation: false`。

OpenClaw 扩展支持 `homepage`、`user-invocable`、`disable-model-invocation`、`command-dispatch: tool`、`command-tool`、`command-arg-mode`，以及 `metadata.openclaw` 下的 OS、binary/env/config 门控和安装提示。正文应使用 `{baseDir}` 引用 Skill 根。

这些字段不应直接进入公共源：嵌套 `metadata.openclaw` 超出 Agent Skills 的 string-to-string 公共类型，而直接工具派发会改变执行语义和授权边界。

来源（检查日期 2026-08-14）：[OpenClaw Skills：prompt reference、frontmatter 与 gating](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/tools/skills.md)。

### 9.3 现有 Codex bundle 的可复用性

**已确认。** OpenClaw 能安装并映射 Agent Plugins、Codex、Claude 和 Cursor bundles。Codex bundle 的标记是 `.codex-plugin/plugin.json`，默认可含 `skills/`；bundle Skill roots 按普通 OpenClaw Skill roots 加载。当前仓库同时具备该标记和根 `skills/`，因此**包形状满足 OpenClaw 的 Codex bundle 识别合同**。官方安装入口为 `openclaw plugins install <directory-or-source>`，随后用 `plugins list/inspect` 验证。

这不证明现有 manifest 的每个 Codex 专用展示字段都会被 OpenClaw采用；bundle 文档只承诺选择性映射。它也不修复 focused Skill 中的 `../` 链接。故可以把“OpenClaw 可识别当前 Codex bundle”列为已确认，把“九个 Skill 的所有共享资源与触发行为无损”列为未确认/当前不成立。

来源（检查日期 2026-08-14）：[OpenClaw Plugin bundles，固定提交](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/plugins/bundles.md)、[OpenClaw compatible manifest说明](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/plugins/manifest.md)。

### 9.4 Windows

**已确认。** OpenClaw 有 Windows Hub、原生 Windows CLI/Gateway，并建议 WSL2 获得最接近 Linux 的 Gateway 运行时。`OPENCLAW_HOME`、`OPENCLAW_STATE_DIR`、`OPENCLAW_WORKSPACE_DIR` 可改变路径默认值；因此不能在 adapter 中把用户级目录写死为某个盘符。WSL 使用 `/mnt/d/...` 访问本仓库；native Windows 使用 Windows 绝对路径。OpenClaw 对 workspace、project-agent 与 extra-dir roots 做 realpath containment；根外 symlink 目标必须显式列入 `skills.load.allowSymlinkTargets`。

来源（检查日期 2026-08-14）：[OpenClaw Windows](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/platforms/windows.md)、[OpenClaw environment/path variables](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/help/environment.md)、[OpenClaw Skill path containment](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/tools/skills.md#security)。

## 10. “一个源集群无损投影”的严格判断

### 10.1 可以共同保留的部分

四个宿主都能消费以目录为单位、以 `SKILL.md` 为入口的 Agent Skills 风格内容。以下可以成为唯一规范源：

- 九个稳定 Skill 名称与 umbrella/focused 边界；
- 标准 `name`、`description`（经过跨宿主触发优化）、可选 `license`/`compatibility`；
- 不依赖宿主命令语法的工作流正文；
- 只在本 Skill 根内的 `references/`、`scripts/`、`assets/`；
- S1 已有的证据层级、主张—证据、方向确认、独立审稿、只读默认与分离授权语义。

### 10.2 不能无差别共同保留的部分

- Claude 插件命令的 namespace 与 `${CLAUDE_PLUGIN_ROOT}`；
- Claude 的 fork/model/tool preapproval 与动态 shell；
- OpenCode 的版本绑定 slash 注册、递归扫描与 `skills.paths`；
- Hermes 的 60 字符提示索引、profile/external_dirs 与 `metadata.hermes`；
- OpenClaw 的 `$skill` picker、agent allowlist、`{baseDir}`、direct tool dispatch 与 `metadata.openclaw`；
- Windows native 与 WSL 的 home、盘符和路径语法；
- 各宿主对 symlink、权限、会话刷新与同名冲突的不同处理。

因此：

- **逐字节单副本、零 adapter、四宿主行为完全相同：不可行。**
- **一个规范源 + 确定性生成投影 + 宿主外层配置：可行。**
- **当前 S1 原样直接投影：不可验收。** Hermes 的 `..` 拒绝已构成确定性失败。

## 11. 推荐的 adapter 架构

### 11.1 规范源

继续以仓库 `skills/` 为唯一手写源，不在其中混入厂商专用 frontmatter。先做两项源级兼容化：

1. 让每个 focused Skill 的规范依赖保持在本 Skill 根内。可由构建阶段复制共享合同，不必在手写源中维护九份；但生成结果必须自包含。
2. 重写每个 `description` 的首句，把最关键的自然语言触发条件放在前 60 字符。若保留长描述，Hermes 投影须生成等价短描述；若能在公共源中做到 60 字符内兼顾“做什么/何时用”，四宿主可共享同一描述。

### 11.2 确定性投影

建议生成器产生而非人工维护以下逻辑产物：

```text
canonical skills/*
  -> common self-contained projection/skills/*
       -> Claude project projection: .claude/skills/*
       -> OpenCode/OpenClaw project projection: .agents/skills/*
       -> Hermes projection: <profile-or-stage>/skills/*
  -> Claude plugin adapter: .claude-plugin/plugin.json + skills/*
  -> existing Codex bundle: .codex-plugin/plugin.json + skills/*
```

对每个 focused Skill：

- 复制实际使用的共享合同到 `references/shared/`；
- 把所有 `../engineering-research-copilot/...` 改写为根内相对链接；
- 保持正文其他字节与换行语义不变；
- 生成 `projection-manifest.json`，记录源路径、目标路径、源 SHA-256、目标 SHA-256、改写规则和宿主；
- 拒绝目标中仍存在 `../`、绝对开发机路径、未解析变量、BOM 或未登记新增文件。

投影生成只是文件准备，不得顺带安装到用户 home、修改宿主配置、启动 agent、执行 Skill、上传或发布。

### 11.3 宿主 adapter 最小职责

| Adapter | 只负责 |
| --- | --- |
| Claude Code | 选择项目 copy 或 `.claude-plugin` 清单；需要共享根时使用 `${CLAUDE_PLUGIN_ROOT}`；不添加 `allowed-tools`/fork/model。 |
| OpenCode | 选择文档化的 `.opencode/skills` 或 `.agents/skills`；`skills.paths` 只作为版本锁定的开发模式；不依赖 slash 作为唯一入口。 |
| Hermes | 选择 `$HERMES_HOME/skills` 或 `external_dirs`；确保描述前 60 字符足够路由；所有资源根内；明确 write-approval/文件系统权限。 |
| OpenClaw | 选择 workspace/`.agents`/extraDir 或复用 Codex bundle；保留 agent allowlist；不把 Skill 可见性误当 shell 授权。 |

## 12. Windows 路径决策表

| 宿主 | Native Windows | WSL | 不应做的假设 |
| --- | --- | --- | --- |
| Claude Code | `%USERPROFILE%\.claude\skills`（官方明确） | WSL home 的 `~/.claude/skills` | 不把 Windows user Skill 自动当作 WSL Skill；不默认 symlink 权限可用。 |
| OpenCode | 先用 `opencode debug paths` 确认实际 config 根；项目 `.opencode/.claude/.agents` 不受此歧义 | `/mnt/d/engineering-research-copilot`；用户根在 WSL home | 不猜 `~/.config/opencode` 在 native Windows 的具体 `%APPDATA%` 展开。 |
| Hermes | `%LOCALAPPDATA%\hermes\skills`（默认 `HERMES_HOME`） | `~/.hermes/skills`；仓库 `/mnt/d/engineering-research-copilot` | 不把相对 external dir 当 cwd 相对；源码显示它相对 `HERMES_HOME`。 |
| OpenClaw | 根据实际 workspace/state/home 与官方环境变量解析 | WSL home + `/mnt/d/...` | 不硬编码 `~/.openclaw` 到固定盘符；state/workspace 可被环境变量覆盖。 |

## 13. 实现后的最小验收

每个宿主必须在 fresh context 分别完成，不以一个宿主的通过替代另一个：

1. **目录验收：** 恰好发现九个预期 Skill 名；无重复名、无漏项、无意外第十个 Skill。
2. **frontmatter 验收：** 公共源通过 Agent Skills validator；宿主投影能被该宿主列出，无 YAML/BOM 错误。
3. **显式调用：** umbrella 与八个 focused Skills 均能用宿主官方入口加载；记录实际命令名和 namespace。
4. **隐式调用：** 用中文和英文各一组正例/相邻负例；Hermes 单独验证前 60 字符仍能区分方向、文献、方法、写作、审稿、数据、对抗审计和绘图。
5. **资源验收：** 每个 focused Skill 都能通过宿主原生渐进读取机制打开其共享合同；禁止以普通 shell 绕过 Skill loader 来假装通过。
6. **权限验收：** 审计默认只读；无 adapter 添加写入、shell、网络、上传、安装或外部通信预授权；Skill 可见性与实际工具权限分别检查。
7. **多 Skill 验收：** 验证 umbrella 路由到 focused Skill，以及宿主允许的组合调用；不得假设四宿主支持相同的叠加数量。
8. **Windows 验收：** native 与 WSL 分开记录路径、home/state、编码、分隔符和符号链接策略；不混用 `D:\...` 与 `/mnt/d/...`。
9. **可追溯验收：** 投影清单的源/目标 SHA-256 可重算；同一源提交重复生成零差异。
10. **分发验收：** Claude 插件、Codex/OpenClaw bundle 及目录式投影分别验证；“能被检测”与“资源可完整加载”必须是两个独立断言。

## 14. 明确保留的未确认项

以下事项没有足够官方合同，本次不得转写为实现假设：

- Claude Code 对同一 `skills/` 根内任意深层 `skills/group/name/SKILL.md` 的普遍递归发现。
- Claude/OpenCode/OpenClaw 是否会把跨 sibling `../` Markdown 链接作为受支持的 Skill 资源自动读取；Hermes 已明确否定。
- OpenCode 原生 Windows 用户级 `~/.config/opencode` 的固定 `%APPDATA%` 展开；应运行官方二进制的 `debug paths` 查询。
- OpenCode slash Skill 注册在未来版本是否继续保持；当前结论绑定 v1.18.18 源码。
- OpenClaw 对现有 `.codex-plugin/plugin.json` 中 `interface` 展示字段的具体呈现；bundle 只承诺选择性映射。
- 未执行四宿主的实际安装和 fresh-context 测试，因此本报告不是运行通过证据。

## 15. 官方来源登记

所有来源最后检查日期均为 **2026-08-14**。

| 范围 | 一手来源 | 固定点/用途 |
| --- | --- | --- |
| Agent Skills | [Specification](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx) | 提交 `69ef37e9424c0a7ea9dd2293b559e43ec8176379`；目录、frontmatter、资源引用、渐进加载。 |
| Claude Code | [Skills](https://code.claude.com/docs/en/skills) | 位置、发现、调用、frontmatter、路径变量、支持文件、Windows shell。 |
| Claude Code | [v2.1.232 release](https://github.com/anthropics/claude-code/releases/tag/v2.1.232) | 检查日稳定版本边界。 |
| Claude Code | [Settings](https://code.claude.com/docs/en/settings) | scope 与 Windows `%USERPROFILE%\.claude`。 |
| Claude Code | [Plugins reference](https://code.claude.com/docs/en/plugins-reference#skills) | 插件 Skill roots、namespace、symlink/根边界。 |
| OpenCode | [Agent Skills](https://opencode.ai/docs/skills) | 文档化位置、直接子级发现、标准 frontmatter、原生 skill tool 与权限。 |
| OpenCode | [Config schema](https://opencode.ai/config.json) | `skills.paths` 配置键。 |
| OpenCode | [Windows/WSL](https://opencode.ai/docs/windows-wsl/) | WSL 推荐及 `/mnt/<drive>` 映射。 |
| OpenCode | [V2 migration guide](https://opencode.ai/v2/docs/migrate-v1) | V2 beta 与 v1 stable 的边界；不作为本次实现合同。 |
| OpenCode | [v1.18.18 release](https://github.com/anomalyco/opencode/releases/tag/v1.18.18) | 检查日 latest 稳定发布，发布提交 `31406cc`。 |
| OpenCode | [`skill/index.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/skill/index.ts) | 递归 glob、symlink、`skills.paths`；源码推断。 |
| OpenCode | [`tool/skill.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/tool/skill.ts) | Skill base directory 与 supporting-file listing；源码推断。 |
| OpenCode | [`command/index.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/command/index.ts) | Skill 注册为同名 command；源码推断。 |
| OpenCode | [`debug/index.ts`](https://github.com/anomalyco/opencode/blob/v1.18.18/packages/opencode/src/cli/cmd/debug/index.ts) | `opencode debug paths`；源码推断。 |
| Hermes | [Skills System](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/features/skills.md) | 提交 `c896c09c...`；位置、调用、frontmatter、external dirs、bundles、写边界。 |
| Hermes | [Work with Skills](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/guides/work-with-skills.md) | 用户工作流与安装/调用补充。 |
| Hermes | [Native Windows Guide](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/website/docs/user-guide/windows-native.md) | 原生 Windows `HERMES_HOME`、Git Bash、UTF-8/BOM。 |
| Hermes | [`agent/skill_utils.py`](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/agent/skill_utils.py) | 描述 60 字符、递归发现、external path 解析；源码推断。 |
| Hermes | [`tools/skills_tool.py`](https://github.com/NousResearch/hermes-agent/blob/c896c09c42910c584c4c7d2325b58c14713ea42c/tools/skills_tool.py) | `skill_view` 根内路径与 `..` 拒绝；源码推断。 |
| OpenClaw | [Skills](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/tools/skills.md) | 提交 `5523f8a...`；路径、递归、multi-agent、调用、frontmatter、containment。 |
| OpenClaw | [Plugin bundles](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/plugins/bundles.md) | Codex/Claude/Agent Plugins bundle 检测与映射。 |
| OpenClaw | [Plugin manifest](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/plugins/manifest.md) | native manifest 与 compatible bundle 的边界。 |
| OpenClaw | [Windows](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/platforms/windows.md) | Windows Hub、native CLI、WSL2。 |
| OpenClaw | [Environment](https://github.com/openclaw/openclaw/blob/5523f8a334c94c107d996a115b4b498a622fe4f0/docs/help/environment.md) | home/state/workspace path variables。 |

## 16. 最终建议

进入实现时采用以下验收口径：

- 把“九个 Skill 均被发现”视为 discovery gate，不视为功能通过。
- 把“每个 focused Skill 能在本 Skill 根内加载共享合同”设为 portability gate；Hermes 是决定性测试宿主。
- 把“描述前 60 字符可区分九类任务”设为 implicit-routing gate。
- 公共源只保留规范字段；厂商元数据只在生成投影中出现，且默认不产生任何执行预授权。
- 优先采用复制 + 哈希清单，Windows symlink 仅作为显式 opt-in 的开发模式。
- 先完成本地生成、静态验证和 fresh-context host tests，再分别请求安装、推送与合并授权；这些阶段不能合并为一个动作。
