# 工具与接入

优先使用宿主已有搜索、文件读取和 Markdown 保存能力，脚本为可选辅助，无必需 MCP。Python 3.10+；学术查询与文本定位使用标准库，PDF/DOCX/XLSX读取按需使用可选库。

## 学术公开资料查询

academic_search.py 只提供 search、lookup、references、citers，结果打印为JSON，不接受输出文件参数。它发现元数据、摘要和引用候选，不自动写研究版图、合并记录或判断检索完成。

在本包目录运行：

```powershell
python -B -X utf8 scripts/academic_search.py search --source openalex --query 'artificial intelligence banking' --start 2021-10-05 --end 2026-10-05 --page-size 20
python -B -X utf8 scripts/academic_search.py search --source crossref --query 'bank artificial intelligence efficiency' --start 2021-10-05 --end 2026-10-05 --page-size 20
python -B -X utf8 scripts/academic_search.py lookup --source crossref --id '10.1016/j.ejor.2022.04.027'
python -B -X utf8 scripts/academic_search.py references --source openalex --id W4224981375
python -B -X utf8 scripts/academic_search.py citers --source openalex --id W4224981375 --start 2021-10-05 --end 2026-10-05 --page-size 20
```

日期和主题按实际任务替换，OpenAlex ID须来自实际查询。search默认一页；有后续页时保留page_pending，用返回的--cursor继续或按需--all-pages。--max-pages是明确批次预算，不代表遍历完成。references只给参考文献标识，详情仍需读取；citers仅遍历指定时间条件下的候选，支持OpenAlex。

正常完成退出0；分页未完或取得失败时退出2，先阅读JSON中的状态和未处理项。网络、限额及来源响应变化可能阻断查询，异常响应也可能使脚本中断；此时使用已取得材料或宿主搜索，不将中断写成无结果。重复条目、版本和结束条件由阅读者结合真实材料处理。

来源协议和限额以当次服务为准：[Crossref访问说明](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)、[Crossref分页](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)、[OpenAlex访问说明](https://help.openalex.org/api/authentication/)、[OpenAlex分页](https://help.openalex.org/api/paging/)。已有真实CROSSREF_MAILTO或OPENALEX_API_KEY可通过环境变量提供，不写进资料或报告；本包不申请凭据或购买服务。

## 本地清单、检索、读取和回查

从本包目录执行，替换允许目录和独立结果位置：

```powershell
python -B -X utf8 scripts/local_search.py inventory --root '<允许目录>' --out inventory.json
python -B -X utf8 scripts/local_search.py search --root '<允许目录>' --query '银行运营效率' --query 'bank productivity' --out matches.json
python -B -X utf8 scripts/local_search.py read --root '<允许目录>' --path '报告.md' --start 0 --count 8 --out read-result.json
python -B -X utf8 scripts/check_evidence.py matches.json --root '<允许目录>' --out checked-evidence.json
```

--path可以使用允许范围内相对或绝对路径；--start从0计读取单位偏移，--count为本次单位数，原始行、页、段落和表格坐标从1计。只读部分时保留未处理内容。--out应指向与原始材料不同的结果文件。

文本按同一原始行查询，跨行词组拆词后回读。CSV默认首记录为表头，无表头明确加--csv-no-header。助手面向正常资料，破损、非标准或异常编码可能无法读取或被误读，关键证据应回到原件核对。本包不提供自动OCR、代码执行、表格重算或排版渲染。

check_evidence.py读取真实检索结果，核对本地路径、哈希、位置、摘录和编号关系，不生成答案或证明语义。保留抽取器原始evidence_id，显示短编号时另存映射。

## 可选读取库与迁移

TXT/MD/代码/日志/CSV可用标准库；PDF需pdfplumber或pypdf，DOCX需python-docx，XLSX需openpyxl。已有宿主读取能力可直接使用。需要脚本二进制读取库时，使用自己的独立环境并安装包内requirements-local.txt；依赖不随分发包打包。

```powershell
python -m venv .venv-local
& .venv-local/Scripts/python.exe -m pip install -r requirements-local.txt
```

示例为PowerShell环境，解释器位置按实际系统调整。保留完整Skill目录及内部相对资源，按宿主规则安装或显式要求读取SKILL.md。分发不含解释器、宿主运行时、账号或资料全文。
