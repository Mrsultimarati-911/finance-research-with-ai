# paper-deepread 使用说明

将金融论文读清楚，逐步解释变量、公式和证据，再通过独立讨论形成研究构思。默认中文 Markdown，输入可为中文或英文论文。

## 快速开始

安装后可在 Codex 中使用 `$paper-deepread`，Claude Code 中使用 `/paper-deepread`，或明确说“使用 paper-deepread”。也可要求智能体先读取本仓库的 [SKILL.md](../skills/paper-deepread/SKILL.md)。安装步骤见 [项目首页](../README.md#3-安装方式)。

```text
使用 paper-deepread 精读我提供的 PDF。
采用“全文总览—变量拆解—理论模型—结果分析—结论”。
详细解释支撑变量构造、推导和关键结论的公式与图表。
先保存中文精读笔记到 outputs/我的论文/，随后独立开展答疑。
```

下载 [完整目录包](../downloads/paper-deepread.zip) 或 [根级上传包](../downloads/upload/paper-deepread.zip)。保留入口、references、scripts、agents 和许可证，不能只复制入口。

## 输入和默认行为

必需材料是一篇可读取的论文，PDF 优先；可补充附录、已有笔记或某个局部问题。可指定结构、重点、输出目录和文件名。

默认中文解释。已经明确结构时直接沿用；首次完整精读未选结构时，展示以下四种选择后等待决定：

| 结构 | 适合的阅读目标 |
|---|---|
| 原文章节 | 沿作者的章节和论证顺序阅读。 |
| 研究逻辑 | 重组为研究问题、机制、变量、设计与证据。 |
| 全文总览与逐章详读 | 先形成全文地图，再逐章深入。 |
| 自定义 | 按读者给定的标题、顺序和关注点组织。 |

没有正式模型、中介变量或因果识别的论文，按实际内容解释，不补造相应模块。

## 完整流程

1. 确认正文、图表和附录的实际可读情况，核对论文信息。
2. 按所选结构完整写笔记，解释符号、构造步骤、数据口径、统计结果和作者结论。
3. 笔记交付后，在对话中另给 3–5 个讨论入口。问题和研究启发独立于精读笔记。
4. 围绕原文追问、补充推导、讨论竞争解释或研究思路。已有笔记可以直接续接。
5. 读者明确延展方向并要求成文后，整理 `论文延展.md`，写清机制、假说、变量、数据条件和检验计划。

没有选定方向时先讨论候选，不将示例方向冒充读者的选择。示范计算使用假定数据时会明确标注；拟开展检验不会写成已有结果。

## 输出和检查

完整流程通常产生 `精读笔记.md` 和 `论文延展.md`。局部问题直接在对话中回答；讨论记录按要求另存。默认保存到工作区 `outputs/<论文简称>/`，用户指定目录优先。

检查时重点看：关键观点能否回到原文位置；变量单位、时间、分母和标准化是否清楚；作者结论与解释是否分开；缺失附录是否标明；延展稿中的研究假设和数据条件是否明确。

## 常用请求

```text
使用 paper-deepread，按原文章节精读这篇英文论文，输出完整中文解释。
```

```text
使用 paper-deepread，按研究逻辑重组这篇论文，重点解释识别策略和竞争机制。
```

```text
使用 paper-deepread，只解释式（2）。逐步说明每个符号、权重和分母，再用假定数据计算。
```

```text
使用 paper-deepread，继续已有笔记，只讨论表 3 的交互项和经济量级，不重写整篇笔记。
```

```text
使用 paper-deepread，核对这篇论文中 X、Y、控制变量与中介变量的实际角色，未定义的口径不要按惯例补齐。
```

```text
使用 paper-deepread，按我们已经选定的方向整理为论文延展.md，数据尚未取得的部分写为条件方案。
```

## 可选工具

宿主已有 PDF 读取和图片查看工具优先。辅助脚本使用 Python 3.10+，提取需要 pdfplumber 或 pypdf，渲染需要 pypdf、Pillow 和 Poppler 的 `pdftoppm`。

从仓库根目录执行：

```powershell
python -B -X utf8 ./skills/paper-deepread/scripts/prepare_pdf.py ./我的论文.pdf --out ./outputs/我的论文/_source
python -B -X utf8 ./skills/paper-deepread/scripts/render_pdf.py ./我的论文.pdf --page 4 --out ./outputs/我的论文/assets/page_04.png
python -B -X utf8 ./skills/paper-deepread/scripts/render_pdf.py ./我的论文.pdf --page 4 --bbox 40 60 510 430 --out ./outputs/我的论文/assets/table_01.png
python -B -X utf8 ./skills/paper-deepread/scripts/check_markdown.py ./outputs/我的论文/精读笔记.md
```

脚本读取的 PDF、页码和裁剪区域须替换为实际值。原页图像需要查看；提取文本不能代替公式和表格核对。工具细节见 [工具说明](../skills/paper-deepread/references/tools.md)。

## 已知限制与参考

扫描件、损坏文件、特殊字体和缺失附录可能使部分读取受阻。出版商登录或付费页面也可能限制补充资料。只取得部分内容时，成果注明实际读取和缺口；不根据标题补写正文。

本仓库不提供原始论文和未明确再分发权限的原图。实例保留文献来源，可回到原文查看。

- [使用案例](../examples/paper-deepread/README.md)
- [工作流程](../skills/paper-deepread/references/workflow.md)
- [来源与修改说明](../skills/paper-deepread/PROVENANCE.md)
- [许可证](../skills/paper-deepread/LICENSE)
