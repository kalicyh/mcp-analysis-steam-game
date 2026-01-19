# Steam Games MCP Server 🎮

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.14+-green.svg)](https://github.com/jlowin/fastmcp)
[![MySQL](https://img.shields.io/badge/MySQL-8.x-orange.svg)](https://www.mysql.com/)

一个基于 **FastMCP** 构建的 Model Context Protocol (MCP) 服务器，可让 LLM 对 Steam 游戏数据集执行复杂的数据驱动查询和分析。

## ✨ 功能特性

### 🔍 搜索与过滤
- **游戏搜索** - 按名称、类型、价格范围、评价数量、平台筛选游戏
- **游戏详情** - 获取指定 Steam App ID 的完整游戏信息

### 📊 数据聚合
- **价格统计** - 获取游戏价格的平均值、中位数、最小/最大值及分布
- **年度价格趋势** - 分析游戏价格随年份的变化趋势
- **类型统计** - 游戏类型的数量、平均价格和游戏时长分析
- **类型游戏时长分析** - 哪些类型的游戏玩家玩得最久

### ⚖️ 对比分析
- **平台评价对比** - 对比 Windows、Mac、Linux 平台的用户评价
- **评价与推荐关联分析** - 分析推荐数与正/负评价比例的相关性
- **发行商满意度排名** - 找出玩家满意度最高的发行商
- **折扣模式分析** - 分析游戏年龄与折扣力度的关系

### 🏆 高级分析
- **高评分游戏** - 基于正面评价比例获取高评分游戏
- **数据集摘要** - 获取整个数据集的综合统计信息

## 📁 项目结构

```
mcp-analysis/
├── server.py              # MCP 服务器主程序
├── pyproject.toml         # 项目配置和依赖
├── data/
│   └── games_sample.csv   # Steam 游戏数据集 (~60MB)
├── db/
│   ├── config.py          # 数据库连接配置
│   └── schema.sql         # MySQL 数据库表结构
└── scripts/
    └── load_data.py       # 数据导入脚本
```

## 🚀 快速开始

### 前置要求

- Python 3.14+
- MySQL 8.x
- [uv](https://github.com/astral-sh/uv) 包管理器 (推荐)

### 1. 克隆仓库

```bash
git clone https://github.com/kalicyh/mcp-analysis.git
cd mcp-analysis
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置数据库

编辑 `db/config.py` 中的数据库连接信息：

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "game",
    "user": "root",
    "password": "your_password",
    "charset": "utf8mb4",
}
```

确保 MySQL 中已创建 `game` 数据库：

```sql
CREATE DATABASE IF NOT EXISTS game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 导入数据

```bash
uv run python scripts/load_data.py
```

此脚本将：
- 创建数据库表结构
- 从 CSV 导入游戏数据
- 填充归一化的类型、标签表

### 5. 启动 MCP 服务器

```bash
uv run python server.py
```

服务器将在 `http://0.0.0.0:8000/mcp` 启动。

## 🔌 连接 MCP 服务器

### 使用 MCP Inspector 测试

```bash
npx @modelcontextprotocol/inspector
```

### MCP 客户端配置

在你的 MCP 客户端中添加以下配置：

```json
{
  "mcpServers": {
    "steam-games": {
      "serverUrl": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 🛠️ 可用工具

| 工具名称 | 描述 |
|---------|------|
| `search_games` | 多条件搜索游戏 |
| `get_game_details` | 获取游戏详细信息 |
| `get_price_statistics` | 价格统计分析 |
| `get_price_trend_by_year` | 年度价格趋势 |
| `get_genre_statistics` | 类型统计 |
| `get_genre_playtime_analysis` | 类型游戏时长分析 |
| `compare_platform_reviews` | 平台评价对比 |
| `analyze_reviews_vs_recommendations` | 评价推荐关联分析 |
| `get_publisher_satisfaction_ranking` | 发行商满意度排名 |
| `analyze_discount_patterns` | 折扣模式分析 |
| `get_top_rated_games` | 高评分游戏 |
| `get_dataset_summary` | 数据集摘要 |

## 📊 数据库架构

### 主表 `games`
包含约 20,000+ 款 Steam 游戏的详细信息：
- 基本信息：名称、发布日期、价格、折扣
- 评价数据：正面/负面评价数、Metacritic 评分
- 游戏时长：平均/中位数游戏时长
- 平台支持：Windows、Mac、Linux
- 分类信息：类型、标签、分类

### 归一化表
- `genres` / `game_genres` - 游戏类型
- `tags` / `game_tags` - 游戏标签
- `categories` / `game_categories` - 游戏分类

## 📝 使用示例

通过 LLM 与 MCP 服务器交互的示例问题：

- "搜索所有价格低于 10 美元的 RPG 游戏"
- "哪个游戏类型的平均游戏时长最长？"
- "对比 Windows 和 Linux 平台的游戏评价"
- "列出评价最好的 20 款独立游戏"
- "分析老游戏是否折扣力度更大"

## 📄 License

MIT License
