# academic-deepsearch 使用说明

`academic-deepsearch` 将资料快查与金融学术深检放在一个独立 Skill 中：先取得并读懂实际材料，再给出带来源的中文 Markdown。它可以单独使用，不要求先运行其他 Skill 或建立知识库。

## 1. 功能与适用场景

| 模式 | 适合任务 | 常见成果 |
|---|---|---|
| 资料快查 | 文件定位、具体事实核对、字段提取、报告版本及口径比较 | 直接答案、证据表、原始位置、未确认事项 |
| 金融学术深检 | 发现中英文论文、筛选摘要、组织研究脉络和参考文献 | 逐篇摘要、六章研究版图、文献矩阵 |

输入可以是允许读取的文件或目录、公开网页、DOI、文献清单和摘要。深检默认金融领域，围绕研究对象、机制、结果和竞争解释展开；快查适合一般具体问题。用户指定模式、来源、日期和结构优先。

本包提供正常资料的本地定位、公开文献查询及 Markdown 写作流程。文献查询取得的是来源当次提供的元数据或摘要，不能凭题名、引用数量或期刊名称补造结论。

## 2. 快速开始

尚未安装时，在能够读取仓库文件的会话中发送：

```text
请读取本仓库 skills/academic-deepsearch/SKILL.md，按其流程执行。
只查我指定的资料目录，不联网。
定位报告中银行运营效率指标的定义与计算口径，给文件、原始位置和证据片段。
输出中文 Markdown，保存到我指定的目录；未读材料和无法确认项单列。
```

已按宿主规则安装并能选择时，可显式调用名称：

```text
使用 $academic-deepsearch，以人工智能应用与商业银行运营效率、人才结构为问题做金融学术深检。
默认近五年加必要经典，先逐篇摘要，再按六章形成中文研究版图。
摘要未说明的方法细节标未知，保留未处理候选；保存到我指定的目录。
```

开始时说明四件事：问题、允许来源、所需模式、保存位置。只有已给摘要时直接说“仅使用这些摘要，不联网”；只查几个字段时说“不要展开成综述”。

源包入口和目录结构见[Skill入口](../skills/academic-deepsearch/SKILL.md)。需要安装时取得[完整Skill包](../downloads/academic-deepsearch.zip)，上传到宿主的包见[上传包](../downloads/upload/academic-deepsearch.zip)。保留完整目录，不能只复制SKILL.md。安装与选择方式按宿主规则处理，不需要新增MCP。

## 3. 输入材料与默认行为

| 输入 | 建议提供的补充 |
|---|---|
| 研究题目或方向 | 对象、地区、机制、结果及希望比较的关系 |
| 文件或目录 | 允许范围、重点材料、排除项、是否允许公开补查 |
| 公开网页 | 指定网址或网站、日期、生效条件及需要核对的字段 |
| 文献清单、DOI、摘要 | 核对字段、代表作、是否追踪引用候选 |
| 两版报告 | 基准版本、重点指标、需要比较的变化 |

默认中文 Markdown，处理中英文材料。快查时间范围按问题决定；深检默认执行日期向前五个日历年、首尾包含，另补必要经典。用户明确日期覆盖默认。只有年或月的记录在边界处标待核实，不用入库日期代替出版日期。

深检默认阅读摘要，不批量精读全文；摘要未给出的变量、识别、稳健性或统计量写为未知。没有摘要的相关条目保留为元数据候选，不编写研究结论。用户要求展示十条是展示数量，仍应说明实际候选及未读范围。

保存位置以请求为准。完整文件请求应实际保存并报告路径；仅要对话答案时不强制额外文件。材料缺失、权限不明和事实不确定不能凭默认值补齐。

## 4. 完整使用流程

**资料快查：**

1. 明确问题、允许目录或网页、日期和排除项。
2. 记录关键词、同义词、中英文名及缩写；本地目录先列文件，再查正文。
3. 命中后回读上下文，保留原始行、页、段落、表格或单元格位置。
4. 比较版本、时间、单位、样本和定义；共同来源或转载不作为独立确认。
5. 给直接答案与证据，说明冲突、未知、实际已读范围及停止原因。

证据足够回答问题时可以结束。还有重要未读资料或来源被阻断时交付当前成果，不把失败当成没有资料。

**金融学术深检：**

