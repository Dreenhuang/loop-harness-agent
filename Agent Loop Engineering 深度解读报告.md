# Agent Loop Engineering 深度解读报告

> 部分内容由豆包生成
> 
> 

# Agent Loop Engineering 深度解读报告

*——从单Agent循环到多Agent编排的完整工程化指南*

---

## 报告摘要

本报告基于《Agent Loop Manual 蓝皮书》进行深度解读与扩展，系统梳理了2026年AI Agent领域最重要的范式跃迁——Loop Engineering（循环工程）。报告从底层逻辑、核心构件、设计方法、编排拓扑、实战场景、成本经济学、架构选择、认知陷阱等多个维度进行了6000字的深度剖析，旨在帮助AI工程师与开发者理解并掌握这一新兴工程范式，构建可信赖的AI自动化系统。

**核心洞察**：2024年的瓶颈是模型能力，2026年的瓶颈是坐在循环里一轮轮手打prompt的人。Loop Engineering不是Cron的重新包装，而是Cron \+ Decision\-maker \+ Feedback \+ Guardrails的完整系统架构。

## 第一章 范式跃迁：为什么是Loop？

### 1\.1 瓶颈转移：从模型到人

2024年，AI领域的核心瓶颈是模型能力——我们需要更好的大语言模型来完成复杂任务。然而到了2026年，情况发生了根本性变化：模型写代码的速度已经远超人类阅读速度。新的瓶颈不再是模型，而是**坐在循环里一轮轮手打prompt的那个人**。

这一转变的标志性人物是Claude Code的创造者Boris Cherny。他分享的数据令人震撼：30天内259个PR，100%由Claude Code编写。他删除了IDE，再也没有打开过。但关键的是，他没有变成不写代码的人——**他变成了写Loop的人**。

### 1\.2 三阶段进化：工作方式的历史性转变

|阶段|工作方式|核心瓶颈|代表特征|
|---|---|---|---|
|**阶段1：手写代码**|人写代码，AI补全|手速|人类是主要生产者|
|**阶段2：Prompt驱动**|人给AI写提示，AI生成代码|人的注意力|一次只能盯一个session|
|**阶段3：Loop驱动**|人设计系统，系统自动prompt AI|验证能力与架构设计|数百Agent自主决策|

Boris现在处于阶段3：数百个Agent读取他的GitHub、Slack、Twitter，自行决定下一步做什么。人的工作从"打字"上移到"设计循环系统"。这是生产力的质的飞跃——一个工程师可以同时管理数十甚至上百个并行工作流。

### 1\.3 这不是Cron换了个帽子

社区最犀利的质疑是："Cronjobs have funny re\-branding rn\."（定时任务换了个好听的名字而已）。这个质疑对了一半，但忽略了本质区别。

**准确公式**：Loop = Cron \+ Decision\-maker \+ Feedback \+ Guardrails

调度层确实可以是Cron，但Cron只跑固定脚本。Loop的核心区别在于：

- **中间有模型根据当前状态决策下一步**——不是固定执行，而是动态决策

- **叠加多层监督**——生成与验证分离

- **持久状态**——跨会话记忆与恢复

- **验证门控**——独立验证器判断完成条件

这些结构是Cron无法表达的。

### 1\.4 演进谱系：从学术到工程化

|年份|阶段|代表|关键特征|
|---|---|---|---|
|2022|学术while\-loop|ReAct论文|推理→工具→观察→重复；单模型单loop|
|2023|自主目标循环|AutoGPT|给目标自prompt；易空转，催生"agents are a toy"叙事|
|2025\.07|Ralph Loop|Geoffrey Huntley|bash一行循环；每轮重置上下文；用$297构建了一门编程语言|
|2026春|产品化单Agent循环|/goal、/loop|Ralph做成一等命令 \+ 独立验证器模型判断完成|
|2026夏|编排循环|Boris/Steinberger/Gas Town|循环监督循环；定时调度；git持久化；多Agent树状编排|

