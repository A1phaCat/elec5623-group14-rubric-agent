# 离线冒烟结果

量表：`dataset/rubrics/engineering_report.md`。  
网关：只使用离线的 FixtureGateway（`fixture-descriptor-v2`），没有调用付费或在线模型。  
参数：`workers=1`，`k=5`。

这是泛化冒烟测试，不是人工一致率。程序能解析这些新文档，只说明输入管道还能用。Fixture 给出的分数和“充分性”是关键词启发式，不是真模型打分，不能当作评分已经泛化的证据。

这些文件是 Markdown，没有分页标记，所以解析页数都是 1。证据单元数是切块之后的总数。C3 是量表里的 Evaluation plan。`missing` 是否非空，看的是 C3 检索到的证据对照满分档描述之后，`top_band_coverage` 的缺失词列表。

10 份全部解析成功。

| 文件 | 解析页数 | 证据单元数 | C3 fixture 充分性 | C3 满分档 missing 是否非空 |
| --- | --- | --- | --- | --- |
| 01.md | 1 | 13 | partial | 是 |
| 02.md | 1 | 16 | partial | 是 |
| 03.md | 1 | 43 | partial | 是 |
| 04.md | 1 | 28 | partial | 是 |
| 05.md | 1 | 20 | partial | 是 |
| 06.md | 1 | 19 | partial | 是 |
| 07.md | 1 | 23 | insufficient | 是 |
| 08.md | 1 | 26 | partial | 是 |
| 09.md | 1 | 9 | partial | 是 |
| 10.md | 1 | 26 | partial | 是 |

`07.md` 的 C3 检索结果是空的，所以 fixture 把充分性标成 insufficient。这仍是启发式结果，不是人工判断。
