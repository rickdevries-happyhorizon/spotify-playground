-- Spotify playground — MySQL 5.7+ schema (utf8mb4)
-- Create database and user (adjust credentials):
--   CREATE DATABASE spotify_playground CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   GRANT ALL ON spotify_playground.* TO 'spotify'@'localhost' IDENTIFIED BY 'your_password';
--   FLUSH PRIVILEGES;
-- Then:
--   mysql -u spotify -p spotify_playground < schema.sql

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS playlist (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  spotify_id VARCHAR(64) NULL,
  name VARCHAR(512) NOT NULL,
  artwork_url TEXT NULL,
  UNIQUE KEY uq_playlist_spotify_id (spotify_id),
  UNIQUE KEY uq_playlist_name (name(191))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS destination_config (
  singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  playlist_ref_id INT UNSIGNED NULL,
  CONSTRAINT fk_destination_playlist FOREIGN KEY (playlist_ref_id) REFERENCES playlist(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS playlist_source (
  sort_order INT UNSIGNED NOT NULL,
  playlist_ref_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (playlist_ref_id),
  KEY idx_playlist_source_sort (sort_order),
  CONSTRAINT fk_playlist_source FOREIGN KEY (playlist_ref_id) REFERENCES playlist(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS playlist_tracking (
  sort_order INT UNSIGNED NOT NULL,
  playlist_ref_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (playlist_ref_id),
  KEY idx_playlist_tracking_sort (sort_order),
  CONSTRAINT fk_playlist_tracking FOREIGN KEY (playlist_ref_id) REFERENCES playlist(id) ON DELETE CASCADE
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

CREATE TABLE IF NOT EXISTS new_tracks (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  track VARCHAR(512) NOT NULL,
  reference_url TEXT NULL,
  playlist_id INT UNSIGNED NULL,
  release_year SMALLINT UNSIGNED NULL,
  energy DECIMAL(4,3) NULL,
  copy_title_count INT UNSIGNED NOT NULL DEFAULT 0,
  image_url TEXT NULL,
  UNIQUE KEY uq_new_tracks_track (track(191)),
  KEY idx_new_tracks_playlist (playlist_id),
  CONSTRAINT fk_new_tracks_playlist FOREIGN KEY (playlist_id) REFERENCES playlist(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS genre_images (
  genre VARCHAR(512) NOT NULL PRIMARY KEY,
  image_url TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Existing database? Run migrations via the app, or manually:
-- 1. Add spotify_id to playlist; create playlist_source / playlist_tracking / new destination_config
-- 2. Migrate rows from source_playlists, tracking_playlists, and destination_config (Spotify IDs)
-- 3. Drop legacy source_playlists and tracking_playlists tables after migration

INSERT IGNORE INTO destination_config (singleton, playlist_ref_id) VALUES (1, NULL);
INSERT IGNORE INTO tracking_start (singleton, start_date, last_updated) VALUES (1, NULL, NULL);