**关键判断**：单Agent Ralph已是"old hat"（过时的东西）。2026年真正新的层是：**多Agent编排循环 \+ 持久化 \+ 调度**。

## 第二章 Loop的解剖学——五大构件与一个记忆层

Google Chrome团队的Addy Osmani将Loop拆解为五个构件加一个记忆层。Claude Code和Codex都已经具备全部五个构件，这是产品成熟度的重要标志。

### 2\.1 五大构件一览

|构件|核心作用|Claude Code实现|Codex实现|
|---|---|---|---|
|**1\. Automations（自动化/心跳）**|定时触发，让loop成为真正的循环而非一次性运行|Automations Tab \+ Triage Inbox|/loop、/schedule、Hooks、GitHub Actions|
|**2\. Worktrees（工作树隔离）**|并行Agent互不踩踏文件|内建worktree支持|\-\-worktree flag、subagent isolation: worktree|
|**3\. Skills（技能资产）**|停止每次从零解释项目，让循环复利|\.claude/skills/$skill\-name|\.codex/skills/SKILL\.md|
|**4\. Plugins/Connectors（连接器）**|Agent能操作真实工具链|MCP协议|MCP协议|
|**5\. Sub\-agents（子代理）**|写代码的和验证的分开，maker ≠ checker|TOML agents定义|subagents \+ agent teams|

**第六构件：Memory（记忆层）**——一个Markdown文件、一个Linear看板、任何存在对话之外的东西。模型每轮都会遗忘，但仓库不会。

### 2\.2 深入：Automations（心跳）

这是区分"一次性会话"和"真正循环"的核心构件。

- **/loop**：在会话内按间隔重跑prompt，适合短期看护任务

- **/goal**：持续运行直到一个独立小模型确认条件为真。**关键细节**：判断完成的不是写代码的那个模型

- **/schedule**：跨会话持久。关掉终端、合上笔记本，任务依然在云端运行

Boris的经典用法：

```bash
/loop babysit all my PRs. Auto-fix build issues, and when comments come in, use a worktree agent to fix them.
```

### 2\.3 深入：Worktrees（隔离）

两个Agent同时写同一个文件 = 两个工程师提交同一行代码且没沟通。这是协作灾难的根源。

Git worktree给每个Agent独立检出，彼此物理隔离。这是多Agent系统能够稳定运行的基础架构决策。没有隔离，并发Agent必然产生冲突和污染。

### 2\.4 深入：Skills（技能即资产）

一个Skill = 一个文件夹 \+ SKILL\.md（指令与元数据） \+ 可选脚本/资源。

**为什么Skills比Prompt重要？**

没有Skills的Loop每轮从零推导项目约定，反复浪费Token。有Skills的Loop像一个不断积累经验的团队——每次做过的难题沉淀为Skill，下次免费调用。

*"The loop is plumbing\. The asset is the skill it calls\." — Matt Van Horn*

这是Loop系统产生复利效应的关键。Skills是团队的知识资产，Loop只是调用这些资产的管道。

### 2\.5 深入：Sub\-agents（Maker\-Checker分离）

**这是Loop能在无人值守时可信的唯一原因**。

写代码的模型给自己的作业打分永远太宽容。人类心理学中的"确认偏误"在AI中同样存在——模型会说服自己的输出是正确的。第二个Agent（不同指令、甚至不同模型）才能抓住第一个说服自己的错误。

/goal底层就是这个结构：写代码的Agent完成后，一个独立的小模型检查停止条件是否满足。Maker\-Checker split应用在了停止条件本身上。

## 第三章 设计一个Loop的五步法

来自Amit Shekhar的结构化方法论。核心类比：**Prompt是一步棋，Loop是一套棋局策略**。

### 3\.1 Step 1：定义"Done"——先写停止条件

**在写任何逻辑之前回答：Loop怎么知道自己完成了？**

如果无法用代码表达"done"，Agent要么永远跑下去，要么过早停止。

