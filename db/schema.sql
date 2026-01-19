-- Steam Games MCP Analysis Database Schema
-- MySQL 8.x

-- 主游戏表
CREATE TABLE IF NOT EXISTS games (
    app_id INT PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    release_date DATE,
    release_year INT,
    estimated_owners VARCHAR(50),
    peak_ccu INT DEFAULT 0,
    required_age INT DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0.00,
    discount INT DEFAULT 0,
    dlc_count INT DEFAULT 0,
    about_the_game TEXT,
    supported_languages TEXT,
    full_audio_languages TEXT,
    reviews TEXT,
    header_image VARCHAR(500),
    website VARCHAR(500),
    support_url VARCHAR(500),
    support_email VARCHAR(200),
    windows BOOLEAN DEFAULT FALSE,
    mac BOOLEAN DEFAULT FALSE,
    linux BOOLEAN DEFAULT FALSE,
    metacritic_score INT DEFAULT 0,
    metacritic_url VARCHAR(500),
    user_score INT DEFAULT 0,
    positive_reviews INT DEFAULT 0,
    negative_reviews INT DEFAULT 0,
    score_rank VARCHAR(50),
    achievements INT DEFAULT 0,
    recommendations INT DEFAULT 0,
    notes TEXT,
    avg_playtime_forever INT DEFAULT 0,
    avg_playtime_2weeks INT DEFAULT 0,
    median_playtime_forever INT DEFAULT 0,
    median_playtime_2weeks INT DEFAULT 0,
    developers TEXT,
    publishers TEXT,
    categories TEXT,
    genres TEXT,
    tags TEXT,
    screenshots TEXT,
    movies TEXT,
    INDEX idx_release_year (release_year),
    INDEX idx_price (price),
    INDEX idx_positive_reviews (positive_reviews),
    INDEX idx_negative_reviews (negative_reviews),
    INDEX idx_metacritic (metacritic_score),
    FULLTEXT idx_name (name),
    FULLTEXT idx_developers (developers),
    FULLTEXT idx_publishers (publishers),
    FULLTEXT idx_genres (genres),
    FULLTEXT idx_tags (tags)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 游戏类型表 (归一化)
CREATE TABLE IF NOT EXISTS genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 游戏-类型关联表
CREATE TABLE IF NOT EXISTS game_genres (
    game_id INT,
    genre_id INT,
    PRIMARY KEY (game_id, genre_id),
    FOREIGN KEY (game_id) REFERENCES games(app_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 游戏标签表 (归一化)
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 游戏-标签关联表
CREATE TABLE IF NOT EXISTS game_tags (
    game_id INT,
    tag_id INT,
    PRIMARY KEY (game_id, tag_id),
    FOREIGN KEY (game_id) REFERENCES games(app_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 游戏分类表 (归一化)
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 游戏-分类关联表
CREATE TABLE IF NOT EXISTS game_categories (
    game_id INT,
    category_id INT,
    PRIMARY KEY (game_id, category_id),
    FOREIGN KEY (game_id) REFERENCES games(app_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB;