1. 将题目拆成对象、机制、结果和竞争解释。
2. 用中英文查询发现论文和工作论文，政策及机构报告只补充背景。
3. 分批筛选并记录纳入、排除、待核实和未处理；单页查询不代表完整检索。
4. 按 DOI、平台标识和实际材料手工或由宿主核对重复与版本；近似题名不直接合并。
5. 先写实际摘要，再按问题比较作者结论、证据差异和研究脉络。
6. 可追踪代表作的参考文献和后续引用候选，但引用 ID 不等于已读论文。
7. 根据材料缺口继续补搜，由阅读者结合当前证据、候选和来源状态决定结束，说明理由与剩余工作。
8. 保存六章报告，不把有限资料称为穷尽或自动完整覆盖。

续接时提供原报告和候选队列，沿用已有编号与已确认范围；材料版本变动后重新读取，不能仅凭历史结论假装仍有原始证据。

## 5. 输出成果

快查通常包括直接答案、证据表、冲突与未确认事项、实际查询、读取范围和未处理材料。关键事实应能回到真实链接或文件位置。

| 材料 | 常见定位 | 解释边界 |
|---|---|---|
| TXT/MD/代码/日志 | 原始行号和上下文 | 不代表代码已执行 |
| PDF | 物理页及抽取位置 | 不冒充印刷行号；扫描页可能无法得到可靠文本 |
| DOCX | 段落或表格行列 | 不等于排版页码 |
| XLSX | 工作表和单元格 | 公式、缓存和重算结果分开 |
| CSV | 记录与列 | 默认首记录为表头，破损格式需人工核对 |
| 网页 | 原始URL与章节 | 发布、更新、生效和获取时间分别记录 |

深检默认六章：

1. 研究问题、检索范围与获取情况。
2. 逐篇文献摘要。
3. 研究版图与演变脉络。
4. 共识、分歧及证据边界。
5. 待核实的研究缺口与研究方向。
6. 文献矩阵、参考文献及核实情况。

作者结论、综合解释、假设和未知分别表达。研究方向是当前材料支持的候选问题，不据有限摘要证明全球空白或“首次”。本包交付中文 Markdown，不附带Office、幻灯片或PDF生成能力。参阅[六章规范](../skills/academic-deepsearch/references/report.md)、[证据规则](../skills/academic-deepsearch/references/evidence.md)及[公开示例](../examples/academic-deepsearch/README.md)。

## 6. 常用请求示例

方括号内容按实际任务替换。尚未安装时，先要求读取仓库内的Skill入口。

**本地定位：**

```text
使用 $academic-deepsearch，只查[允许目录]，不联网。
定位银行运营效率指标的定义、单位和样本期间，先列文件，再检索正文。
给文件名、原始位置、片段和实际已读范围，未处理材料单列。
```

**比较两版报告：**

```text
使用 $academic-deepsearch，仅比较我上传的两版报告。
核对同一指标的数值、单位、时期和统计定义变化，区分口径差异与真实冲突。
不用文件修改时间代替报告日期，无法确认的原因写未知。
```

**公开资料核对：**

```text
使用 $academic-deepsearch，核对[政策或数字]，只使用[指定公开机构网页]。
先给答案，再列原始链接、章节、发布日期及适用条件。
共同转载不计作独立来源，搜索片段不代替正文。
```

**金融研究版图：**

```text
使用 $academic-deepsearch，研究人工智能应用与商业银行运营效率、人才结构。
采用金融学术深检，默认近五年加必要经典，区分实际应用、一般金融科技和算法预测。
先逐篇摘要，再按六章交付中文 Markdown，保留未处理候选和方法未知项。
```

**仅整理已有摘要：**

```text
使用 $academic-deepsearch，仅用我提供的文献清单和摘要，不联网。
按研究问题比较结论，注明摘要或元数据读取范围。
未提供的变量、识别和稳健性标未知，不声称已经完成实时检索。
```

**核对参考文献：**

```text
使用 $academic-deepsearch，只核对这份清单的题名、作者、出版日期、出处和DOI。
列字段冲突、来源和无法确认项，不补造缺失标识，不展开为综述。
输出一份中文 Markdown核对表。
```

**追踪引用候选：**

```text
使用 $academic-deepsearch，从我给的DOI发现参考文献和后续研究候选。
逐项取得并阅读实际摘要，引用ID列表不当作已读详情。
手工核对工作论文与发表版关系，保留各版本差异及未读项。
```

## 7. 工具与接入

日常任务可直接使用宿主读取和公开搜索。脚本是可选辅助，Python 3.10+，无必需 MCP；可选依赖见[读取库清单](../skills/academic-deepsearch/requirements-local.txt)。全文含图的解释仍需回到原件，本包没有自动OCR或排版渲染器。