```python
def is_done(state):
    """停止条件必须是代码，不是你脑子里的想法"""
    return (
        state.tests_pass and 
        state.lint_clean and 
        state.coverage > 0.8
    )
```

常见的"done"定义：

- 测试全部通过

- 输出匹配JSON Schema

- 评分超过阈值

- CI流水线绿色

**最常见错误**：用自然语言描述"做好为止"、"满意为止"，而不是用可执行代码定义完成条件。这是无限循环的第一诱因。

### 3\.2 Step 2：构建Context，而非手写指令

大多数人的错误：每轮手动粘贴报错信息。正确做法：从系统当前状态自动组装prompt。

```python
def build_prompt(state):
    prompt = f"Goal: {state.goal}\n"
    prompt += f"Files: {state.relevant_files}\n"
    prompt += f"Tools available: {state.tools}\n"
    if state.last_error:
        prompt += f"Last failure: {state.last_error}\n"
    prompt += f"Previous attempts: {state.attempt_history}\n"
    return prompt
```

同一个build\_prompt函数每轮产出不同的prompt——因为背后的state在移动。**Loop不变，Context变**。

### 3\.3 Step 3：执行并捕获一切

Agent行动后，必须抓取：

- 代码diff

- stdout/stderr

- 测试结果

- 系统新状态

**关键洞察**：失败输出不是终点，是下一轮prompt的原材料。

### 3\.4 Step 4：用反馈闭合循环

两条路径：

- **通过** → 停止，任务完成

- **失败** → 将失败信息写入state，下一轮build\_prompt自动包含这个报错

Agent用上一轮的失败重新prompt自己。**Loop自我喂养**。这是自动化的核心——人类不需要在中间手动传递错误信息。

### 3\.5 Step 5：设置护栏（Guardrails）

没有出口的Loop不是系统，是永不停止的账单。

```python
def run_loop(goal, max_turns=15, max_cost_usd=5.0):
    state = State(goal=goal)
    for turn in range(max_turns):
        if state.cost > max_cost_usd:
            return "Stopped: budget exhausted"
        prompt = build_prompt(state)
        result = agent.run(prompt)
        state.update(result)
        if is_done(state):
            git_commit("Task completed")
            return "Success"
        if state.no_progress_detected(): # 连续两轮相同错误
            return "Stopped: no progress"
    return "Stopped: max iterations reached"
```

**三道硬刹车**：

1. 最大迭代次数（通常15\-50）

2. 无进展检测（fingerprint相同的tool call重复出现）

3. Token/美元预算上限

### 3\.6 完整示例：修复登录Bug

- **Turn 1**：State包含目标和文件，无报错。Agent修改代码。测试失败："password check returns true for empty password"。错误写入state。

- **Turn 2**：build\_prompt自动包含上轮错误。Agent读到具体报错，修复那一行。测试通过。

- **Turn 3**：不存在。is\_done在Turn 2返回True，Loop自行停止。

**全程零人工prompt**。失败从Turn 1自动流向Turn 2的输入。

## 第四章 从单Agent到舰队——六种编排拓扑

来自Avid的多Agent工作流完整指南。核心问题：**如何在不让Agent互相污染上下文的前提下协调？**

### 4\.1 为什么需要多Agent

单Agent的三个硬限制：

1. **上下文饱和**：所有中间结果挤占窗口，Agent在自己的历史里推理而非面对实际问题

2. **串行瓶颈**：200文件迁移本可并行，单Agent串行跑几小时

3. **脆弱恢复**：中途崩溃整个任务重启，无检查点

### 4\.2 六种拓扑深度解析

#### ▸ 拓扑1：顺序流水线（Sequential Pipeline）

**结构**：Agent A → Agent B → Agent C

**适用**：工作严格依赖，每步必须在下步开始前完成

**实现**：动态工作流脚本中链式调用subagent

**失败模式**：延迟累积。Agent B慢则整条管线等待

