# 八种本地资料的快查

任务：从MD、DOCX、XLSX、CSV、PDF和代码中找出AI、银行运营效率与人才结构的相关信息，比较版本并定位公式。日期：2026-10-05。

示例请求：“用 academic-deepsearch，只读 inputs 内八份材料，比较运营效率初稿与修订稿、找出客户响应耗时与人才资料，解释工作簿公式能否直接作为结果，用中文Markdown给出答案与原文定位。”

输入均为作者自制的虚构小材料，不代表现实银行数据或金融事实：

- [主题与说明](inputs/topic.md)、[初稿指标](inputs/metrics_old.md)、[修订稿指标](inputs/metrics_new.md)
- [研究笔记DOCX](inputs/research_note.docx)、[数据XLSX](inputs/research_data.xlsx)
- [CSV记录](inputs/records.csv)、[混合文字与扫描页PDF](inputs/mixed_report.pdf)、[代码文本](inputs/analysis.py)

成果：

- [详细快查答案](results/详细快查答案.md)：版本比较、公式缓存、隐藏行及扫描页定位。
- [资料快查示例](results/资料快查示例.md)：简洁中文Markdown报告与资料定位表。

输入中的18%与12%属于初稿与修订稿文字差异，10分钟与8分钟只能作描述比较。工作簿公式缓存缺失、人数资料尚未核实；42来自自制PDF扫描页和隐藏工作表，不能补成现实员工统计。公开副本调整了示例说明和文件路径，保留原有数值及材料限制。
