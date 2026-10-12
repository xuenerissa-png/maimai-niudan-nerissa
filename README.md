# 麦门天意 McFortune

面向支持本地 Skill 的 AI 助手的趣味组餐技能。用户说“摇个麦门”，助手会结合预算、必选餐品、口味和可选的单餐热量上限，使用麦当劳中国官方 MCP 查询真实菜单、核价，并生成一句轻松的餐桌寄语（不涉及运势预测）。

## 产品视觉概念

![麦门天意 McFortune 产品概念：需求输入、扭蛋组餐、推荐揭晓、锁定重摇与偏好界面](assets/product-concept.jpg)

这是产品的早期概念设计，用于展示视觉方向与交互构想，非已上线界面。当前可运行版本是 AI 助手 Skill 与 Python CLI，尚未实现图中的手机界面、3D 动画、历史记录或收藏页。图中餐品、价格和文案为概念占位，不作为实时菜单、核价或营养数据。

图中的“运势”“宜吃辣”等属于早期创意表达；实际产品采用随机组餐和餐桌寄语，不提供运势预测，也不据此给出饮食或健康建议。品牌形象仅用于说明概念场景，本项目非麦当劳官方产品，相关商标及形象权利归各自权利人；代码许可证不授予这些素材的权利。

## 目标用户

想减少点餐纠结、按预算和单餐热量目标挑选麦当劳餐品的用户，以及希望在 AI 助手中复用 MCP 组餐流程的开发者。

## 安装 Skill

克隆本仓库，将整个目录作为本地 Skill 导入支持 SKILL.md 的 AI 助手。以 Codex 为例，可把完整目录放到 `~/.codex/skills/mcfortune`，重新载入技能后说“摇个麦门”。其余助手按各自本地技能导入方式安装；只使用 CLI 则直接在仓库目录运行下述命令。

## 已实现

- 官方 MCP Streamable HTTP 客户端、鉴权、工具发现和实际参数查询。
- 会话式组餐、锁定餐品及重新摇餐，通过 Skill 指导助手执行；不是独立网页或自动优化求解器。
- 到店自取门店查询、菜单与套餐详情、整单官方核价。
- 官方营养数据适配、标准份量热量汇总、单餐热量上限比较；缺失或特调餐品标为未知，不把未知项计为零。
- 确认后创建自取订单；提交前重新核价并检查确认金额上限。支付由用户在官方页面或 App 完成。
- 创建后查询订单状态；创建请求不自动重试，避免重复订单。

## 快速开始

需要 Python 3.10+，运行时只用标准库。先从 https://open.mcd.cn/mcp 获取自己的 Token，切勿发到聊天、放入参数或提交版本库。

在 macOS 的 Finder 中右键 `配置麦门.command` → 打开方式 → 终端，输入 Token 后自动测试连接。本机配置保存在 `.private/token`，目录权限 700、文件权限 600，已排除 Git。

也可以运行 `python3 local_setup.py --configure`。后续本机命令：

```bash
python3 local_setup.py test
python3 local_setup.py tools
python3 local_setup.py schema query-meals
python3 local_setup.py call query-meals --args-file .private/menu_args.json
python3 local_setup.py nutrition --args-file .private/nutrition_args.json
```

参数文件根据实际 schema 创建。热量参数示例：

```json
{"items":[{"name":"麦辣鸡翅2块","quantity":1},{"name":"圆筒冰淇淋","quantity":1}],"maxKcal":500}
```

直接使用 `python3 -m skill.cli` 时，从本机环境变量 `MCD_MCP_TOKEN` 读取 Token。Skill 的会话行为与确认下单用法见 [SKILL.md](SKILL.md)。

## 验证与边界

```bash
python3 -m unittest discover -s tests -v
```

已通过 13 项离线测试，并完成官方鉴权、门店菜单查询、套餐详情、整单核价、营养工具与两次真实待支付订单创建联调。测试不会创建真实订单，也不需要真实 Token。尚未验证支付完成后的完整取餐闭环。

热量按官方标准份量估算，实际制作存在差异。套餐需拆分实际选中子项，不推断缺失营养数据。下单支持到店自取，未实现外送、领券、退款、独立 3D 网页。新建订单不等于支付成功。

真实订单、账号、Token、支付链接和原始个人响应不作为公开演示材料。仓库内的测试使用虚构响应，仅验证程序行为，不冒充实时菜单。

官方 MCP 项目：https://github.com/M-China/mcd-mcp-server

## 对话示例

以下是脱敏后的交互形态，价格和营养数值来自本次官方联调，供应与价格随门店和时间变化，需要实时重查：

> 用户：广州，某地铁站附近自取，1人20元，想吃麦辣鸡翅。
> 助手：这餐要控制热量吗？不控制／尽量清爽／指定单餐上限。
> 用户：500千卡以内。
> 助手：查询门店、真实菜单与份量，核价后推荐麦辣鸡翅2块＋圆筒冰淇淋1个，共20元、约317千卡。若作为正餐不够饱，可调整搭配条件。
> 用户：放开必选鸡翅，不限预算，1000千卡以内，再摇。
> 助手：重新查询、核价后推荐巨无霸＋中薯条＋中杯可乐，共37.5元、约949千卡。
> 用户：锁定巨无霸，换个饮料。
> 助手：保留锁定项，只重新选择饮料，并重新计算价格和热量；用户确认后才创建订单。

## 参赛与来源

参加麦当劳程序员创意开发大赛，非麦当劳官方产品。基于提交者提供的初始技能包，在 Codex 辅助下迭代实现并完成实际联调；没有使用 WorkBuddy，不申报 WorkBuddy 专项奖励。不对娱乐寄语赋予运势预测、健康或医疗结论。

- [官方参赛声明](CONTEST_DECLARATION.md)：按官方文件原文保留。
- [MCP 集成说明](MCP_INTEGRATION.md)：实际 Server、Tool、调用流程与验证边界。
- [脱敏配置](mcp-config.example.json)：凭证只使用环境变量占位符。
- [活动规则](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/activityGuidelines.md)。

代码以 MIT License 开源。麦当劳商标、MCP 服务和官方参赛声明归相应权利人；许可证不授予商标或官方服务授权。