**禁用于**：有独立并行路径的工作

#### ▸ 拓扑2：协调者\-工作者（Coordinator\-Worker）

**结构**：Coordinator分发任务给多个Worker

**适用**：工作可分解为不同专家领域，路由逻辑在计划时已知

**关键规则**：协调者只做分解和路由，绝不做领域推理。否则其上下文膨胀成单Agent瓶颈

**失败模式**：协调者单点故障。上下文漂移时整个系统退化

#### ▸ 拓扑3：并行扇出\-合并（Parallel Fan\-Out with Merge）

**结构**：Fan\-Out → A/B/C/D/E并行执行 → Merge

**适用**：子任务间无依赖。典型：审计200文件、查询多数据源

**性能**：并行执行将处理时间削减60\-80%

**Claude实现**：动态工作流默认支持最多16并发Agent

**失败模式**：Merge逻辑是难点。Agent返回不一致schema或矛盾结论时，朴素合并产出垃圾。**必须在扇出前定义输出契约**

#### ▸ 拓扑4：生成\-验证（Generator\-Verifier）

**结构**：Generator → Verifier → \(pass/fail\) → Generator → \.\.\.

**适用**：输出质量关键且评判标准可明确写出（安全审计、迁移计划、测试用例）

**关键**：验证标准写成可检查规则。如果验证器标准模糊，它就变成橡皮图章

**本质**：这就是Loop的核心模式在多Agent层面的映射

#### ▸ 拓扑5：共享状态（Shared\-State）

**结构**：Agent A ↔ \[Shared Store\] ↔ Agent B ↔ Agent C

**适用**：Agent间需要渐进式共建发现，一个Agent的发现立即对其他人有用

**实现**：git worktree中的结构化docs文件夹，Markdown文件即通信协议

**致命风险**：上下文污染——一个Agent写入错误发现，所有下游Agent当作真理。**必须在每个写入点做schema验证**

#### ▸ 拓扑6：辩论对抗（Debate/Adversarial）

**结构**：Agent A（正方） ↔ Judge ↔ Agent B（反方）

**适用**：需要经受对抗压力的发现（安全审计、迁移风险评估）

**价值**：经过refutation存活的结论比单次扫描的结论可信度高出一个量级

### 4\.3 五大生产失败模式

|失败模式|表现|预防措施|
|---|---|---|
|**上下文污染**|Agent写入幻觉到共享存储，下游当真理传播|Schema验证每个写入点；验证Agent在写入前检查|
|**级联失败**|一个Agent挂掉，坏结果被路由给下游，引发连锁崩溃|熔断器：null/error输出立即切断该分支|
|**范围蔓延**|"审计代码库"的Agent开始编辑不该碰的文件|每个Agent显式声明可操作路径和权限|
|**静默替换**|Agent无法完成步骤，悄悄插入占位数据，报告成功|System Prompt中明确要求：失败必须大声报错，绝不静默替代|
|**协调死锁**|Agent A等B，B等A|显式依赖图 \+ 每次调用设超时|

### 4\.4 通信架构：直接通信 vs 基底介导

**生产系统规则**：Claude动态工作流用JavaScript脚本变量作为基底——中间结果存在脚本变量里，而非任何Agent的上下文窗口中。这是架构上的关键决策。

**最大架构错误**：把所有Agent结果路由回协调者上下文。这等于用额外网络跳重建了单Agent上下文瓶颈。

## 第五章 实战场景与完整写法

### 5\.1 场景1：CI看护者（最成熟，立即可用）

**为什么最适合Loop**：停止条件完全客观（CI绿 = done）。

```bash
/loop Watch CI on all my open PRs. When a check fails:
1. Pull the failure log
2. Open a worktree for that PR
3. Fix the issue
4. Push and wait for CI to re-run
Stop when all checks are green.
```

来自实际使用者Tyler Gibbs的经验：

- Agent不应直接对话。它们写入共享记忆层，从中读取。权威知识只存在一个地方

