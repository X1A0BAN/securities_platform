# Securities Platform 技术文档

## 1. 项目定位

本项目是一个面向证券数据采集、存储、处理、查询与展示的平台，目标是逐步建设为可支持股票基础信息、交易日历、日线行情、指标分析、AI 摘要与问答增强的后端服务系统。

当前阶段以数据同步和标准化存储为核心，后续逐步扩展 API 服务、可视化看板、容器化部署和智能分析能力。

## 2. 技术选型

### 2.1 核心技术

| 类别 | 技术 | 说明 |
| --- | --- | --- |
| 主开发语言 | Python | 负责数据采集、清洗、服务开发与脚本调度 |
| 后端框架 | FastAPI | 提供高性能 API，便于后续扩展查询、分析和 AI 接口 |
| 主数据库 | MySQL | 存储证券基础数据、交易日历、行情数据和业务日志 |
| 数据处理 | Pandas / NumPy | 负责结构化数据处理、缺失值处理、批量计算与指标加工 |
| 看板展示 | FineBI | 对接 MySQL，构建行情概览、数据更新监控等可视化页面 |
| 部署环境 | Linux | 作为生产环境部署平台，便于稳定运行和自动化运维 |
| 版本管理 | Git | 管理代码版本、分支协作与发布流程 |
| 容器化 | Docker | 后期用于统一开发、测试、生产环境，提升部署一致性 |
| 智能增强 | AI API / 本地模型 | 用于摘要生成、问答增强和看板文字解读 |

### 2.2 选型原则

1. 以 Python 为中心，兼顾开发效率与数据处理能力。
2. 以后端 API 为统一服务出口，便于对接前端、BI 和 AI 能力。
3. 先完成数据底座，再建设分析和智能增强模块。
4. 优先保证系统简单、稳定、可维护，避免早期过度设计。

## 3. 系统目标

### 3.1 一期目标

1. 建立数据库与基础表结构。
2. 完成股票基础信息同步。
3. 完成交易日历同步。
4. 完成日线行情历史回补与日常增量更新。
5. 提供基础日志能力和简单服务层封装。

### 3.2 二期目标

1. 基于 FastAPI 提供统一数据查询接口。
2. 支持常用证券筛选、行情查询和统计分析。
3. 将核心数据接入 FineBI 看板。
4. 增加任务调度、异常告警和运行监控。

### 3.3 三期目标

1. 引入 Docker 进行标准化部署。
2. 接入 AI API 或本地模型实现摘要、问答与辅助分析。
3. 扩展多数据源、更多证券品类和分析指标。

## 4. 项目结构设计

当前目录规划如下：

```text
securities_platform/
├─ app/
│  ├─ config.py
│  ├─ db.py
│  ├─ models/
│  │  ├─ stock.py
│  │  ├─ trade_calendar.py
│  │  └─ daily_price.py
│  ├─ collectors/
│  │  ├─ stock_basic_collector.py
│  │  ├─ trade_calendar_collector.py
│  │  └─ daily_price_collector.py
│  ├─ services/
│  │  ├─ stock_service.py
│  │  └─ update_service.py
│  └─ utils/
│     ├─ logger.py
│     └─ date_utils.py
├─ scripts/
│  ├─ init_db.py
│  ├─ sync_stock_basic.py
│  ├─ sync_trade_calendar.py
│  ├─ backfill_daily_price.py
│  └─ update_daily_price.py
├─ requirements.txt
└─ README.md
```

### 4.1 模块职责

#### `app/config.py`

统一管理配置项，例如数据库连接、日志级别、第三方数据源配置、AI 接口配置等。

#### `app/db.py`

负责数据库连接初始化、会话管理和基础数据库操作封装。

#### `app/models/`

定义数据表对应的模型结构，作为数据库层的核心对象。

- `stock.py`：股票基础信息模型
- `trade_calendar.py`：交易日历模型
- `daily_price.py`：日线行情模型

#### `app/collectors/`

负责从外部数据源拉取原始数据，并做初步清洗与字段映射。

- `stock_basic_collector.py`：采集股票基础资料
- `trade_calendar_collector.py`：采集交易日历
- `daily_price_collector.py`：采集日线行情

#### `app/services/`

承接业务逻辑，负责协调采集层、模型层和接口层。

- `stock_service.py`：股票数据查询、筛选与业务逻辑
- `update_service.py`：统一执行同步、增量更新、任务编排

#### `app/utils/`

提供通用工具能力。

- `logger.py`：日志初始化与格式定义
- `date_utils.py`：日期转换、交易日判断、区间生成等工具

#### `scripts/`

保存可直接执行的脚本，用于初始化、同步和更新任务。

## 5. 逻辑架构设计

系统整体建议采用分层架构：

```text
数据源 -> Collector 采集层 -> Service 业务层 -> MySQL 存储层 -> FastAPI 服务层 -> FineBI / AI / 外部调用方
```

### 5.1 各层说明

1. 采集层：对接外部行情或证券数据源，拉取原始数据。
2. 清洗层：使用 Pandas / NumPy 进行格式标准化、去重、补空和字段转换。
3. 存储层：将处理后的数据写入 MySQL。
4. 服务层：封装查询、更新和统计逻辑。
5. 接口层：通过 FastAPI 暴露标准 API。
6. 展示层：FineBI 直接基于 MySQL 或 API 展示业务看板。
7. AI 增强层：基于结构化数据和文本信息生成摘要、回答问题、辅助分析。

