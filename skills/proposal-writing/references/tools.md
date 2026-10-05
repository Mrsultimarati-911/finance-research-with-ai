# 工具与独立使用

基本执行依靠宿主的文本、文件与公开搜索能力，无运行依赖、无必需MCP或其他科研Skill。可直接处理用户给定材料，不联网也能做有限范围的框架/修订。Python 3.10+仅用于可选结构化检查器，使用标准库。

```powershell
python -B -X utf8 scripts/check_project.py project-contract.json
```

JSON字段：`questions`为 `{id,text}` 数组；`sources`为 `{id,read_range}` 数组，读取范围为 `full_text/abstract/metadata/user_material`；`claims`包含 `{id,kind,source_ids,requires_full_text}`，kind为 `literature_fact/user_fact/hypothesis/analysis`；`datasets`包含 `{id,status}`，status为 `available/permission_pending/unknown`；`tasks`包含 `{id,question_ids,dataset_ids,conditional}`；可选 `materials` 为 `{name,status,marker}`，未知/待授权须marker为待补；可选 `template_sections/draft_sections` 必须保持一致及 `untouched_before/untouched_after` 映射用于局部修改范围核对。

检查器验证标识引用、实体结论至少有摘要/全文、团队事实须用户材料、需要全文的论断不能仅引摘要、数据未确认须条件化、总问题是否被任务覆盖、缺失项与范围约束。输出issues和passed，失败退出2，成功0。它不能验证资料真假、实际因果识别、所有自然语言是否严谨，也不能代替人工审查；普通任务不用强制建JSON台账。

输入根节点必须为对象，各集合必须为对象数组。标识为非空白且集合内唯一的字符串，问题须有非空白text；引用字段必须为字符串标识数组，requires_full_text/conditional若提供必须为JSON布尔值。materials的name须非空白，status同样限available/permission_pending/unknown。template_sections与draft_sections须成对提供非空标题数组；untouched_before与untouched_after须成对提供“标题—原文”映射，逐字比较。不符合字段类型也不能通过；输入文件错误返回input_error和退出码2。结果以JSON输出到终端，不改写输入。

迁移复制完整Skill目录；需要自动发现时按宿主规则安装。此交付不安装到全局、不自动配置、也不要求其他Skill。输出中文 Markdown；交付目录由用户指定。