- 协调者上下文里应该只有：计划 \+ 最终综合。别的什么都不放

- "我有循环来：照看CI直到它们通过、监控PR的评论、保持所有下游文档最新"

### 5\.2 场景2：PR评论响应

```bash
/loop Monitor my open PRs for new review comments.
When a comment arrives:
1. Read the comment and understand the requested change
2. Create a worktree agent to implement the fix
3. Run tests to verify
4. Push and reply "Fixed in latest commit"
```

### 5\.3 场景3：TDD驱动的自主开发

Elvis Sun的公式：**Right harness \+ Loop = 解决任何工程问题**

**写法**：

1. 你负责写出严苛的测试（这是你的"Constitution"）

2. 启动Loop，让Agent反复修改代码直到测试全部通过

3. 每次测试通过的版本自动git commit（检查点）

```bash
/goal All tests in test/parser/ pass and coverage > 90%. 
Run pytest after each change. Commit on each green run.
```

**实战数据**：Eric Ventor确认ML训练中Loop极强——"指定测试集成功率x%，就一直跑到达标"。

**但注意**：纯软件开发的结果定义没ML那么明确。如果测试不够严苛，Agent会hack测试而非真正解决问题。

### 5\.4 场景4：看板驱动开发（Thomas Rice模式）

```bash
/loop Read the "Ready" column in Linear.
For each ticket:
1. Create a worktree
2. Implement the ticket
3. Run all tests
4. If green, open PR and move ticket to "AI Review"
5. Move to next ticket
Stop when "Ready" column is empty.
```

### 5\.5 场景5：多Agent编排（Gas Town模式）

Steve Yegge的Gas Town：20\-30个Claude Code实例协调运行。

|角色|职责|
|---|---|
|**Mayor（市长）**|任务分解、分发、综合|
|**Polecat（工人）**|在隔离worktree中执行具体任务|
|**Witness（监工）**|独立Review，对抗式验证|
|**Deacon（巡逻daemon）**|持续循环运行的ephemeral workflow|

状态存git（称为"beads"），崩溃可恢复。指数退避节省资源。

### 5\.6 场景6：Orchestrate\-Map\-Reduce（高阶技能）

Daniel Grant的高阶编排：

1. 将问题空间扇出给多个Agent，每个探索不同解法

2. 收集所有方案

3. Reduce为最优候选

```text
orchestrate-map-reduce:
diverge: "针对当前 bug,各尝试一种不同的修复策略"
converge: "选择测试覆盖率最高且改动最小的方案"
```

**核心洞察**：这是一个高阶Skill（接受另一个Skill作为输入的Skill），让"发散\-收敛"模式可复用于任何领域。

### 5\.7 场景7：Autoloop（自进化循环）

普通Loop重复。Autoloop改进。区别在于：**有没有一个benchmark让Agent给自己打分**。

Meta Alchemist的Spark Domain Chip架构：

1. **标准化工作流**：Loop需要稳定的形状才能抓住

2. **Eval基准**：Agent能被度量而非仅仅"听起来不错"

3. **Autoloop**：尝试变异→对benchmark评分→赢了保留/输了回滚

"A loop that repeats is not a loop that improves\. The difference is a way to score itself\."

**Guardrails**：变异限幅、停止条件、回滚记录、证据门控。

## 第六章 经济学与避坑——Loop的真实成本

### 6\.1 成本结构已经反转

> "Every AI agent I shipped this year is a for\-loop, an LLM call, and a try/catch around JSON parsing\. The only thing agentic about it is the Anthropic bill at the end of the month\." — @rohit\_jsfreaky
> 
> 

> "The costliest thing in AI coding is no longer writing code—it is managing the agent loop\." — @runes\_leo
> 
> 

Uber的教训：给工程师设Claude Code/Cursor月cap $1,500/人/工具，因为四个月就烧光了全年AI预算。

