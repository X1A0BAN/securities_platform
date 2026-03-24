# Securities Platform

一个基于 Tushare + Python + MySQL 的证券数据采集、同步与分析项目，当前聚焦沪深主板股票数据。

项目现阶段以后端数据链路为主，已经覆盖：
- 股票基础信息同步
- 交易日历同步
- 日线行情回补与增量同步
- 复权因子回补与增量同步
- 基础 ORM 查询层
- 基础查询服务层
- 后端查询缓存

后续规划方向包括：
- 基于 FastAPI 提供统一 HTTP 查询接口
- 对接 React 前端
- 引入更完整的分析选股能力
- 对接 Metabase 做看板和报表

## 项目目标

这个项目希望把“采集 -> 入库 -> 查询 -> 分析 -> 展示”这条链路逐步搭完整。

当前重点是先把后端基础能力打稳：
- 数据来源稳定
- 表结构清晰
- 同步脚本可重复执行
- 查询逻辑可复用
- 后续 API 和前端可以直接接入

## 当前业务范围

当前默认覆盖范围：
- 沪深主板股票
- 最近三年全量回补
- 每日增量同步

当前核心数据表：
- `dim_stock`
- `dim_trade_calendar`
- `fact_daily_price`
- `fact_adj_factor`

## 技术栈

### 当前已落地

| 分类 | 技术 | 作用 |
| --- | --- | --- |
| 数据源 | `Tushare Pro` | 拉取股票基础信息、交易日历、日线行情、复权因子 |
| 开发语言 | `Python 3` | 编写采集、同步、查询和分析逻辑 |
| 数据处理 | `pandas` | 处理 Tushare 返回的数据集 |
| ORM / 查询层 | `SQLAlchemy` | 管理模型定义、数据库连接和 ORM 查询 |
| MySQL 驱动 | `PyMySQL` | 为 SQLAlchemy 提供 MySQL 连接能力 |
| 数据库 | `MySQL` | 存储维度表、事实表和同步结果 |
| 配置管理 | `.env` + `app/config.py` | 统一管理数据库、Token、缓存等配置 |
| 数据访问层 | `app/crud` | 集中放置 ORM 查询函数，避免查询逻辑分散 |
| 服务层 | `app/services` | 组合查询结果并承载业务分析逻辑 |
| 缓存 | `app/cache.py` | 提供基础 TTL 查询缓存，降低重复查询开销 |
| 命令行脚本 | `scripts/` | 提供初始化、回补、全量同步、增量同步入口 |
| 运行环境 | `PowerShell` / `Bash` | 执行脚本和配置环境变量 |
| 定时调度 | `Windows 任务计划` / `cron` | 定时执行每日同步任务 |

### 当前 Python 依赖

`requirements.txt` 中当前已使用的核心依赖：
- `tushare`
- `pandas`
- `SQLAlchemy`
- `PyMySQL`
- `python-dateutil`

### 后续规划技术栈

下面这些是项目已经规划、但当前仓库还没有完整落地的部分：

| 分类 | 技术 | 规划用途 |
| --- | --- | --- |
| API 服务 | `FastAPI` | 对外提供行情查询、指标查询、选股接口 |
| 前端应用 | `React` | 展示行情、榜单、筛选结果与图表 |
| 前端缓存 | `TanStack Query (React Query)` / `SWR` | 缓存接口结果、减少重复请求、优化交互体验 |
| 可视化分析 | `Metabase` | 快速搭建报表、榜单、Dashboard |

说明：
- 当前仓库是后端仓库，还没有 React 代码。
- 这次新增的是后端查询缓存，不是 React 前端缓存。
- 如果后面接 React，建议优先使用 `TanStack Query` 做接口缓存。

## 系统分层

当前代码结构按职责分层：

1. 采集层：`app/collectors`
   负责从 Tushare 拉取原始数据。
2. 模型层：`app/models`
   负责定义数据库表结构。
3. 查询层：`app/crud`
   负责封装 ORM 查询，统一数据库读操作。
