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

CREATE TABLE IF NOT EXISTS tracking_start (
  singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  start_date DATETIME NULL,
  last_updated DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- New tracks (track name + optional reference URL, genre, release year, energy)
CREATE TABLE IF NOT EXISTS new_tracks (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  track VARCHAR(512) NOT NULL,
  reference_url TEXT NULL,
  genre VARCHAR(512) NULL,
  release_year SMALLINT UNSIGNED NULL,
  energy DECIMAL(4,3) NULL,
  UNIQUE KEY uq_new_tracks_track (track(191))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Existing database? Run once:
-- ALTER TABLE new_tracks ADD COLUMN genre VARCHAR(512) NULL AFTER reference_url;
-- ALTER TABLE new_tracks ADD COLUMN release_year SMALLINT UNSIGNED NULL AFTER genre;
-- ALTER TABLE new_tracks ADD COLUMN energy DECIMAL(4,3) NULL AFTER release_year;
-- DROP TABLE IF EXISTS play_counts;

INSERT IGNORE INTO destination_config (singleton, playlist_id) VALUES (1, '');
INSERT IGNORE INTO tracking_start (singleton, start_date, last_updated) VALUES (1, NULL, NULL);