## 6. 数据流设计

### 6.1 基础信息同步流程

1. 执行 `scripts/sync_stock_basic.py`
2. 调用 `stock_basic_collector.py` 拉取股票清单
3. 清洗后写入 `stock` 表
4. 记录同步时间、成功数量和异常信息

### 6.2 交易日历同步流程

1. 执行 `scripts/sync_trade_calendar.py`
2. 调用 `trade_calendar_collector.py` 获取交易日历
3. 清洗后写入 `trade_calendar` 表
4. 支持后续行情补数与交易日判断

### 6.3 日线行情流程

1. 执行 `scripts/backfill_daily_price.py` 回补历史行情
2. 执行 `scripts/update_daily_price.py` 做日常增量更新
3. 调用 `daily_price_collector.py` 获取行情数据
4. 使用 Pandas 做字段标准化与数据去重
5. 写入 `daily_price` 表

## 7. 数据库设计建议

### 7.1 核心表

建议第一阶段至少包含以下三张核心表：

1. `stock`：股票基础信息表
2. `trade_calendar`：交易日历表
3. `daily_price`：日线行情表

### 7.2 建议字段方向

#### `stock`

- 股票代码
- 股票名称
- 市场
- 上市日期
- 状态
- 行业
- 更新时间

#### `trade_calendar`

- 交易所
- 日期
- 是否开市
- 前一交易日
- 更新时间

#### `daily_price`

- 股票代码
- 交易日期
- 开盘价
- 最高价
- 最低价
- 收盘价
- 成交量
- 成交额
- 涨跌幅
- 更新时间

### 7.3 数据库规范建议

1. 所有核心表应设置主键或唯一索引。
2. 常用查询字段如股票代码、交易日期应建立联合索引。
3. 时间字段统一使用明确时区策略，避免更新日期混乱。
4. 保留 `created_at`、`updated_at` 等审计字段，方便追踪数据变更。

## 8. FastAPI 规划

当前项目可先完成数据采集与存储，FastAPI 作为下一阶段能力接入。建议后续新增：

1. 健康检查接口
2. 股票基础信息查询接口
3. 交易日历查询接口
4. 日线行情查询接口
5. 数据更新触发接口
6. AI 摘要与问答接口

建议接口分层如下：

```text
router -> service -> db/model
```

这样可以保持接口逻辑简洁，并方便单元测试和后期维护。

## 9. FineBI 看板规划

FineBI 可作为管理层和分析人员的主要可视化入口，建议建设以下看板：

1. 股票基础信息概览看板
2. 交易日历与开市状态看板
3. 每日行情更新监控看板
4. 热门股票行情趋势分析看板
5. 数据同步任务运行状态看板

FineBI 初期可直接连接 MySQL，后期如有复杂权限控制需求，可改为通过 API 或中间层提供数据。

## 10. AI 增强能力规划

AI 模块建议在数据底座稳定后接入，优先从“增强功能”切入，而不是替代核心交易或行情逻辑。

### 10.1 可落地方向

1. 行情摘要：自动总结某只股票或某日市场表现。
2. 异动说明：结合价格波动输出简要解释模板。
3. 自然语言问答：例如“某只股票最近 30 天走势如何”。
4. 报表说明：为 FineBI 看板生成文字解读。

### 10.2 技术路线

1. 外部 AI API：开发快，适合早期验证。
2. 本地模型：更利于私有化和成本控制，适合后期演进。

### 10.3 接入建议

1. 将 AI 能力设计为独立服务模块，不与核心采集逻辑强耦合。
2. 输入以结构化数据和摘要文本为主，减少幻觉风险。
3. 对 AI 输出增加日志记录与人工校验机制。

## 11. 部署与运维规划

### 11.1 当前部署方式

建议初期采用 Linux 服务器部署，方式如下：

1. Python 虚拟环境运行采集脚本与 API 服务
2. MySQL 独立部署
3. 定时任务使用 `cron` 管理
4. 日志按天切分并定期归档

### 11.2 后续 Docker 化方向

后续可逐步容器化：

1. `app` 服务容器
2. MySQL 容器或外部数据库服务
3. 定时任务容器
4. 统一使用 `docker-compose` 或等价方案管理本地开发环境

## 12. 版本管理规范

项目使用 Git 进行版本管理，建议采用以下规则：

1. `main` 作为稳定分支
2. `dev` 作为日常开发分支
3. 功能开发使用 `feature/*` 分支
4. 修复问题使用 `fix/*` 分支

提交信息建议保持清晰，例如：

```text
feat: add stock basic collector
fix: handle duplicate daily price records
docs: update technical design
```

## 13. 后续开发建议

建议按以下顺序推进：

1. 完成 MySQL 表结构设计与初始化脚本
2. 完成配置管理、数据库连接和日志模块
3. 完成三个 collector 的基础版本
4. 完成同步脚本与 update service
5. 验证数据链路稳定性
6. 再接入 FastAPI 接口
7. 最后建设 FineBI 看板和 AI 增强模块

## 14. 当前结论

本项目的技术路线清晰，适合采用“数据底座优先、服务逐步扩展、智能能力后置增强”的建设方式。

整体推荐路线为：

```text
Python + FastAPI + MySQL + Pandas/NumPy + FineBI + Linux + Git
```

后续逐步加入：

```text
Docker + AI API / 本地模型
```

这套方案兼顾了开发效率、落地速度、后期扩展性与部署稳定性，适合作为证券数据平台的第一版技术实现方案。