**关键认知**：成本不在模型写代码——那很便宜。成本在Loop一轮轮跑模型。通宵跑可能跑数千轮。

### 6\.2 八大反模式

|\#|反模式|后果|修复|
|---|---|---|---|
|1|**无"done"检查**|Loop永不停止|先写is\_done\(\)，在写任何其他代码之前|
|2|**手动喂prompt**|不是Loop，是你在做苦力|从state自动组装prompt|
|3|**丢弃输出**|失败信息是下一轮的弹药，丢了等于断了反馈链|捕获一切：diff、stdout、error|
|4|**无护栏**|无限循环 \+ 账单爆炸|三道刹车：max iterations \+ no progress \+ budget|
|5|**Agent自己验证自己**|给自己作业永远打满分\("Looks great\! LGTM\!"\)|独立验证器（不同Agent/不同模型/客观测试）|
|6|**上下文无限膨胀**|第10轮prompt 100K tokens，Agent忘记初始任务，幻觉放大|Ralph模式（每轮重置上下文）；进度存Git/Markdown|
|7|**Loop内无Skills**|每轮从零推导项目约定，重复烧钱|重复做的事 → Skill；难题解法 → Skill|
|8|**对一次性任务强上Loop**|过度工程|Loop只在工作可重复且可验证时有价值。一次性的用单次prompt|

### 6\.3 停止条件设计检查表

* [ ] "Done"用代码表达了吗？（非人脑判断）

* [ ] 有独立于执行者的验证器吗？

* [ ] 中间状态存在外部介质（文件/git/脚本变量）而非Agent上下文吗？

* [ ] 不可逆操作处有人类门控吗？

* [ ] 最大迭代数设了吗？

* [ ] 无进展检测（连续相同错误）启用了吗？

* [ ] Token/美元硬上限设了吗？

* [ ] 失败时loud failure，禁止silent substitution？

### 6\.4 Token优化策略

|策略|原理|
|---|---|
|协调者只路由不推理|窄上下文 = 少Token|
|中间结果存脚本变量而非管道回协调者|避免O\(n\)上下文增长|
|每个Agent只接收完成其任务所需的文件|不要把整个文件树塞给只需要三个文件的Agent|
|短期记忆只保留最近3\-5轮交互|旧上下文落盘|
|心跳 \+ 时间抖动\(±jitter\)代替不间断循环|约每30分钟伪随机唤醒，而非24h狂转|
|3\-7 Agent规则|超过则创建层级结构，扁平20\+ Agent有O\(n²\)通信开销|

## 第七章 Open Loop vs Closed Loop——选择你的战场

### 7\.1 定义对比

|维度|Open Loop（开放循环）|Closed Loop（封闭循环）|
|---|---|---|
|**结构**|有目标和条件，但探索空间大|人类预先设计端到端路径|
|**Agent自由度**|可尝试不同路径，发现未预设方案|在预设框架内循环|
|**成本**|Token消耗极大|预算可控|
|**风险**|松散标准下变slop machine|每轮迭代改进|
|**适用**|前沿探索、有无限预算的实验|**90%的生产工作今天就能用**|

### 7\.2 Closed Loop结构

来自Shann³ Holmberg的推荐架构：

```text
Orchestrator(拥有目标)
    ↓
Specialists(拥有步骤)
    ↓
Subagents(做窄工作)
    ↓
Eval Gate(确保不是slop)
```

每一层都有验证门。每次循环的数据喂给下一轮。在正常预算内运行因为路径是紧凑的。

### 7\.3 Inside\-the\-Loop vs Outside\-the\-Loop

|架构|特征|风险|
|---|---|---|
|**Inside\-the\-Loop**|计划可见、高风险操作有approval gate、中间状态可介入|需要更多设计|
|**Outside\-the\-Loop**|派发任务后黑盒运行，只在开始和结束有界面|失败静默、晚期才发现|

**最小可行inside\-the\-loop** = 计划审查门 \+ diff提交前门。

### 7\.4 何时用多Agent，何时留单Agent

