# kehan.skill

认识了很多厉害的人，项目却没怎么往前走。你可以再听一轮建议，也可以先问：这段时间，你独立做出了什么决定？下一次见面，有没有一件能打开、能检查的东西？

`kehan.skill` 想让模型在问答和写作时，多做后面这一步。

它把给定文章样本中的判断习惯、语气和文章组织方式，整理成一个可以调用的 skill：先对准眼前的岔路，看作品、反馈和实际推进，再给出当前判断及改变判断的条件。写文章时，让段落推进论证，保留反例和不确定性，不靠几句强势语录装出一个人。

文章库是依据，不是每次回答的主角。你可以直接拿一个问题来讨论，也可以交一份素材，让它写文章或 README。这是基于有限样本的模拟视角，不是董科含本人，也不是官方项目。

仓库：[reshuibuduo/kehan.skill](https://github.com/reshuibuduo/kehan.skill) · 目录：`dong-kehan` · 调用：`$dong-kehan` · `SKILL.md` 版本：`0.2.0`

## 先拿一个真问题试

在支持加载此 skill 的宿主中调用。别先问它“像不像”，先看它有没有把问题说得更具体。

**问答**

```text
用 $dong-kehan 和我讨论：我做了一个 AI 记忆原型，认识了一些研究者，
但三个月没有明显进展。我该补基础、找合作，还是继续改产品？
先根据我给的事实作出当前判断，给一个两周内可检查的动作，
说明什么结果会让你改变建议。不要替董科含本人表态。
```

**写作**

```text
用 $dong-kehan 的文章组织方式，写一篇《为什么认识高手后仍然没有成长》。
先明确要改变读者的哪项判断，再展开机制，写进一个重要反面，
最后回到读者能做的事。只用我提供的事实，不补造亲历、对话或统计。
```

**README**

```text
用 $dong-kehan 为这个开源项目写 README。
先讲读者遇到的具体问题和项目已经做出的东西，尽早给可运行入口，
再交代范围、验证方式与来源边界。保留我提供的事实，
不要把计划写成已完成功能，不编安装命令、用户数量或效果提升。
项目事实如下：……
```

如果你只要客观查证文章，直接问出处、题名或原文即可。它会切换到资料模式，不必让每次讨论都附一份检索报告。

## 安装

使用[skills安装器](https://github.com/vercel-labs/skills#install-a-skill)（Node.js 22.20+）：

```bash
npx skills add reshuibuduo/kehan.skill --skill dong-kehan
```

按提示选择宿主；加 `-g` 可全局安装。安装后在下一轮对话中调用 `$dong-kehan`。

也可以先下载仓库检查材料：

```bash
git clone https://github.com/reshuibuduo/kehan.skill.git
cd kehan.skill
```

只需要文件包时，见[Release中的kehan.skill](https://github.com/reshuibuduo/kehan.skill/releases/latest)。打包格式是ZIP，内部目录为 `dong-kehan/`。

## 不调用模型，也能先检查材料

在仓库根目录运行，需 Python 3.9+：

```bash
python3 dong-kehan/scripts/library.py validate
python3 dong-kehan/scripts/library.py stats
python3 dong-kehan/scripts/library.py search '成长 作品' --scope usable --limit 3
python3 dong-kehan/scripts/library.py text dkh-user-20261110-07 --offset 0 --length 2000
```

`validate` 检查记录与本地正文完整性；`stats` 查看收集范围；`search` 查材料；`text` 打开保存正文。当前统计应包含 `total: 40`、`local_full_text_count: 5`、`full_history_verified: false`。这能验证资料包，不等于验证生成回答像本人。

CLI 只使用 Python 标准库，离线运行，不需要 API Key，没有爬虫或后台任务。调用 skill 时的模型运行、联网和费用，仍取决于你使用的宿主；本地搜索不等于宿主模型也在本地运行。

## 里面装了什么

```text
dong-kehan/
├── SKILL.md                      # 入口、判断动作、4 个候选心智模型
├── agents/openai.yaml            # 宿主展示配置
├── scripts/library.py            # 离线查找与校验
└── references/
    ├── voice.md                 # 8 段声音样本
    ├── writing.md               # 问答、长文与审稿工序
    ├── casebook.md              # 6 张材料内案例卡
    ├── articles.jsonl           # 40 条带来源状态的目录记录
    ├── catalog.md
    ├── coverage.json
    ├── collection.md            # 收集与更新规则
    ├── research/                # 提炼底稿
    └── user-provided/           # 5 份保存正文与原始输入记录
```

正文共 32500 字符。声音样本、案例和模型都从这些有限材料中提炼，不能把数量相加，当成更多独立证据。

本版 **40项程序与资料测试通过**。独立代理完成了带／不带skill的问答、写作与未知立场边界对照，**整体打平**；带skill答卷在个别样本细节上更明确，这不足以声称能力显著提升。详细结论见[FIDELITY.md](dong-kehan/FIDELITY.md)和[完整盲评](evaluations/blind-review.md)。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package_skill.py --output dist/kehan.skill
```

代码检查、样本适配和本人实际想法是三件不同的事。没有未见材料的封存验证，不给保真百分比。

## 哪些材料能支持哪些判断

40 条目录记录分为：6 条已核实署名记录、4 条用户正文记录、2 条官网补充、4 条其他署名、24 条待核实线索。

5 份全文包含已有融资记录的一份正文，并非在上述记录之外又新增 5 篇已核实文章。该融资记录有署名转载依据，保存全文仍是用户提供版本，未与原页逐字比对；另外 4 份缺少独立核实的作者栏与原标题。这不是全集，也没有完整公众号历史。

因此，材料能支持“这组样本里出现了怎样的写法和判断动作”，不能直接回答“本人现在一定怎么看”或“本人会不会投资”。案例卡是材料中的叙述，不是独立核验的传记；多人讨论中的学生、老师与叙述者也不会被合并成同一个人的观点。

查资料时，`usable` 包含已核实署名与用户正文，`self` 只查已核实署名，`supplied` 查保存的 5 份正文。其他作者、官网补充和待核实线索分别使用 `other`、`supplement`、`pending`；需要全目录时才用 `all`。

更好的新材料可能推翻现有提炼。这个项目保留这种可能，而不是把一次总结固定成人物的全部判断。

## 方法与授权

方法参考花叔的[女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill)。本项目是参考其框架的语料受限改版，不冒充女娲官方，也不声称已完成六路完整调研。

代码与自编说明采用 **MIT** 许可证。第三方文章、原文摘录及其他第三方内容不因仓库采用 MIT 而获得重新授权，相关权利仍归原权利人。

先用它处理一个你熟悉的问题：看它是否找到了真正影响决定的缺口，是否保留了会改变建议的反例，是否给出了能检查的下一步。一个口吻熟悉但判断空泛的回答，不算通过。

本README由加载本skill的独立代理起草，维护者补核安装命令、测试结果和发布链接；[写作任务与编辑记录](examples/README-generation.md)。
