# Engineering Research Copilot

Engineering Research Copilot 是一个面向工科研究者的全流程 Agent Skill。它从用户当前阶段开始，在证据和权限边界内协助完成概念纠偏、文献核验、方向与方法比较、研究路线规划、科研主张审计、证据门控写作、独立多视角审稿，以及作者控制下的修改、复审和润色。

这个仓库发布的是一个轻量、可移植的 Skill 文件夹，不包含模型、论文语料库、数据库、后台服务或私有检索系统。它遵循开放的 [Agent Skills 规范](https://agentskills.io/specification)，详细规则按需从一层 `references/` 加载；需要核验最新文献或事实时，使用宿主 Agent 已有的学术检索或网络工具。

## 核心能力

- 从一句模糊想法、已有文献、研究计划、结果、提纲、草稿或审稿意见直接进入；
- 分开文献发现与身份、内容核验，明确元数据、摘要、全文和用户材料的证据层级；
- 比较主方向、相邻备选和迁移探索，并为高风险想法给出最小证伪检验；
- 按真实就绪度返回概念草图、路线准备方案或可执行路线，不把路线生成当作执行授权；
- 在写作前建立主张—证据关系，不虚构引文、数据、实验、结果、数值或结论；
- 先保留独立审稿视角和分歧，再综合问题，并由作者决定实质修改；
- 审计默认只读；文件写入、上传、下载、实验、仿真、训练、发表和外部沟通分别需要明确授权。

## 仅支持主动调用

本版本不提供被动触发方式。安装后必须由用户显式选择或输入 Skill 名称；普通对话不会授权 Agent 自动启用它。

| 宿主 | 主动调用方式 | 被动触发控制 |
|---|---|---|
| Claude Code | `/engineering-research-copilot <任务或材料>` | 安装器向宿主副本写入 `disable-model-invocation: true` |
| GitHub Copilot CLI | `/engineering-research-copilot <任务或材料>` | 安装器向宿主副本写入 `disable-model-invocation: true` |
| Codex CLI / IDE | `$engineering-research-copilot <任务或材料>`，或先运行 `/skills` 后选择 | `agents/openai.yaml` 设置 `allow_implicit_invocation: false` |
| ChatGPT 桌面端 | 输入 `@` 后选择 `engineering-research-copilot` | `agents/openai.yaml` 设置 `allow_implicit_invocation: false` |

Gemini CLI 当前的 Skill 激活工具只能由模型调用，不能保证“仅用户主动调用”，因此不列入这个严格主动调用版本的兼容范围。其他 Agent 即使能读取开放格式，也只有在明确支持上述调用控制时，才应视为完整兼容。

### 调用示例

Claude Code 或 GitHub Copilot CLI：

```text
/engineering-research-copilot 我只有一个模糊想法：用机器学习改进换热系统。请先纠正概念并收紧成可证伪的研究问题。
```

Codex CLI 或 IDE：

```text
$engineering-research-copilot 请核验这组论文，并区分主要支持、反证、局限和仍未解决的证据缺口。
```

也可以在调用后附上研究计划、数据说明、结果、论文草稿或审稿意见。Skill 会从材料当前所处阶段开始，不要求重走已经满足的流程。

## 一键安装

前置条件：已安装 Python 3。仓库自带的安装器只下载本仓库、拒绝覆盖已有目标，并在 Claude Code 和 GitHub Copilot 副本中加入各自支持的主动调用控制。以下命令把 Skill 安装到 Codex、Claude Code 和 GitHub Copilot CLI 的用户级目录。

PowerShell：

```powershell
(Invoke-WebRequest 'https://raw.githubusercontent.com/zxy19960316/engineering-research-copilot/main/install-skill.py').Content | python - --agent codex --agent claude-code --agent github-copilot --scope user
```

macOS / Linux：

```bash
curl -fsSL https://raw.githubusercontent.com/zxy19960316/engineering-research-copilot/main/install-skill.py | python3 - --agent codex --agent claude-code --agent github-copilot --scope user
```

只安装到一个 Agent 时，保留对应的一个 `--agent` 参数即可。将 `--scope user` 改为 `--scope project` 可安装到当前项目。远程命令会执行下载到的安装器；建议先在浏览器中检查 [`install-skill.py`](install-skill.py) 以及本仓库的 `SKILL.md`、`references/` 和 `scripts/`。

## 下载并手动部署

1. [下载仓库 ZIP](https://github.com/zxy19960316/engineering-research-copilot/archive/refs/heads/main.zip)，或克隆仓库：

   ```bash
   git clone --depth 1 https://github.com/zxy19960316/engineering-research-copilot.git
   ```

2. 解压后，在仓库根目录运行安装器。以下示例安装到当前项目，并显式指定本地源码，整个过程不访问网络：

   ```powershell
   python .\install-skill.py --source . --agent codex --agent claude-code --agent github-copilot --scope project
   ```

   ```bash
   python3 ./install-skill.py --source . --agent codex --agent claude-code --agent github-copilot --scope project
   ```

3. 安装器会把完整的 `skills/engineering-research-copilot/` 文件夹复制到目标目录；不要只复制 `SKILL.md`，运行时还需要其 `references/`、`scripts/` 和 `agents/`：

   | 宿主 | 用户级目录 | 项目级目录 |
   |---|---|---|
   | Codex | `~/.agents/skills/engineering-research-copilot/` | `<项目>/.agents/skills/engineering-research-copilot/` |
   | Claude Code | `~/.claude/skills/engineering-research-copilot/` | `<项目>/.claude/skills/engineering-research-copilot/` |
   | GitHub Copilot | `~/.copilot/skills/engineering-research-copilot/` | `<项目>/.github/skills/engineering-research-copilot/` |

   严格手动复制到 Claude Code 或 GitHub Copilot 时，还必须在目标副本的 `SKILL.md` frontmatter 中加入 `disable-model-invocation: true` 和 `user-invocable: true`；因此更推荐使用安装器。

4. 重新加载 Skill 列表或重启宿主，然后只使用上一节列出的主动调用方式。

## 包结构

```text
install-skill.py                         # 安装并应用宿主调用策略
skills/engineering-research-copilot/
├── SKILL.md              # 通用入口、路由、证据与权限边界
├── agents/openai.yaml    # Codex / ChatGPT 界面与显式调用策略
├── references/           # 按当前科研阶段加载的详细协议
└── scripts/              # 正式机器制品所需的离线确定性工具
```

安装 Skill 只提供工作流指令，不等于授权它写入文件、访问未提供的数据、执行科研任务或对外发布。高风险、安全相关、受监管或专业统计结论仍需领域专家复核。