4. 服务层：`app/services`
   负责组织业务逻辑，例如行情查询、排行、选股分析。
5. 脚本层：`scripts`
   负责提供命令行入口，不承载复杂业务逻辑。

这种拆分的好处是：
- 采集逻辑和查询逻辑分开
- 脚本只做入口，不直接堆业务代码
- 后续接 FastAPI 时可以直接复用 `crud` 和 `service`
- 查询与分析功能扩展时更容易维护

## 目录结构

```text
securities_platform_backend/
├─ app/
│  ├─ cache.py
│  ├─ config.py
│  ├─ db.py
│  ├─ collectors/
│  │  ├─ daily_price_collector.py
│  │  ├─ stock_basic_collector.py
│  │  └─ trade_calendar_collector.py
│  ├─ crud/
│  │  ├─ __init__.py
│  │  ├─ daily_price_crud.py
│  │  └─ stock_crud.py
│  ├─ models/
│  │  ├─ adj_factor_model.py
│  │  ├─ daily_price_model.py
│  │  ├─ stock_model.py
│  │  └─ trade_calendar_model.py
│  ├─ services/
│  │  ├─ indicator_service.py
│  │  ├─ market_query_service.py
│  │  ├─ ranking_service.py
│  │  ├─ screener_service.py
│  │  ├─ sector_service.py
│  │  ├─ single_stock_service.py
│  │  ├─ stock_analysis_service.py
│  │  └─ sync_service.py
│  └─ utils/
│     ├─ date_utils.py
│     └─ logger.py
├─ scripts/
│  ├─ backfill_adj_factor.py
│  ├─ backfill_daily_price.py
│  ├─ init_db.py
│  ├─ run_daily_sync.py
│  ├─ run_full_sync.py
│  ├─ sync_stock_basic.py
│  ├─ sync_trade_calendar.py
│  ├─ test_stock_analysis.py
│  └─ sql/
│     └─ mysql_schema.sql
├─ test/
├─ requirements.txt
└─ README.md
```

## 环境变量

### 必填

- `DATABASE_URL`
- `TUSHARE_TOKEN`

### 可选

- `TUSHARE_PAUSE_SECONDS`
- `QUERY_CACHE_ENABLED`
- `QUERY_CACHE_TTL_SECONDS`
- `QUERY_CACHE_MAXSIZE`

### MySQL 示例

```text
mysql+pymysql://root:123456@127.0.0.1:3306/securities_data?charset=utf8mb4
```

### PowerShell 示例

```powershell
$env:DATABASE_URL="mysql+pymysql://root:123456@127.0.0.1:3306/securities_data?charset=utf8mb4"
$env:TUSHARE_TOKEN="你的_tushare_token"
$env:QUERY_CACHE_ENABLED="true"
$env:QUERY_CACHE_TTL_SECONDS="300"
$env:QUERY_CACHE_MAXSIZE="512"
```

## 数据库初始化

建表 SQL 位于：

```text
scripts/sql/mysql_schema.sql
```

如果数据库还没有建表，可以执行：

```bash
python scripts/init_db.py
```

## 使用顺序

建议按下面顺序初始化整个链路：

1. 安装并启动 MySQL
2. 配置 `DATABASE_URL` 和 `TUSHARE_TOKEN`
3. 执行 `python scripts/init_db.py`
4. 执行 `python scripts/run_full_sync.py --years 3`
5. 之后每日执行 `python scripts/run_daily_sync.py`
6. 后续再接 FastAPI、React、Metabase

## 已有脚本说明

### 初始化

- `python scripts/init_db.py`
  初始化数据库表结构。

### 同步股票基础信息

- `python scripts/sync_stock_basic.py --years 3`
  同步主板股票基础信息。

### 同步交易日历

- `python scripts/sync_trade_calendar.py --years 3`
  同步交易日历数据。

### 回补历史日线行情

- `python scripts/backfill_daily_price.py --years 3`
  回补最近三年的主板日线行情。

