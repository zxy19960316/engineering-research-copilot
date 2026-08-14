# Engineering Research Workbench

Engineering Research Workbench 是一组面向工科研究者的证据约束型 Agent Skills。它从一句模糊想法、已有文献、研究计划、结果、提纲、草稿或审稿意见直接进入，在同一套证据、就绪度与权限规则下，调用九个互补 Skill 完成方向调查、文献核验、方法迁移、写作、交叉审阅、数据比较、对抗证据检查和科研绘图工作流。

这不是九套互不相干的提示词，也不是某个宿主专属的实现。仓库只手工维护一份符合 [Agent Skills 规范](https://agentskills.io/specification)的规范 Skill 源，再为 Codex、Claude Code、OpenCode、Hermes、OpenClaw 和 GitHub Copilot 生成确定性的自包含投影。安装过程不改规范源、科研规则或权限；它只把跨 Skill 的共享引用复制到当前 Skill 内并改写引用位置，Hermes 投影还会使用不超过 60 字符的发现描述。每项变化和源/投影 SHA-256 都写入投影清单。

## 能力边界

- 分开文献发现、身份核验与内容核验，明确元数据、摘要、全文和用户材料的证据层级；
- 比较主方向、相邻备选、迁移探索和高风险想法，并给出最小证伪检验；
- 用层级关系图表达方向、主张、证据、反证、约束和测试，节点大小只表示当前任务相关度；
- 按真实就绪度返回概念草图、路线准备方案或可执行路线，不把路线生成当作执行授权；
- 写作前建立主张—证据关系，不虚构引文、数据、实验、结果、数值或结论；
- 先保留独立审稿视角和分歧，再综合问题，并由作者决定实质修改；
- 按科研目的选择绘图配方、统计前提、失败门槛和导出要求，不复制论文图片素材；
- 审计默认只读；文件写入、上传、下载、实验、仿真、训练、发表和外部沟通分别需要明确授权。

## Skill 集群

| Skill | 作用 |
|---|---|
| `engineering-research-copilot` | 模糊入口与跨阶段路由 |
| `research-direction-evidence` | 主张调查、方向比较与交互式层级图 |
| `research-literature-evidence` | 文献发现、身份核验与内容检查 |
| `research-method-transfer` | 方法设计、迁移分析与最小证伪检验 |
| `research-manuscript` | 主张驱动的写作、重构与润色 |
| `research-cross-review` | 独立审阅、分歧保留与综合 |
| `research-data-comparison` | 单位、配对、缺失与不确定性敏感的数据比较 |
| `research-evidence-adversary` | 只读的反证、泄漏和过度推断检查 |
| `research-figure-workflow` | 科研图选择、绘制交接与质量审计 |

共享的证据、权限、就绪度和交接规则只在 umbrella Skill 中规范维护。安装器把实际用到的共享文件按原始字节复制到每个 focused Skill 的 `references/shared/`，同时记录来源和哈希；这些副本是可审计投影，不是第二份规范源。

## 纯净发行包

开发仓库保留测试、研究记录和 M1–M4 历史证据，但这些内容不进入可安装发行包。使用标准库构建器从 Git 已跟踪文件和显式白名单生成 `0.7.0` 纯净 ZIP：

```powershell
python .\build-release.py --check --json
python .\build-release.py --output .\dist\engineering-research-workbench-0.7.0.zip --json
```

ZIP 只包含九个 Skill、`.codex-plugin/plugin.json`、`.claude-plugin/plugin.json`、`agent-hosts.json`、`install-skill.py`、`opencode.json` 和自动生成的 `release-manifest.json`。清单逐文件记录大小与 SHA-256；安装器在清单存在时会先核对完整文件集合和每个字节，再生成宿主投影。相同源码会生成字节一致的 ZIP，`evals/**`、`tests/**`、`docs/**`、状态、计划、CI 和未跟踪文件均不能进入。五个旧里程碑的组合、渲染和验证脚本只保留在开发仓库中用于历史证据回放，并通过 `source_only_paths` 从 ZIP 和所有宿主投影中排除；可安装的 Markdown/Python 运行时不再携带里程碑状态机。

解压后从发行根目录执行：

```powershell
python .\install-skill.py --source . --agent all --scope user --dry-run --json
```

本地构建发行包不等于安装到真实宿主，也不等于发布 GitHub Release；仓库许可证确定和任何公开发布仍需单独决定与授权。

## AGENT适配

| 宿主 | 用户级投影 | 项目级投影 | 主动调用 |
|---|---|---|---|
| Codex | `~/.agents/skills/` | `<项目>/.agents/skills/` | `$research-direction-evidence` 或 `/skills` |
| Claude Code | `~/.claude/skills/` | `<项目>/.claude/skills/` | `/research-direction-evidence` |
| OpenCode | `~/.config/opencode/skills/` | `<项目>/.opencode/skills/` | 在提示中点名 Skill，由原生 `skill` 工具加载 |
| Hermes | Windows 默认 `%LOCALAPPDATA%\hermes\skills`；其他平台 `~/.hermes/skills/` | 见下方说明 | `/research-direction-evidence` |
| OpenClaw | `~/.openclaw/skills/` | `<项目>/.agents/skills/` | `$research-direction-evidence` 或 `/research-direction-evidence` |
| GitHub Copilot CLI | `~/.copilot/skills/` | `<项目>/.github/skills/` | `/research-direction-evidence` |

宿主可依据 Skill 的 `description` 自动发现合适入口，但这只表示工作流被加载，不表示获得文件写入、实验或对外沟通权限。完整路径、刷新方式和官方来源记录在 [`agent-hosts.json`](agent-hosts.json)。适配依据包括 [Codex Skills](https://developers.openai.com/codex/skills)、[Claude Code Skills](https://code.claude.com/docs/en/slash-commands)、[OpenCode Skills](https://opencode.ai/docs/skills)、[Hermes Skills](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md)、[OpenClaw Skills](https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md)和 [GitHub Copilot Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)。

为保留已发布入口的行为，Codex 中的 umbrella router `engineering-research-copilot` 仍关闭隐式调用；八个边界更窄的 focused Skills 可由 Codex 按描述发现，也可由用户显式调用。其他宿主按各自的原生发现机制处理。无论如何被加载，Skill 激活都不会扩大共享权限台账。

OpenCode 的稳定文档保证模型通过原生 `skill` 工具按名称加载；当前稳定版源码虽可形成 `/skill-name` 命令，但这不是稳定文档合同，且可能被同名 command 遮蔽，因此本项目不把 slash 形式写成已确认能力。仓库根部的 `opencode.json` 让从仓库根启动的 OpenCode 直接读取同一 `skills/` 源；安装器仍支持原生用户级和项目级投影，并尊重 `OPENCODE_CONFIG_DIR` 或 `XDG_CONFIG_HOME`。OpenClaw 用户级投影会尊重 `OPENCLAW_STATE_DIR`。

仓库也包含 Claude Code 与 Codex 的原生插件清单，供宿主识别集群身份与版本。Claude Code 开发模式可以从仓库根加载：

```text
claude --plugin-dir .
```

插件方式会使用命名空间，例如 `/engineering-research-workbench:research-direction-evidence`；直接投影到 `.claude/skills/` 时使用短名称。仓库根加载属于开发模式，会看见历史源码；纯净使用应解压发行 ZIP 或使用安装器生成的投影。当前环境没有 Claude Code 可执行文件，因此原生插件方式只完成了清单与静态结构验证，不声称真实加载通过；需要自包含跨宿主安装时，以安装器生成的投影为准。

Hermes 没有约定自动发现的项目级 Skill 目录。若希望由项目维护源码，请按 Hermes 官方说明在其 home 目录的 `config.yaml` 中配置 `skills.external_dirs`。安装器会尊重 `HERMES_HOME`，Windows 下也识别 `LOCALAPPDATA`；它不会悄悄修改宿主配置，因此 `--agent hermes --scope project` 会在写入前明确失败。

## 安装

前置条件为 Python 3.10 或更高版本。先查看不写入的完整计划：

```powershell
python .\install-skill.py --source . --agent all --scope user --dry-run --json
```

把全部宿主安装到隔离的用户级目录：

```powershell
python .\install-skill.py --source . --agent all --scope user
```

只安装用户实际使用的宿主时，重复指定 `--agent`：

```powershell
python .\install-skill.py --source . --agent codex --agent claude-code --agent opencode --scope user
```

远程安装器会下载本仓库的 `main` 分支；执行前应先检查脚本：

```powershell
(Invoke-WebRequest 'https://raw.githubusercontent.com/zxy19960316/engineering-research-copilot/main/install-skill.py').Content | python - --agent all --scope user
```

项目级示例不包含 Hermes：

```powershell
python .\install-skill.py --source . --agent codex --agent claude-code --agent opencode --agent openclaw --agent github-copilot --scope project --project-root D:\path\to\project
```

安装器先验证九个 Skill、共享参考和两份原生插件清单，再在隐藏暂存区生成全部自包含投影。默认拒绝覆盖；确认升级时显式加 `--upgrade`，已有副本会先备份，全部投影成功后才删除备份，失败则回滚。`--source .` 模式不访问网络。除引用位置、生成的共享副本/清单以及 Hermes 的短描述外，文件保持与规范源一致；复制的共享参考逐字节一致，且清单记录全部 SHA-256 和空的权限变更列表。

安装 Skill 只提供工作流指令，不会自动安装模型、论文语料、数据库或后台服务，也不授权执行科研任务。高风险、安全相关、受监管或专业统计结论仍需领域专家复核。
