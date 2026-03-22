CREATE DATABASE IF NOT EXISTS securities_data
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

USE securities_data;

CREATE TABLE IF NOT EXISTS dim_stock (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    ts_code VARCHAR(20) NOT NULL COMMENT '统一股票代码，如 600000.SH',
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码，如 600000',
    name VARCHAR(50) NOT NULL COMMENT '股票名称',
    market VARCHAR(20) DEFAULT NULL COMMENT '市场类型，如 主板/创业板/科创板',
    exchange VARCHAR(10) DEFAULT NULL COMMENT '交易所，如 SH/SZ/BJ',
    industry VARCHAR(100) DEFAULT NULL COMMENT '所属行业',
    list_date DATE DEFAULT NULL COMMENT '上市日期',
    delist_date DATE DEFAULT NULL COMMENT '退市日期',
    is_active TINYINT NOT NULL DEFAULT 1 COMMENT '是否仍在上市，1是0否',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_ts_code (ts_code),
    KEY idx_symbol (symbol),
    KEY idx_name (name),
    KEY idx_exchange (exchange)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基础信息表';

CREATE TABLE IF NOT EXISTS dim_trade_calendar (
    trade_date DATE NOT NULL COMMENT '交易日期',
    exchange VARCHAR(10) NOT NULL COMMENT '交易所，如 SH/SZ',
    is_open TINYINT NOT NULL COMMENT '是否开市，1开市0休市',
    pretrade_date DATE DEFAULT NULL COMMENT '上一个交易日',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    PRIMARY KEY (trade_date, exchange),
    KEY idx_is_open (is_open)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易日历表';

CREATE TABLE IF NOT EXISTS fact_daily_price (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    ts_code VARCHAR(20) NOT NULL COMMENT '统一股票代码，如 600000.SH',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,3) DEFAULT NULL COMMENT '开盘价',
    high DECIMAL(10,3) DEFAULT NULL COMMENT '最高价',
    low DECIMAL(10,3) DEFAULT NULL COMMENT '最低价',
    close DECIMAL(10,3) DEFAULT NULL COMMENT '收盘价',
    pre_close DECIMAL(10,3) DEFAULT NULL COMMENT '昨收价',
    change_amount DECIMAL(10,3) DEFAULT NULL COMMENT '涨跌额',
    pct_chg DECIMAL(10,3) DEFAULT NULL COMMENT '涨跌幅(%)',
    vol BIGINT DEFAULT NULL COMMENT '成交量',
    amount DECIMAL(20,3) DEFAULT NULL COMMENT '成交额',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_ts_code_trade_date (ts_code, trade_date),
    KEY idx_trade_date (trade_date),
    KEY idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票日线行情表';

CREATE TABLE IF NOT EXISTS fact_adj_factor (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    ts_code VARCHAR(20) NOT NULL COMMENT '统一股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    adj_factor DECIMAL(20,8) DEFAULT NULL COMMENT '复权因子',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_ts_code_trade_date (ts_code, trade_date),
    KEY idx_trade_date (trade_date),
    KEY idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票复权因子表';