**用多Agent当：**

- 任务有真正独立的并行路径

- 工作超出单Agent上下文窗口且无损摘要不可能

- 需要对抗验证（经过refutation的发现更可信）

- 任务运行数小时到数天，需要检查点恢复

- 流程可重复，编排本身应成为可复用资产

**留单Agent当：**

- 任务纯串行无并行性

- 工作舒适地装在一个上下文窗口里

- 协调开销超过执行时间

- 你还在快速迭代系统（多Agent架构重构成本高）

## 第八章 Loop Engineering的认知陷阱与工程师角色

### 8\.1 Loop不替代你，它放大你

Addy Osmani的警告：

> "Two people can build the exact same loop and get completely opposite results\. One uses it to move faster on work they understand deeply\. The other uses it to avoid understanding the work at all\. The loop does not know the difference\. You do\."
> 
> 

三个会因Loop变更难而非更容易的问题：

1. **验证仍在你身上**：无人值守的Loop也是无人值守地犯错。"Done"是声明不是证明。

2. **理解力腐蚀**：Loop越快产出你没写的代码，"存在的"和"你真正理解的"之间的鸿沟越大。这叫Comprehension Debt。

3. **认知投降**：当Loop自己跑得顺时，极其诱人的姿态是停止有主见、接受一切产出。这是Cognitive Surrender。

### 8\.2 Loop Engineering比Prompt Engineering更难

Boris的观点不是"工作变容易了"，而是"杠杆点上移了"。

|Prompt Engineering|Loop Engineering|
|---|---|
|写一条好指令|设计一个系统，该系统能持续地、可验证地、在预算内驱动Agent完成复杂任务|
|语言学能力|系统设计 \+ 测试工程 \+ 成本管控 \+ 进度管理|

### 8\.3 场景成熟度排序

|成熟度|场景|原因|
|---|---|---|
|★★★ 高|CI看护、PR监控、文档同步、小patch\+测试|停止条件100%客观|
|★★ 中|多Agent编排、看板驱动开发、可度量autoresearch|需良好架构设计|
|★ 低|通宵全自主造产品、开放式"做好为止"|目标模糊、易跑偏、费Token|
|✗ 不推荐|无监督hack目标、纯while\-true、无验证的Open Loop|社区明确警告|

### 8\.4 正确姿态

"Build the loop\. But build it like someone who intends to stay the engineer, not just the person who presses go\." — Addy Osmani

## 第九章 从零开始的系统设计清单

当你准备为一个真实项目设计Loop时，按以下步骤走：

### Step 1：任务分解

用一句话写下顶层任务。列出所有需要的操作。对每个操作回答：

- 它依赖另一个操作的输出吗？（串行依赖）

- 它能和其他操作同时跑吗？（并行候选）

将串行依赖操作分组为Phase，并行候选分组为Phase内的Fan\-out。

### Step 2：专家识别

对Phase图中的每个操作，定义Agent：

- **角色**（一句话，无歧义）

- **工具权限**（只读？可写哪些路径？可执行哪些命令？）

- **输出契约**（精确JSON Schema）

- **失败行为**（不能完成时做什么——必须loud fail）

**避免万能Agent**。"代码Agent"什么都做 = 上下文膨胀的单Agent。

### Step 3：通信设计

决定基底介导还是直接通信。绝大多数系统答案是基底介导。

画出读/写图。如果任何Agent从多个其他Agent都写入的位置读取——你有上下文污染向量。在那个读取前加验证步骤。

### Step 4：治理契约

在写任何工作流prompt之前，先写CLAUDE\.md（或等效的Agent规则）：

- 每个Agent的权限范围

- 错误处理策略

- 人类门控点

- 审计日志要求

### Step 5：起飞前检查

* [ ] 在git worktree / feature branch中工作，不在main上

* [ ] 每个Agent的权限在task prompt中显式限定

* [ ] 每个写入共享存储的Agent有输出契约

