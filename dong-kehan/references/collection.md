# 增补与核验

## 当前范围

核验日期为2026-11-10（Asia/Shanghai）。`coverage.json` 是数量、渠道和缺口的唯一状态源。当前不是完整公众号历史。原生微信主页出现的“45篇原创内容”只是一项界面观察，不等于董科含本人署名的45篇，也不构成收集率分母。

资料更新默认使用作者官网、可读署名转载、公开索引和贡献者提交的正文。需要登录的采集由使用者另行决定；这个skill不启动爬虫、不更改微信或网络设置。

## 来源顺序与停止条件

1. 已公开的作者官网：核对页面署名、题名与内容；微信版本关系另外确认。
2. 带明确来源与作者栏的全文转载：记录“正文署名已核实”，保留微信入口与转载URL。
3. 搜索目录和他文提及：仅登记题名、发布账号、索引日期与来源，暂不归因或生成正文摘要。

同一公开入口出现登录、验证或读取失败后，记录结果并换独立来源；不循环重试，不修改微信、代理或账户设置。公开检索结果趋于重复时停止扩展，保留剩余缺口，而不是用重复转载制造“全量”。

## 数据字段

每行是一个JSON对象，字段由 `scripts/library.py validate` 检查：

- `id`：稳定唯一标识；不因更换来源而改变。
- `title`、`aliases`：原题与改题；未知原题应明确标记。
- `status`：`verified_self`、`verified_other`、`unresolved`、`official_supplement`、`user_supplied`。
- `byline`：实际看见的作者栏；未看见时为空数组。署名冲突用 `byline_claims` 并列记录。
- `wechat_url`：原文URL或null。清除分享跟踪参数，保留长链接的 `__biz/mid/idx/sn`；文内引用链接放 `other_wechat_links`，不误当本篇原文。
- `wechat_publication_date/reprint_date/website_date/index_date`：首发、转载、官网、索引日期分别记录；未知使用null。
- `sources`：来源URL、类型、核对内容和核验日期；原生界面观察使用 `native_ui_observation` 和确切的 `locator`，用户提供正文使用 `user_submission`、会话编号定位及本地 `path`，不虚构文章URL。`authorship_evidence_url` 指向确实包含署名证据的页面。
- `content_evidence`：`original_read`、`signed_reprint_read`、`index_only`、`mention_only`、`user_provided_body`。
- `full_text`：用户提供正文的相对路径、SHA256、`origin=user_provided` 与输入编号；路径限于 `references/user-provided`。原样保存，不把HTML实体或笔误静默改成别的文本。通过 `library.py text ID` 读取，正文也参与检索。
- `title_is_provisional`：缺原标题时必须为true；整理者拟题不是原题。`possible_match_ids` 仅提示可能的版本关系，不能据此合并记录。
- `summary/key_points/topics`：独立撰写的简短笔记，不封装整篇正文；只有题名或提及时，summary为空字符串、key_points为空数组。
- `notes`：证据边界、冲突、版本关系和下次待确认项。

先按规范化微信URL去重，再人工核对同题文章。相同标题可能是别人的借题发挥；同作者的中英文官网版本也可能不是新文章。

## 2026-11-10用户正文增补

用户提供编号1、2、3、5、6、7，共6段。编号5与6在去掉分段边界空白后逐字相等，只保留一份正文。编号3与既有融资记录合并，另外4份新增为 `user_supplied`。共保存5份全文，不增加6篇已核实本人公众号文章的统计。提交映射与正文哈希见 [submission.json](user-provided/20261110/submission.json)。

用户第2份与旧目录《什么样的人非创业不可》主题相近，但缺原标题和链接，暂列可能对应而不删除原线索。目录40项不代表40篇已确证不同的本人文章。用户第7份中的N1招生段落只是所提供版本的内容，发表日期与现时状态均未知。

文章库是思维与写作的证据层，不是本skill的主要输出形式。更新时也要检查判断动作、声音样本和案例归属；先有可靠材料，再改提炼，不把新样本当作独立封存题。

## 更新与验收

编辑 `articles.jsonl`，核对引用链接，更新 `coverage.json` 中统计与缺口，再重建人读目录。保留旧证据，记录为何改变作者归属。`full_history_verified` 仅在取得权威完整历史清单并逐项核对后设为true；可见主页到底也要说明删文和历史迁移的边界。

运行 `library.py validate`，并检索“融资”“结构外生长力”“冷邮件”，检查默认结果均为本人署名。用 `--scope all` 检查署名冲突记录确实仍有标签。
