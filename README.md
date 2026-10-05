# finance-research-with-ai

让 AI 工具参与金融科研的日常工作：读懂论文、整理资料、查找文献，并把研究问题写成有依据的方案。

[快速开始](#2-快速开始) · [安装方式](#3-安装方式) · [技能索引](#4-技能索引) · [使用示例](#5-使用示例) · [方法来源](#6-方法来源)

## 1. 项目简介

金融研究需要反复处理原文、公式、变量、数据条件与论证。这些工作可以借助 AI 加快，但研究判断仍需要清楚的证据和边界。本项目将金融科研中的四类任务整理为可复用的 Skill，让智能体按照明确的工作流程交付可阅读、可回查的成果。

四个 Skill 的目标各不相同，可以单独使用，也可以搭配。例如，先用 `academic-deepsearch` 梳理文献，挑出关键论文交给 `paper-deepread`，再用 `proposal-writing` 整理研究方案；`wechat-summary` 可以补充政策、行业讨论与研究背景。没有固定的运行顺序，也不要求安装其他科研技能、建立知识库或使用 Zotero。

默认使用中文 Markdown。支持阅读中文和英文材料；研究假设、作者观点、来源事实与综合分析分别表达。未知数据权限、团队条件和未实施的检验不能写成既定事实。

```text
finance-research-with-ai/
├── README.md                 项目入口
├── skills/                   四个技能及必要工具、支持资料
├── guide/                    每项技能的详细使用说明
├── examples/                 使用请求、自建输入与成果示例
├── downloads/                完整目录包
│   └── upload/               根级 SKILL.md 上传包
├── LICENSE                   项目新增内容的许可证
└── THIRD_PARTY_NOTICES.md     第三方来源与适用许可
```

## 2. 快速开始

安装后，直接给出材料和任务即可。也可以明确说“使用 `技能名`”。

| 想做什么 | 可直接复制的请求 |
|---|---|
| 读懂一篇金融论文 | 使用 paper-deepread 精读这篇 PDF，结构采用“全文总览—变量拆解—理论模型—结果分析—结论”。详细解释关键公式与变量，先输出中文笔记，随后独立开展答疑。 |
| 整理公众号主题资料 | 使用 wechat-summary，收集中国金融四十人论坛和金融时报近一年关于人工智能与金融的公开图文，先逐篇摘要，再综合主题与金融研究背景。 |
| 查资料与梳理文献 | 使用 academic-deepsearch，围绕人工智能应用与商业银行运营效率、人才结构，检索近五年及必要经典文献，先逐篇摘要，再整理研究脉络和文献矩阵。 |
| 形成研究方案 | 使用 proposal-writing，围绕人工智能应用与商业银行运营效率先提出研究框架，列明研究问题、机制、方法和数据条件，缺少团队基础或权限的部分标“待补”。 |

在 Codex 中可写 `$paper-deepread`、`$wechat-summary`、`$academic-deepsearch`、`$proposal-writing`；Claude Code 中使用 `/paper-deepread` 等命令。其他宿主可以选择技能后描述任务。

还没有安装时，可在有本地文件工具的智能体中明确请求：“读取本仓库 `skills/<技能名>/SKILL.md`，按其流程处理下面的任务。”完整技能目录需要与入口一起保留。

## 3. 安装方式

先克隆仓库，也可通过 GitHub 的 **Code → Download ZIP** 下载后解压：

```powershell
git clone https://github.com/Mrsultimarati-911/finance-research-with-ai.git
Set-Location finance-research-with-ai
```

下列复制命令从仓库根目录执行。目标存在同名技能时，先确认是否需要替换，避免覆盖自己的修改。四个技能可以一起安装，也可以只复制需要的目录。

### Claude

Claude Code 的个人目录是 `~/.claude/skills/`，项目目录是 `.claude/skills/`。例如，安装到当前项目：

```powershell
New-Item -ItemType Directory -Force .claude/skills | Out-Null
Copy-Item -Path ./skills/* -Destination .claude/skills -Recurse
```

随后使用 `/paper-deepread` 等命令。目录规则见 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)。

Claude 网页版或桌面聊天中的技能，通过 **Customize → Skills** 上传普通目录包并启用。下载本项目 [downloads 中的对应 ZIP](downloads/)，保留其中单层 `<技能名>/SKILL.md` 及附属资源。[上传说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude)。网页环境不能直接运行本机 Windows 的 STDIO MCP；公众号阅读需要宿主能访问相应工具。

### Codex

项目技能放入 `.agents/skills/`；个人技能可放入 `~/.agents/skills/`：

```powershell
New-Item -ItemType Directory -Force .agents/skills | Out-Null
Copy-Item -Path ./skills/* -Destination .agents/skills -Recurse
```

用 `$academic-deepsearch` 等名字选择技能，或在 `/skills` 中查找。未出现时重新打开会话。详见 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills)。

### WorkBuddy

进入技能页，选择 **添加技能 → 上传技能**，从 [根级上传包](downloads/upload/) 逐项选择 ZIP；安装后在已安装列表启用，并在对话框选择技能。若当前客户端提示包结构不兼容，可尝试 [普通目录包](downloads/) 并按官方导入提示处理。

