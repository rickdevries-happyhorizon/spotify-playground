-- Spotify playground — MySQL 5.7+ schema (utf8mb4)
-- Create database and user (adjust credentials):
--   CREATE DATABASE spotify_playground CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   GRANT ALL ON spotify_playground.* TO 'spotify'@'localhost' IDENTIFIED BY 'your_password';
--   FLUSH PRIVILEGES;
-- Then:
--   mysql -u spotify -p spotify_playground < schema.sql

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS destination_config (
  singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  playlist_id VARCHAR(64) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS source_playlists (
  sort_order INT UNSIGNED NOT NULL,
  playlist_id VARCHAR(64) NOT NULL,
  PRIMARY KEY (playlist_id),
  KEY idx_source_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tracking_playlists (
  sort_order INT UNSIGNED NOT NULL,
  playlist_id VARCHAR(64) NOT NULL,
  PRIMARY KEY (playlist_id),
  KEY idx_tracking_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS historical_tracks (
  playlist_key VARCHAR(64) NOT NULL,
  track_uri VARCHAR(255) NOT NULL,
  PRIMARY KEY (playlist_key, track_uri),
  KEY idx_hist_playlist (playlist_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS play_counts (
  track_uri VARCHAR(255) NOT NULL,
  track_name VARCHAR(512) NOT NULL DEFAULT '',
  artists TEXT,
  play_count INT UNSIGNED NOT NULL DEFAULT 0,
  first_played DATETIME NULL,
  last_played DATETIME NULL,
  PRIMARY KEY (track_uri)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tracking_start (
  singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  start_date DATETIME NULL,
  last_updated DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO destination_config (singleton, playlist_id) VALUES (1, '');
INSERT IGNORE INTO tracking_start (singleton, start_date, last_updated) VALUES (1, NULL, NULL);