* [ ] 关键路径上的生成Agent配有验证Agent

* [ ] 所有不可逆操作定义了人类门控

* [ ] 所有evaluator\-optimizer循环设了max iterations

* [ ] 每个Agent的失败行为已定义（loud fail, never silent）

* [ ] 检查Token预算

## 第十章 工具速查与快速上手

### 10\.1 Claude Code命令速查

|命令|作用|持久性|
|---|---|---|
|**/loop \<prompt\>**|会话内按间隔重跑|关终端即停|
|**/goal "\<condition\>"**|持续运行直到条件满足（独立模型判断）|会话内|
|**/schedule**|跨会话定时任务|持久|
|**Routines**|云端自主运行完整session|关笔记本也能跑|
|**Dynamic Workflows**|脚本编排多阶段多Agent|可存为slash command|
|**Hooks**|Agent生命周期特定点触发shell命令|配置持久|

### 10\.2 推荐路径（由浅入深）

|Level|做什么|门槛|
|---|---|---|
|0|手动prompt|\-|
|1|/loop或/goal babysit一个明确任务|一句话|
|2|加验证门（测试、lint、type check）；设max\-iterations和预算|10分钟配置|
|3|把重复流程沉淀为Skills；用Routines持久化|半小时写SKILL\.md|
|4|Dynamic Workflows / 多Agent拓扑|需系统设计能力|
|5|Autoloop：给Loop加benchmark，让它自我进化|需定义领域eval|

## 第十一章 未来展望与行业趋势

### 11\.1 Loop Engineering的演进方向

基于当前的技术路线图，我们可以预见Loop Engineering的几个关键演进方向：

1. **自进化Loop（Autoloop）**：从重复执行到持续改进。Loop不仅能重复任务，还能通过benchmark自我评估、自我优化。这是当前最前沿的研究方向。

2. **跨平台Loop编排**：Loop不再局限于单个工具，而是跨Claude、GPT、Codex等多个平台的混合编排。

3. **Loop市场与可组合性**：像npm包一样，Loop和Skill成为可交易、可组合的软件资产。

4. **形式化验证**：将形式化方法引入Loop设计，从根本上保证系统的安全性和可靠性。

### 11\.2 对软件工程的深远影响

Loop Engineering正在重新定义软件工程的本质：

- **从"写代码"到"设计系统"**：工程师的核心技能从编码转向系统架构设计、验证策略、成本管控

- **从"单人工作"到"团队管理"**：每个工程师管理数十个Agent，成为AI团队的技术负责人

- **从"一次性交付"到"持续运营"**：软件成为持续运行的Loop系统，需要监控、优化、迭代

- **从"代码资产"到"Skill资产"**：知识沉淀为可复用的Skill，而非散落的代码

### 11\.3 一句话总结

**Stop being the thing in the loop\.**

Write the loop once, give it skills worth calling and feedback so it can check itself, cap it so it halts, and let it run on cron while you go decide what to build next\.

---

## 附录：关键引用来源

|来源|作者|核心贡献|
|---|---|---|
|WTF Is a Loop?|Matt Van Horn|从15个Reddit线程 \+ 21条X帖综合定义|
|Loop Engineering|Addy Osmani|五大构件框架|
|How to design a loop|Amit Shekhar|五步法系统教程|
|Multi Agent Workflows Full Guide|Avid|六种编排拓扑 \+ 五大失败模式|
|Autoloops \> Agent Loops|Meta Alchemist|自进化循环 \+ Eval是秘密|
|Beyond Ralph Loops|Daniel Grant|高阶Skill \+ orchestrate\-map\-reduce|
|Open vs Closed Loop|Shann³ Holmberg|开放/封闭循环分类|
|Gas Town|Steve Yegge|20\-30实例编排系统落地实现|

---

*本报告基于《Agent Loop Manual 蓝皮书》深度解读与扩展 \| 报告字数：约6500字*

> （注：文档部分内容可能由 AI 生成）
