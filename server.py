"""
Steam Games MCP Server
FastMCP server providing tools for querying and analyzing Steam games dataset
"""

from fastmcp import FastMCP
import mysql.connector
from mysql.connector import Error
from typing import Optional
from db.config import DB_CONFIG

# Create MCP Server
mcp = FastMCP(
    name="Steam Games MCP Server",
    instructions="""
    This MCP server provides tools for querying and analyzing a dataset of 20,000 Steam games.
    
    Available data includes:
    - Game metadata (name, release date, price, age requirements)
    - Platform support (Windows/macOS/Linux)
    - Developers and publishers
    - Categories, genres, and tags
    - User feedback (positive/negative reviews, recommendations)
    - Playtime statistics (average and median playtime)
    - Metacritic scores
    
    Use the tools to filter, aggregate, and compare games based on various criteria.
    """
)


def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise Exception(f"Database connection failed: {e}")


def execute_query(sql: str, params: tuple = None) -> list[dict]:
    """Execute a query and return results as list of dicts"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()


# ============ SEARCH & FILTER TOOLS ============

@mcp.tool
def search_games(
    name: Optional[str] = None,
    genre: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_positive_reviews: Optional[int] = None,
    platform: Optional[str] = None,
    limit: int = 20
) -> list[dict]:
    """
    Search for games with various filters.
    
    Args:
        name: Search by game name (partial match)
        genre: Filter by genre (e.g., "Action", "RPG", "Indie")
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        min_positive_reviews: Minimum number of positive reviews
        platform: Filter by platform ("windows", "mac", "linux")
        limit: Maximum number of results (default 20, max 100)
    
    Returns:
        List of games matching the criteria
    """
    conditions = []
    params = []
    
    if name:
        conditions.append("name LIKE %s")
        params.append(f"%{name}%")
    
    if genre:
        conditions.append("genres LIKE %s")
        params.append(f"%{genre}%")
    
    if min_price is not None:
        conditions.append("price >= %s")
        params.append(min_price)
    
    if max_price is not None:
        conditions.append("price <= %s")
        params.append(max_price)
    
    if min_positive_reviews is not None:
        conditions.append("positive_reviews >= %s")
        params.append(min_positive_reviews)
    
    if platform:
        platform = platform.lower()
        if platform == "windows":
            conditions.append("windows = TRUE")
        elif platform == "mac":
            conditions.append("mac = TRUE")
        elif platform == "linux":
            conditions.append("linux = TRUE")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    limit = min(limit, 100)
    
    sql = f"""
        SELECT app_id, name, release_date, price, 
               positive_reviews, negative_reviews, 
               genres, developers, publishers,
               windows, mac, linux
        FROM games 
        WHERE {where_clause}
        ORDER BY positive_reviews DESC
        LIMIT %s
    """
    params.append(limit)
    
    return execute_query(sql, tuple(params))


@mcp.tool
def get_game_details(app_id: int) -> dict:
    """
    Get detailed information about a specific game by its Steam App ID.
    
    Args:
        app_id: The Steam application ID
    
    Returns:
        Complete game details including all metadata
    """
    sql = """
        SELECT * FROM games WHERE app_id = %s
    """
    results = execute_query(sql, (app_id,))
    return results[0] if results else {"error": "Game not found"}


# ============ AGGREGATION TOOLS ============

@mcp.tool
def get_price_statistics() -> dict:
    """
    Get overall price statistics for all games in the dataset.
    
    Returns:
        Dictionary with average, min, max, median prices and distribution by price range
    """
    sql = """
        SELECT 
            COUNT(*) as total_games,
            ROUND(AVG(price), 2) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price,
            SUM(CASE WHEN price = 0 THEN 1 ELSE 0 END) as free_games,
            SUM(CASE WHEN price > 0 AND price <= 5 THEN 1 ELSE 0 END) as under_5,
            SUM(CASE WHEN price > 5 AND price <= 20 THEN 1 ELSE 0 END) as between_5_20,
            SUM(CASE WHEN price > 20 AND price <= 60 THEN 1 ELSE 0 END) as between_20_60,
            SUM(CASE WHEN price > 60 THEN 1 ELSE 0 END) as above_60
        FROM games
        WHERE price IS NOT NULL
    """
    results = execute_query(sql)
    return results[0] if results else {}


@mcp.tool
def get_price_trend_by_year() -> list[dict]:
    """
    Analyze how average game prices have changed over the years.
    
    Returns:
        List of yearly statistics: year, count, average price, and comparison to overall average
    """
    sql = """
        SELECT 
            release_year,
            COUNT(*) as game_count,
            ROUND(AVG(price), 2) as avg_price,
            ROUND(AVG(price) - (SELECT AVG(price) FROM games WHERE price > 0), 2) as diff_from_overall
        FROM games
        WHERE release_year IS NOT NULL 
          AND release_year >= 2000
          AND price > 0
        GROUP BY release_year
        ORDER BY release_year
    """
    return execute_query(sql)


@mcp.tool
def get_genre_statistics(top_n: int = 15) -> list[dict]:
    """
    Get statistics for game genres including count, average price, and playtime.
    
    Args:
        top_n: Number of top genres to return (default 15)
    
    Returns:
        List of genre statistics sorted by game count
    """
    # Note: This analyzes the genres column which may contain multiple genres
    sql = """
        SELECT 
            g.name as genre,
            COUNT(DISTINCT gg.game_id) as game_count,
            ROUND(AVG(gm.price), 2) as avg_price,
            ROUND(AVG(gm.avg_playtime_forever), 0) as avg_playtime_minutes,
            ROUND(AVG(gm.positive_reviews), 0) as avg_positive_reviews
        FROM genres g
        JOIN game_genres gg ON g.id = gg.genre_id
        JOIN games gm ON gg.game_id = gm.app_id
        GROUP BY g.name
        ORDER BY game_count DESC
        LIMIT %s
    """
    return execute_query(sql, (top_n,))


@mcp.tool
def get_genre_playtime_analysis() -> list[dict]:
    """
    Analyze which game genres have the longest average playtime and their price correlation.
    
    Returns:
        List of genres sorted by average playtime with price comparison
    """
    sql = """
        SELECT 
            g.name as genre,
            COUNT(DISTINCT gg.game_id) as game_count,
            ROUND(AVG(gm.avg_playtime_forever) / 60, 1) as avg_playtime_hours,
            ROUND(AVG(gm.price), 2) as avg_price,
            ROUND(AVG(gm.price) / NULLIF(AVG(gm.avg_playtime_forever) / 60, 0), 2) as price_per_hour
        FROM genres g
        JOIN game_genres gg ON g.id = gg.genre_id
        JOIN games gm ON gg.game_id = gm.app_id
        WHERE gm.avg_playtime_forever > 0
        GROUP BY g.name
        HAVING game_count >= 50
        ORDER BY avg_playtime_hours DESC
        LIMIT 20
    """
    return execute_query(sql)


# ============ COMPARISON TOOLS ============

@mcp.tool
def compare_platform_reviews(include_multiplatform: bool = True) -> dict:
    """
    Compare user reviews between different platforms.
    
    Args:
        include_multiplatform: Whether to include games available on multiple platforms
    
    Returns:
        Review statistics for Windows-only, Mac-supporting, and Linux-supporting games
    """
    results = {}
    
    # Windows only games
    sql_windows = """
        SELECT 
            'Windows Only' as platform,
            COUNT(*) as game_count,
            ROUND(AVG(positive_reviews), 0) as avg_positive,
            ROUND(AVG(negative_reviews), 0) as avg_negative,
            ROUND(AVG(positive_reviews) / NULLIF(AVG(positive_reviews) + AVG(negative_reviews), 0) * 100, 1) as positive_ratio
        FROM games
        WHERE windows = TRUE AND mac = FALSE AND linux = FALSE
    """
    results['windows_only'] = execute_query(sql_windows)[0]
    
    # Games with Linux support
    sql_linux = """
        SELECT 
            'Linux Support' as platform,
            COUNT(*) as game_count,
            ROUND(AVG(positive_reviews), 0) as avg_positive,
            ROUND(AVG(negative_reviews), 0) as avg_negative,
            ROUND(AVG(positive_reviews) / NULLIF(AVG(positive_reviews) + AVG(negative_reviews), 0) * 100, 1) as positive_ratio
        FROM games
        WHERE linux = TRUE
    """
    results['linux_support'] = execute_query(sql_linux)[0]
    
    # Games with Mac support
    sql_mac = """
        SELECT 
            'Mac Support' as platform,
            COUNT(*) as game_count,
            ROUND(AVG(positive_reviews), 0) as avg_positive,
            ROUND(AVG(negative_reviews), 0) as avg_negative,
            ROUND(AVG(positive_reviews) / NULLIF(AVG(positive_reviews) + AVG(negative_reviews), 0) * 100, 1) as positive_ratio
        FROM games
        WHERE mac = TRUE
    """
    results['mac_support'] = execute_query(sql_mac)[0]
    
    return results


@mcp.tool
def analyze_reviews_vs_recommendations() -> dict:
    """
    Analyze the correlation between recommendations and positive/negative review ratios.
    
    Returns:
        Statistics showing relationship between recommendation counts and review ratios
    """
    sql = """
        SELECT 
            CASE 
                WHEN recommendations = 0 THEN '0 recommendations'
                WHEN recommendations BETWEEN 1 AND 100 THEN '1-100 recommendations'
                WHEN recommendations BETWEEN 101 AND 1000 THEN '101-1000 recommendations'
                WHEN recommendations > 1000 THEN '1000+ recommendations'
            END as recommendation_tier,
            COUNT(*) as game_count,
            ROUND(AVG(positive_reviews), 0) as avg_positive,
            ROUND(AVG(negative_reviews), 0) as avg_negative,
            ROUND(AVG(positive_reviews) / NULLIF(AVG(positive_reviews) + AVG(negative_reviews), 0) * 100, 1) as positive_ratio
        FROM games
        WHERE positive_reviews + negative_reviews > 0
        GROUP BY recommendation_tier
        ORDER BY avg_positive DESC
    """
    return execute_query(sql)


@mcp.tool
def get_publisher_satisfaction_ranking(min_games: int = 5, top_n: int = 20) -> list[dict]:
    """
    Find publishers with consistently high player satisfaction.
    
    Args:
        min_games: Minimum number of games a publisher must have (default 5)
        top_n: Number of top publishers to return (default 20)
    
    Returns:
        Ranked list of publishers by average positive review ratio
    """
    sql = """
        SELECT 
            publishers,
            COUNT(*) as game_count,
            ROUND(AVG(positive_reviews), 0) as avg_positive,
            ROUND(AVG(negative_reviews), 0) as avg_negative,
            ROUND(AVG(positive_reviews) / NULLIF(AVG(positive_reviews) + AVG(negative_reviews), 0) * 100, 1) as positive_ratio,
            ROUND(AVG(price), 2) as avg_price
        FROM games
        WHERE publishers IS NOT NULL 
          AND publishers != ''
          AND positive_reviews + negative_reviews >= 10
        GROUP BY publishers
        HAVING game_count >= %s
        ORDER BY positive_ratio DESC, avg_positive DESC
        LIMIT %s
    """
    return execute_query(sql, (min_games, top_n))


@mcp.tool
def analyze_discount_patterns() -> dict:
    """
    Analyze discount patterns by game age - are older games discounted more heavily?
    
    Returns:
        Discount statistics grouped by game age (years since release)
    """
    sql = """
        SELECT 
            CASE 
                WHEN YEAR(CURDATE()) - release_year = 0 THEN 'New (this year)'
                WHEN YEAR(CURDATE()) - release_year BETWEEN 1 AND 2 THEN '1-2 years old'
                WHEN YEAR(CURDATE()) - release_year BETWEEN 3 AND 5 THEN '3-5 years old'
                WHEN YEAR(CURDATE()) - release_year > 5 THEN '5+ years old'
            END as age_group,
            COUNT(*) as game_count,
            ROUND(AVG(discount), 1) as avg_discount,
            SUM(CASE WHEN discount > 50 THEN 1 ELSE 0 END) as large_discounts,
            ROUND(AVG(price), 2) as avg_price
        FROM games
        WHERE release_year IS NOT NULL AND release_year > 2000
        GROUP BY age_group
        ORDER BY avg_discount DESC
    """
    return execute_query(sql)


# ============ ADVANCED ANALYSIS TOOLS ============

@mcp.tool
def get_top_rated_games(
    min_reviews: int = 100,
    genre: Optional[str] = None,
    limit: int = 20
) -> list[dict]:
    """
    Get top-rated games based on positive review ratio.
    
    Args:
        min_reviews: Minimum total reviews required (default 100)
        genre: Optional genre filter
        limit: Number of results (default 20)
    
    Returns:
        List of top-rated games with review statistics
    """
    conditions = ["positive_reviews + negative_reviews >= %s"]
    params = [min_reviews]
    
    if genre:
        conditions.append("genres LIKE %s")
        params.append(f"%{genre}%")
    
    where_clause = " AND ".join(conditions)
    
    sql = f"""
        SELECT 
            app_id, name, release_year, price, genres,
            positive_reviews, negative_reviews,
            ROUND(positive_reviews * 100.0 / (positive_reviews + negative_reviews), 1) as positive_ratio,
            developers, publishers
        FROM games
        WHERE {where_clause}
        ORDER BY positive_ratio DESC, positive_reviews DESC
        LIMIT %s
    """
    params.append(limit)
    
    return execute_query(sql, tuple(params))


@mcp.tool
def get_dataset_summary() -> dict:
    """
    Get a comprehensive summary of the entire dataset.
    
    Returns:
        Overview statistics including counts, averages, and distributions
    """
    summary = {}
    
    # Basic counts
    counts_sql = """
        SELECT 
            COUNT(*) as total_games,
            SUM(CASE WHEN price = 0 THEN 1 ELSE 0 END) as free_games,
            SUM(CASE WHEN windows = TRUE THEN 1 ELSE 0 END) as windows_games,
            SUM(CASE WHEN mac = TRUE THEN 1 ELSE 0 END) as mac_games,
            SUM(CASE WHEN linux = TRUE THEN 1 ELSE 0 END) as linux_games,
            MIN(release_year) as earliest_year,
            MAX(release_year) as latest_year
        FROM games
    """
    summary['counts'] = execute_query(counts_sql)[0]
    
    # Averages
    avg_sql = """
        SELECT 
            ROUND(AVG(price), 2) as avg_price,
            ROUND(AVG(positive_reviews), 0) as avg_positive_reviews,
            ROUND(AVG(negative_reviews), 0) as avg_negative_reviews,
            ROUND(AVG(avg_playtime_forever) / 60, 1) as avg_playtime_hours,
            ROUND(AVG(metacritic_score), 0) as avg_metacritic
        FROM games
        WHERE price > 0
    """
    summary['averages'] = execute_query(avg_sql)[0]
    
    # Genre count
    genre_sql = "SELECT COUNT(DISTINCT name) as total_genres FROM genres"
    summary['genre_count'] = execute_query(genre_sql)[0]['total_genres']
    
    return summary


if __name__ == "__main__":
    # Run with Streamable HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")