WorkBuddy 的界面和格式要求可能随客户端变化；这里提供本地导入，不涉及开放平台上架。[官方技能说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。

### Trae

按 TRAE CN 的目录规则，将完整技能目录放入项目 `.trae/skills/`：

```powershell
New-Item -ItemType Directory -Force .trae/skills | Out-Null
Copy-Item -Path ./skills/* -Destination .trae/skills -Recurse
```

也可通过 **设置 → 技能与命令** 导入 [根级上传包](downloads/upload/)，在对话中写“使用 paper-deepread 技能……”。不同地区客户端的路径或导入界面可能不同，请按对应官方说明处理。[TRAE CN 技能说明](https://docs.trae.cn/ide_skills)。

`wechat-summary` 还需创建 Python 环境并接入本地 MCP；安装 Skill 本身不会自动安装依赖或连接服务。三个接口、启动和配置示例见 [公众号技能指南](guide/wechat-summary_README.md)。其他技能优先使用宿主已有文件、网页和文本工具，辅助 Python 脚本按需使用。

## 4. 技能索引

| 技能 | 核心用途 | 主要成果 | 详细说明 |
|---|---|---|---|
| `paper-deepread` | 论文精读、变量与公式解释、原文答疑、研究构思延展 | 独立精读笔记；方向明确后形成论文延展稿 | [使用指南](guide/paper-deepread_README.md) · [入口](skills/paper-deepread/SKILL.md) |
| `wechat-summary` | 指定公众号与主题的公开图文收集和整理 | 逐篇摘要、主题综合、金融研究背景及来源说明 | [使用指南](guide/wechat-summary_README.md) · [入口](skills/wechat-summary/SKILL.md) |
| `academic-deepsearch` | 资料快查、证据定位、金融文献发现和研究脉络整理 | 快查答案或六章文献报告、文献矩阵 | [使用指南](guide/academic-deepsearch_README.md) · [入口](skills/academic-deepsearch/SKILL.md) |
| `proposal-writing` | 框架、初稿、局部修改、补写及审查 | 研究框架、计划书草案、修改稿或审查建议 | [使用指南](guide/proposal-writing_README.md) · [入口](skills/proposal-writing/SKILL.md) |

访问可能受验证码、登录、付费、配额或页面变化影响；异常 API 返回和损坏文件也可能使读取受阻。元数据需结合原页核对，公开检索不能保证资料穷尽。每项技能的具体限制随指南说明。

## 5. 使用示例

案例展示任务、输入与实际成果；原始论文、公众号全文及内部科研材料不随仓库提供。图表请通过成果中的原始来源回查。

| 案例 | 看什么 | 入口 |
|---|---|---|
| 同一论文的四种精读结构 | 原文章节、研究逻辑、总览与详读、自定义结构如何组织同一材料；另有中文论文变量和公式解释、答疑及延展稿 | [精读案例](examples/paper-deepread/README.md) |
| 金融情绪因子公众号资料 | 逐篇摘要如何区分作者观点、原文证据和综合分析；如何保留来源与覆盖限制 | [公众号案例](examples/wechat-summary/README.md) |
| 多格式资料定位与银行 AI 文献 | 自建输入的定位、回查和来源比较；公开文献的摘要与研究脉络 | [检索案例](examples/academic-deepsearch/README.md) |
| 银行 AI 研究计划书 | 从框架到初稿，以及局部修改、补写和审查；未知条件如何标“待补” | [计划书案例](examples/proposal-writing/README.md) |

例如，论文笔记不仅说明“使用了中介检验”，还解释变量如何构造、每个系数对应什么量、计算使用什么口径。计划书则把“研究问题—理论机制—变量—方法—数据条件”连接起来，尚未开展的研究始终写为拟检验方案。

## 6. 方法来源

本项目来自将成熟科研 Skill 用于日常金融研究的需求。借鉴其证据组织和论证方法，再围绕金融变量、识别设计、统计解释及实际资料条件重新组织。公开入口、支持资料和工具按本项目任务编写或改编，使用本项目不要求先安装上游技能。

| 本项目技能 | 主要来源 | 金融领域的改编 |
|---|---|---|
| paper-deepread | nature-paper-card、nature-reader；theory-paper-reader | 四种可选笔记结构；金融变量、单位和经济量级；精读笔记与问题分离；讨论后形成研究设计。 |
| academic-deepsearch | nature-academic-search | 金融论文与工作论文优先；摘要未说明的信息保留未知；加入本地多格式定位和回查。 |
| proposal-writing | nature-proposal-writer / researchwrite | 面向金融和社科课题，检查识别、竞争解释、变量与数据条件；组织为五种模式。 |
| wechat-summary | weixin-articles-mcp | 改编公开图文读取与 Markdown 转换，配合公开候选检索、逐篇摘要和五章报告；音视频不纳入。 |

计划书写作保留“证据先于行文、论证先于章节”和局部修改边界，同时简化强制基础文件包、专家调度与评分流程。只给题目时先形成框架；明确要求完整初稿时直接起草。用户模板优先，团队成果和数据权限缺失时标“待补”。

感谢 [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) 的作者与贡献者、[Benny Wang 的 theory-paper-reader-skill](https://github.com/drbzw/theory-paper-reader-skill)，以及 [jj-cheng25/weixin-articles-mcp](https://github.com/jj-cheng25/weixin-articles-mcp) 的贡献者。

具体来源、锁定提交与修改说明保留在各技能的 `PROVENANCE.md`。项目新增内容采用 [Apache-2.0](LICENSE)，组件适用的 MIT 许可证和署名随包保留，详见 [第三方来源声明](THIRD_PARTY_NOTICES.md)。
