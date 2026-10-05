# 来源、许可与改编

本包局部参考 [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills/tree/50851efc109c981be6cdc1ed5171a2eaa739d20a) 的方法，锁定提交为 50851efc109c981be6cdc1ed5171a2eaa739d20a。

## 方法来源

- [多源搜索流程](https://github.com/Yuan1z0825/nature-skills/blob/50851efc109c981be6cdc1ed5171a2eaa739d20a/skills/nature-academic-search/references/workflows/wf1-multi-source-search.md)。
- [身份与重复记录核对](https://github.com/Yuan1z0825/nature-skills/blob/50851efc109c981be6cdc1ed5171a2eaa739d20a/skills/nature-academic-search/references/dedup-engine.md)。
- [Crossref适配方法](https://github.com/Yuan1z0825/nature-skills/blob/50851efc109c981be6cdc1ed5171a2eaa739d20a/skills/nature-academic-search/mcp-server/sources/crossref.py)。
- [学术查询方法](https://github.com/Yuan1z0825/nature-skills/blob/50851efc109c981be6cdc1ed5171a2eaa739d20a/skills/nature-academic-search/scripts/academic_search.py)。

所用方法材料在锁定提交采用 Apache-2.0，完整文本保留于 [LICENSE](LICENSE)。上游入口的许可标记与根许可证不同，本包重新编写入口，不复制该入口。上游权利与适用声明保留，本包新增内容采用 Apache-2.0。

## 本地实现与公开范围

入口、支持资料和Python适配由本项目重新实现或局部改编。公开适配保留文献发现、标识查询、引用候选、摘要与出版日期；重复记录、版本和结束条件由实际材料及阅读者判断。

本地PDF读取方法参考本项目自写的 paper-deepread 逐页读取、哈希及稀疏文本信号，在本包独立实现；不要求安装该 Skill，也不复制其理论或讨论材料。PDF、DOCX与XLSX读取库为可选依赖，不打包其源码、宿主运行时或其他 Skill。

本包软件许可不覆盖用户论文、图表、办公文档、网站、API摘要或第三方数据。来源内容的权利由原来源决定，本包不附带账号、授权、密钥或全文资料。