### 回补历史复权因子

- `python scripts/backfill_adj_factor.py --years 3`
  回补最近三年的主板复权因子。

### 执行全量同步

- `python scripts/run_full_sync.py --years 3`
  依次执行股票基础信息、交易日历、日线行情、复权因子的全量同步。

### 执行每日增量同步

- `python scripts/run_daily_sync.py`
  执行日常增量同步。

- `python scripts/run_daily_sync.py --end-date 2026-03-20`
  指定同步日期执行增量同步。

### 测试股票分析查询

- `python scripts/test_stock_analysis.py recent-prices --ts-code 600000.SH --days 60`
  测试查询某只股票最近 N 天行情。

- `python scripts/test_stock_analysis.py top-gainers --limit 50`
  测试查询最新交易日涨幅前 N 的股票。

## 查询与分析扩展建议

如果后续要继续做更多分析功能，建议遵循下面的约定：

- `app/crud`
  放基础 ORM 查询函数，例如按股票查最近 N 天行情、查询最新交易日、查询行业成分股。
- `app/services/single_stock_service.py`
  放单只股票查询，例如最近 N 天行情、后续的单股指标查询。
- `app/services/ranking_service.py`
  放市场级排行，例如涨幅榜、跌幅榜、成交额榜。
- `app/services/screener_service.py`
  放多只股票筛选，例如放量、创新高、连涨连跌。
- `app/services/sector_service.py`
  放行业和板块维度分析。
- `app/services/indicator_service.py`
  放均线等通用指标计算逻辑，供其他 service 复用。
- `app/services/stock_analysis_service.py`
  作为总入口 facade，统一组合上面的分析能力。
- `scripts`
  放命令行入口，负责解析参数和打印结果。

推荐写法是：
- 不把 SQL / ORM 查询散落在多个脚本里
- 不把所有分析都塞进一个大脚本
- 让脚本只做入口，核心逻辑写在 `crud` 和 `services`

## 当前已加的查询能力

目前已经有一个基础查询服务示例：
- `app/services/single_stock_service.py`
- `app/services/ranking_service.py`
- `app/services/indicator_service.py`
- `app/services/stock_analysis_service.py`
- `app/services/market_query_service.py`

已接入的方法包括：
- `get_recent_prices(ts_code, days=60)`
- `get_top_gainers(limit=50, trade_date=None)`
- `get_recent_prices_with_ma(ts_code, days=60, window=20)`

这些方法的调用链路是：

```text
script / API
    -> service
    -> crud
    -> database
    -> cache
```

其中：
- `app/crud/daily_price_crud.py` 负责基础行情查询
- `app/crud/stock_crud.py` 负责股票基础信息查询
- `app/services/single_stock_service.py` 负责单股查询
- `app/services/ranking_service.py` 负责市场排行
- `app/services/indicator_service.py` 负责通用指标计算
- `app/services/stock_analysis_service.py` 负责统一组合分析入口
- `app/cache.py` 负责查询结果缓存

## 缓存说明

当前新增的是后端内存查询缓存，不依赖 Redis。

特点：
- 基于 TTL 过期
- 可通过环境变量开关控制
- 可设置最大缓存条数
- 适合当前单进程脚本 / 后端开发阶段使用

如果后面系统进一步扩展，可以再升级为：
- Redis 缓存
- FastAPI 接口缓存
- React Query 前端缓存

## 当前约定

- 当前默认业务对象是沪深主板股票
- 当前默认数据库是 `DATABASE_URL` 指定的 MySQL
- 当前仓库先聚焦后端数据采集、同步、查询和分析
- FastAPI、React、Metabase 属于下一阶段扩展方向

## 备注

- 如果当天不是交易日，`run_daily_sync.py` 可能写入 0 行，这是正常现象
- 部分股票如果在回补区间内没有有效交易数据，可能只出现在 `dim_stock` 中
- 现在 README 中描述的“缓存”默认指后端查询缓存，不是前端 React 缓存