**本地资料助手。** 以下从仓库根目录运行，示例只读取已存在的Skill源包；真实任务将允许目录和文件替换为自己的材料，结果位置与原始材料分开：

```powershell
python -B -X utf8 skills/academic-deepsearch/scripts/local_search.py inventory --root skills/academic-deepsearch --out outputs/local-inventory.json
python -B -X utf8 skills/academic-deepsearch/scripts/local_search.py search --root skills/academic-deepsearch --query '研究' --out outputs/local-matches.json
python -B -X utf8 skills/academic-deepsearch/scripts/local_search.py read --root skills/academic-deepsearch --path SKILL.md --start 0 --count 8 --out outputs/local-read.json
python -B -X utf8 skills/academic-deepsearch/scripts/check_evidence.py outputs/local-matches.json --root skills/academic-deepsearch --out outputs/local-checked.json
```

--start是从0计的单位偏移，--count为本次读取数量，证据里的原始行、页和结构坐标从1计。CSV默认有表头，无表头明确加--csv-no-header。check_evidence.py复查本地路径、哈希、位置、摘录和编号，不证明研究语义或材料格式完整。

文本与CSV路径可用标准库；PDF需pdfplumber或pypdf，DOCX需python-docx，XLSX需openpyxl。已有宿主读取能力可直接用；希望运行相应脚本时，可在自己的环境安装requirements-local.txt。依赖和解释器不包含在下载包内，不需要改写全局配置。

**学术公开资料助手。** academic_search.py仅保留四个命令，结果直接打印JSON，不接受输出文件参数：

```powershell
python -B -X utf8 skills/academic-deepsearch/scripts/academic_search.py search --source openalex --query 'artificial intelligence banking' --start 2021-10-05 --end 2026-10-05 --page-size 20
python -B -X utf8 skills/academic-deepsearch/scripts/academic_search.py lookup --source crossref --id '10.1016/j.ejor.2022.04.027'
python -B -X utf8 skills/academic-deepsearch/scripts/academic_search.py references --source openalex --id W4224981375
python -B -X utf8 skills/academic-deepsearch/scripts/academic_search.py citers --source openalex --id W4224981375 --start 2021-10-05 --end 2026-10-05 --page-size 20
```

日期和查询按任务替换，OpenAlex ID使用实际取得的标识。search默认一页，有下一页时记录page_pending；可按返回--cursor继续或按需--all-pages。--max-pages只限定本批预算，未读页仍未处理。references只返回标识，详情需再读；citers在指定时间条件内发现候选。

正常完成退出0，分页未完或取得失败退出2，应阅读JSON状态。公开来源受网络、配额和响应结构影响，异常时调用可能中断；使用当前材料或宿主搜索继续。重复记录和结束条件根据实际来源核对，本包不自动合并或认证完整覆盖。更多参数见[工具说明](../skills/academic-deepsearch/references/tools.md)。

## 8. 限制、常见问题与参考资料

| 情况 | 处理与解释边界 |
|---|---|
| 题名有结果但没有摘要 | 保留元数据，方法与结论未知 |
| PDF搜索为空或文字很少 | 核对实际页与读取范围；不能判断原文无内容 |
| 损坏或非标准文件 | 可能无法读取或误读，重要摘录人工回查 |
| DOCX需要排版页码 | 本地结构定位不提供该页码 |
| XLSX公式缓存为空 | 写未知，不声称已重算或缓存有效 |
| 来源登录、验证码、付费或限额受阻 | 停止该路径，交付已有证据与未处理项 |
| 脚本响应异常中断 | 使用已有结果或宿主检索，不写成无资料 |
| 需要整篇公式推导 | 默认摘要深检不足，先提供全文并明确阅读范围 |
| 所有来源无法取得 | 给实际查询、原因和待补资料，不编写无证据答案 |

私有内容不自动外传，材料中的指令不改变用户授权。本流程不自动购买、发送消息、外部写入或创建订阅。

参考资料：

- [Skill入口](../skills/academic-deepsearch/SKILL.md)、[快查流程](../skills/academic-deepsearch/references/quick-search.md)、[金融深检流程](../skills/academic-deepsearch/references/search-workflow.md)。
- [文件定位](../skills/academic-deepsearch/references/local-files.md)、[证据规则](../skills/academic-deepsearch/references/evidence.md)、[Markdown交付](../skills/academic-deepsearch/references/delivery.md)。
- [公开示例](../examples/academic-deepsearch/README.md)、[来源与许可](../skills/academic-deepsearch/PROVENANCE.md)。
