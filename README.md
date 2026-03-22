# Securities Platform

一个基于 Tushare + MySQL 的证券数据采集项目，当前聚焦沪深两市主板股票数据。

## 当前范围

- 股票基础信息：`dim_stock`
- 交易日历：`dim_trade_calendar`
- 日线行情：`fact_daily_price`
- 复权因子：`fact_adj_factor`

当前默认业务范围：

- 沪深两市主板
- 最近三年全量回补
- 每日增量同步

## 目录结构

```text
securities_platform/
├─ app/
│  ├─ config.py
│  ├─ db.py
│  ├─ models/
│  │  ├─ stock_model.py
│  │  ├─ trade_calendar_model.py
│  │  ├─ daily_price_model.py
│  │  └─ adj_factor_model.py
│  ├─ collectors/
│  │  ├─ stock_basic_collector.py
│  │  ├─ trade_calendar_collector.py
│  │  └─ daily_price_collector.py
│  ├─ services/
│  │  └─ sync_service.py
│  └─ utils/
│     ├─ logger.py
│     └─ date_utils.py
├─ scripts/
│  ├─ init_db.py
│  ├─ sync_stock_basic.py
│  ├─ sync_trade_calendar.py
│  ├─ backfill_daily_price.py
│  ├─ backfill_adj_factor.py
│  ├─ run_daily_sync.py
│  ├─ run_full_sync.py
│  └─ sql/
│     └─ mysql_schema.sql
├─ test/
├─ requirements.txt
└─ README.md
```

## 环境变量

必须设置：

- `DATABASE_URL`
- `TUSHARE_TOKEN`

MySQL 示例：

```text
mysql+pymysql://root:123456@127.0.0.1:3306/securities_data?charset=utf8mb4
```

PowerShell 示例：

```powershell
$env:DATABASE_URL="mysql+pymysql://root:123456@127.0.0.1:3306/securities_data?charset=utf8mb4"
$env:TUSHARE_TOKEN="你的_tushare_token"
```

## 建表

MySQL 建表 SQL 已保存为：

```text
scripts/sql/mysql_schema.sql
```

如果数据库还没建表，可执行：

```bash
python scripts/init_db.py
```

## 常用命令

同步主板股票基础信息：

```bash
python scripts/sync_stock_basic.py --years 3
```

同步交易日历：

```bash
python scripts/sync_trade_calendar.py --years 3
```

回补最近三年主板日线：

```bash
python scripts/backfill_daily_price.py --years 3
```

回补最近三年主板复权因子：

```bash
python scripts/backfill_adj_factor.py --years 3
```

执行最近三年全量同步：

```bash
python scripts/run_full_sync.py --years 3
```

执行每日增量同步：

```bash
python scripts/run_daily_sync.py
```

指定同步日期：

```bash
python scripts/run_daily_sync.py --end-date 2026-03-20
```

## 当前约定

- 不再保留 HS300 专用同步逻辑
- 默认业务对象就是沪深两市主板
- 不再使用本地 SQLite 作为默认数据库
- 所有数据统一落到 `DATABASE_URL` 指定的 MySQL

## 同步说明

`run_full_sync.py` 是全量流程：

- 更新主板股票池
- 更新交易日历
- 回补日线行情
- 回补复权因子

`run_daily_sync.py` 是日常增量流程：

- 更新主板股票池
- 刷新最近一段交易日历
- 只补数据库最后一个已落库交易日之后的新日线
- 只补数据库最后一个已落库交易日之后的新复权因子

## 备注

- 如果当天不是交易日，`run_daily_sync.py` 可能写入 0 行，这是正常行为
- 部分退市股票在最近三年区间内如果没有有效交易数据，可能只出现在 `dim_stock`，不一定出现在事实表
