"""
Steam Games Dataset Loader
Loads games_sample.csv into MySQL database
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import re
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.config import DB_CONFIG


def parse_date(date_str: str) -> tuple[str | None, int | None]:
    """Parse date string to MySQL date format and extract year"""
    if not date_str or pd.isna(date_str):
        return None, None
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    formats = [
        "%b %d, %Y",  # "Oct 29, 2024"
        "%B %d, %Y",  # "October 29, 2024"
        "%Y-%m-%d",   # "2024-10-29"
        "%d %b, %Y",  # "29 Oct, 2024"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d"), dt.year
        except ValueError:
            continue
    
    # Try to extract year only
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        year = int(year_match.group())
        return f"{year}-01-01", year
    
    return None, None


def parse_bool(value) -> bool:
    """Parse boolean value from various formats"""
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes')


def safe_int(value, default=0) -> int:
    """Safely convert to integer"""
    if pd.isna(value):
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0) -> float:
    """Safely convert to float"""
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, max_length=None) -> str | None:
    """Safely convert to string"""
    if pd.isna(value):
        return None
    result = str(value).strip()
    if max_length and len(result) > max_length:
        result = result[:max_length]
    return result if result else None


def create_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise


def execute_schema(conn, schema_path: str):
    """Execute schema SQL file"""
    print("Creating database schema...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    cursor = conn.cursor()
    for statement in schema_sql.split(';'):
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
            except Error as e:
                print(f"Warning executing statement: {e}")
    conn.commit()
    cursor.close()
    print("Schema created successfully!")


def load_games(conn, csv_path: str, batch_size: int = 500):
    """Load games data from CSV"""
    print(f"Loading data from {csv_path}...")
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig', index_col=False)
    print(f"Total rows in CSV: {len(df)}")
    
    cursor = conn.cursor()
    
    insert_sql = """
        INSERT INTO games (
            app_id, name, release_date, release_year, estimated_owners, 
            peak_ccu, required_age, price, discount, dlc_count,
            about_the_game, supported_languages, full_audio_languages, reviews,
            header_image, website, support_url, support_email,
            windows, mac, linux,
            metacritic_score, metacritic_url, user_score,
            positive_reviews, negative_reviews, score_rank,
            achievements, recommendations, notes,
            avg_playtime_forever, avg_playtime_2weeks,
            median_playtime_forever, median_playtime_2weeks,
            developers, publishers, categories, genres, tags,
            screenshots, movies
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            price = VALUES(price),
            positive_reviews = VALUES(positive_reviews),
            negative_reviews = VALUES(negative_reviews)
    """
    
    inserted = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            release_date, release_year = parse_date(row.get('Release date'))
            
            values = (
                safe_int(row.get('AppID')),
                safe_str(row.get('Name'), 500),
                release_date,
                release_year,
                safe_str(row.get('Estimated owners'), 50),
                safe_int(row.get('Peak CCU')),
                safe_int(row.get('Required age')),
                safe_float(row.get('Price')),
                safe_int(row.get('DiscountDLC count')),  # Column seems to be named oddly
                safe_int(row.get('DLC count', 0)),
                safe_str(row.get('About the game')),
                safe_str(row.get('Supported languages')),
                safe_str(row.get('Full audio languages')),
                safe_str(row.get('Reviews')),
                safe_str(row.get('Header image'), 500),
                safe_str(row.get('Website'), 500),
                safe_str(row.get('Support url'), 500),
                safe_str(row.get('Support email'), 200),
                parse_bool(row.get('Windows')),
                parse_bool(row.get('Mac')),
                parse_bool(row.get('Linux')),
                safe_int(row.get('Metacritic score')),
                safe_str(row.get('Metacritic url'), 500),
                safe_int(row.get('User score')),
                safe_int(row.get('Positive')),
                safe_int(row.get('Negative')),
                safe_str(row.get('Score rank'), 50),
                safe_int(row.get('Achievements')),
                safe_int(row.get('Recommendations')),
                safe_str(row.get('Notes')),
                safe_int(row.get('Average playtime forever')),
                safe_int(row.get('Average playtime two weeks')),
                safe_int(row.get('Median playtime forever')),
                safe_int(row.get('Median playtime two weeks')),
                safe_str(row.get('Developers')),
                safe_str(row.get('Publishers')),
                safe_str(row.get('Categories')),
                safe_str(row.get('Genres')),
                safe_str(row.get('Tags')),
                safe_str(row.get('Screenshots')),
                safe_str(row.get('Movies')),
            )
            
            cursor.execute(insert_sql, values)
            inserted += 1
            
            if inserted % batch_size == 0:
                conn.commit()
                print(f"Inserted {inserted} rows...")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"Error row {idx}: {e}")
    
    conn.commit()
    cursor.close()
    
    print(f"\nData loading complete!")
    print(f"  Inserted: {inserted}")
    print(f"  Errors: {errors}")


def populate_normalized_tables(conn):
    """Populate normalized genre, tag, category tables"""
    print("\nPopulating normalized tables...")
    cursor = conn.cursor()
    
    # Get unique genres
    cursor.execute("SELECT DISTINCT genres FROM games WHERE genres IS NOT NULL AND genres != ''")
    all_genres = set()
    for row in cursor.fetchall():
        if row[0]:
            for genre in row[0].split(','):
                genre = genre.strip()
                if genre:
                    all_genres.add(genre)
    
    print(f"Found {len(all_genres)} unique genres")
    for genre in all_genres:
        try:
            cursor.execute("INSERT IGNORE INTO genres (name) VALUES (%s)", (genre,))
        except:
            pass
    conn.commit()
    
    # Link games to genres
    cursor.execute("SELECT app_id, genres FROM games WHERE genres IS NOT NULL")
    for app_id, genres_str in cursor.fetchall():
        if genres_str:
            for genre in genres_str.split(','):
                genre = genre.strip()
                if genre:
                    try:
                        cursor.execute("""
                            INSERT IGNORE INTO game_genres (game_id, genre_id)
                            SELECT %s, id FROM genres WHERE name = %s
                        """, (app_id, genre))
                    except:
                        pass
    conn.commit()
    
    # Similar for tags
    cursor.execute("SELECT DISTINCT tags FROM games WHERE tags IS NOT NULL AND tags != ''")
    all_tags = set()
    for row in cursor.fetchall():
        if row[0]:
            for tag in row[0].split(','):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
    
    print(f"Found {len(all_tags)} unique tags")
    for tag in all_tags:
        try:
            cursor.execute("INSERT IGNORE INTO tags (name) VALUES (%s)", (tag,))
        except:
            pass
    conn.commit()
    
    cursor.close()
    print("Normalized tables populated!")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    schema_path = os.path.join(project_dir, 'db', 'schema.sql')
    csv_path = os.path.join(project_dir, 'data', 'games_sample.csv')
    
    print("=" * 50)
    print("Steam Games Dataset Loader")
    print("=" * 50)
    
    conn = create_connection()
    print("Connected to MySQL!")
    
    execute_schema(conn, schema_path)
    load_games(conn, csv_path)
    populate_normalized_tables(conn)
    
    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM games")
    count = cursor.fetchone()[0]
    print(f"\nVerification: {count} games in database")
    cursor.close()
    
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
