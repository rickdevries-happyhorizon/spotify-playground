<?php

declare(strict_types=1);

final class TrackStore
{
    private const TRACK_SELECT =
        'SELECT nt.id, nt.track, nt.reference_url, nt.playlist_id, nt.release_year, '
        . 'nt.copy_title_count, nt.image_url, p.name AS genre, '
        . 'p.artwork_url AS playlist_artwork_url '
        . 'FROM new_tracks nt '
        . 'LEFT JOIN playlist p ON p.id = nt.playlist_id ';

    public static function loadAll(?string $genre = null): array
    {
        self::ensureSchema();

        $stmt = Db::connection()->query(self::TRACK_SELECT . 'ORDER BY nt.track ASC');

        $tracks = [];
        foreach ($stmt->fetchAll() as $row) {
            $trackGenre = !empty($row['genre']) ? $row['genre'] : null;
            if ($genre !== null) {
                if ($genre === 'Uncategorized') {
                    if ($trackGenre !== null) {
                        continue;
                    }
                } elseif ($trackGenre !== $genre) {
                    continue;
                }
            }

            $tracks[] = self::mapTrackRow($row);
        }

        return $tracks;
    }

    public static function loadGenres(): array
    {
        $tracks = self::loadAll();
        $counts = [];

        foreach ($tracks as $track) {
            $name = trim((string) ($track['genre'] ?? ''));
            $key = $name !== '' ? $name : '__uncategorized__';
            $counts[$key] = ($counts[$key] ?? 0) + 1;
        }

        uksort($counts, static function (string $left, string $right): int {
            if ($left === '__uncategorized__') {
                return 1;
            }

            if ($right === '__uncategorized__') {
                return -1;
            }

            return strcasecmp($left, $right);
        });

        $genres = [];
        foreach ($counts as $key => $count) {
            $slug = $key === '__uncategorized__' ? 'Uncategorized' : $key;
            $label = $key === '__uncategorized__' ? 'Uncategorized' : $key;
            $imageUrl = $key === '__uncategorized__'
                ? null
                : self::resolveGenreImage($slug, null, $tracks);

            $genres[] = [
                'slug' => $slug,
                'label' => $label,
                'track_count' => $count,
                'image_url' => $imageUrl,
            ];
        }

        return [
            'genres' => $genres,
            'total' => count($tracks),
        ];
    }

    public static function resolveGenreImage(
        string $genre,
        ?array $genreImages = null,
        ?array $tracks = null
    ): ?string {
        $genreName = trim($genre);
        if ($genreName === '') {
            return null;
        }

        self::ensureSchema();

        $stmt = Db::connection()->prepare(
            'SELECT artwork_url FROM playlist WHERE name = :name LIMIT 1'
        );
        $stmt->execute(['name' => $genreName]);
        $row = $stmt->fetch();
        if (!empty($row['artwork_url'])) {
            return $row['artwork_url'];
        }

        $images = $genreImages ?? self::loadGenreImages();
        if (isset($images[$genreName])) {
            return $images[$genreName];
        }

        $trackRows = $tracks ?? self::loadAll();
        foreach ($trackRows as $track) {
            if (trim((string) ($track['genre'] ?? '')) !== $genreName) {
                continue;
            }

            if (!empty($track['playlist_artwork_url'])) {
                return $track['playlist_artwork_url'];
            }

            if (!empty($track['image_url'])) {
                return $track['image_url'];
            }
        }

        return null;
    }

    public static function create(string $track, ?string $referenceUrl = null, ?string $genre = null): array
    {
        self::ensureSchema();

        $trackName = TrackNormalizer::normalize(trim($track));
        if ($trackName === '') {
            throw new InvalidArgumentException('Track name is required');
        }

        $url = UrlNormalizer::normalize($referenceUrl);
        $genreValue = trim((string) ($genre ?? ''));
        $genreValue = $genreValue !== '' ? $genreValue : null;
        $playlistId = $genreValue !== null ? self::upsertPlaylist($genreValue) : null;
        $pdo = Db::connection();

        try {
            $stmt = $pdo->prepare(
                'INSERT INTO new_tracks (track, reference_url, playlist_id) '
                . 'VALUES (:track, :reference_url, :playlist_id)'
            );
            $stmt->execute([
                'track' => $trackName,
                'reference_url' => $url,
                'playlist_id' => $playlistId,
            ]);
        } catch (PDOException $e) {
            if ((int) ($e->errorInfo[1] ?? 0) === 1062) {
                throw new InvalidArgumentException('Track already exists');
            }

            throw $e;
        }

        return [
            'id' => (int) $pdo->lastInsertId(),
            'track' => $trackName,
            'reference_url' => $url,
            'playlist_id' => $playlistId,
            'genre' => $genreValue,
            'release_year' => null,
            'copy_title_count' => 0,
            'image_url' => null,
            'playlist_artwork_url' => null,
        ];
    }

    public static function incrementCopyTitleCount(int $trackId): ?int
    {
        self::ensureSchema();

        $pdo = Db::connection();
        $stmt = $pdo->prepare(
            'UPDATE new_tracks SET copy_title_count = copy_title_count + 1 WHERE id = :id'
        );
        $stmt->execute(['id' => $trackId]);

        if ($stmt->rowCount() === 0) {
            return null;
        }

        $countStmt = $pdo->prepare('SELECT copy_title_count FROM new_tracks WHERE id = :id');
        $countStmt->execute(['id' => $trackId]);
        $row = $countStmt->fetch();

        return $row ? (int) $row['copy_title_count'] : null;
    }

    public static function updateReferenceUrl(int $trackId, ?string $referenceUrl): ?string
    {
        $url = UrlNormalizer::normalize($referenceUrl);
        $stmt = Db::connection()->prepare(
            'UPDATE new_tracks SET reference_url = :reference_url WHERE id = :id'
        );
        $stmt->execute([
            'reference_url' => $url,
            'id' => $trackId,
        ]);

        if ($stmt->rowCount() === 0) {
            return null;
        }

        return $url;
    }

    public static function delete(int $trackId): bool
    {
        $stmt = Db::connection()->prepare('DELETE FROM new_tracks WHERE id = :id');
        $stmt->execute(['id' => $trackId]);

        return $stmt->rowCount() > 0;
    }

    public static function upsertPlaylist(string $name, ?string $artworkUrl = null): int
    {
        self::ensureSchema();

        $playlistName = trim($name);
        if ($playlistName === '') {
            throw new InvalidArgumentException('Playlist name is required');
        }

        $url = $artworkUrl !== null ? trim($artworkUrl) : null;
        if ($url === '') {
            $url = null;
        }

        $pdo = Db::connection();
        $stmt = $pdo->prepare('SELECT id, artwork_url FROM playlist WHERE name = :name LIMIT 1');
        $stmt->execute(['name' => $playlistName]);
        $row = $stmt->fetch();

        if ($row) {
            $playlistId = (int) $row['id'];
            if ($url !== null && $url !== ($row['artwork_url'] ?? '')) {
                $update = $pdo->prepare('UPDATE playlist SET artwork_url = :artwork_url WHERE id = :id');
                $update->execute([
                    'artwork_url' => $url,
                    'id' => $playlistId,
                ]);
            }

            return $playlistId;
        }

        $insert = $pdo->prepare(
            'INSERT INTO playlist (name, artwork_url) VALUES (:name, :artwork_url)'
        );
        $insert->execute([
            'name' => $playlistName,
            'artwork_url' => $url,
        ]);

        return (int) $pdo->lastInsertId();
    }

    private static function mapTrackRow(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'track' => $row['track'],
            'reference_url' => $row['reference_url'] ?: null,
            'playlist_id' => isset($row['playlist_id']) ? (int) $row['playlist_id'] : null,
            'genre' => !empty($row['genre']) ? $row['genre'] : null,
            'release_year' => isset($row['release_year']) ? (int) $row['release_year'] : null,
            'copy_title_count' => (int) ($row['copy_title_count'] ?? 0),
            'image_url' => !empty($row['image_url']) ? $row['image_url'] : null,
            'playlist_artwork_url' => !empty($row['playlist_artwork_url']) ? $row['playlist_artwork_url'] : null,
        ];
    }

    private static function loadGenreImages(): array
    {
        self::ensureSchema();

        $stmt = Db::connection()->query(
            'SELECT name, artwork_url FROM playlist WHERE artwork_url IS NOT NULL'
        );
        $images = [];
        foreach ($stmt->fetchAll() as $row) {
            if (!empty($row['name']) && !empty($row['artwork_url'])) {
                $images[$row['name']] = $row['artwork_url'];
            }
        }

        return $images;
    }

    private static function ensureSchema(): void
    {
        self::ensurePlaylistTable();
        self::ensureOptionalColumns();
        self::migrateLegacyGenreData();
        self::dropGenreColumn();
        self::backfillPlaylistArtwork();
    }

    private static function ensurePlaylistTable(): void
    {
        Db::connection()->exec(
            'CREATE TABLE IF NOT EXISTS playlist ('
            . 'id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            . 'spotify_id VARCHAR(64) NULL, '
            . 'name VARCHAR(512) NOT NULL, '
            . 'artwork_url TEXT NULL, '
            . 'UNIQUE KEY uq_playlist_spotify_id (spotify_id), '
            . 'UNIQUE KEY uq_playlist_name (name(191))'
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );
        self::ensurePlaylistSpotifyIdColumn();
    }

    private static function ensurePlaylistSpotifyIdColumn(): void
    {
        $pdo = Db::connection();
        $stmt = $pdo->query(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            . "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'playlist' "
            . "AND COLUMN_NAME = 'spotify_id'"
        );
        $row = $stmt->fetch();
        if ((int) ($row['cnt'] ?? 0) === 0) {
            $pdo->exec('ALTER TABLE playlist ADD COLUMN spotify_id VARCHAR(64) NULL AFTER id');
            $pdo->exec('ALTER TABLE playlist ADD UNIQUE KEY uq_playlist_spotify_id (spotify_id)');
        }
    }

    private static function ensureOptionalColumns(): void
    {
        self::ensureColumn(
            'playlist_id',
            'ALTER TABLE new_tracks ADD COLUMN playlist_id INT UNSIGNED NULL AFTER reference_url'
        );
        self::ensureColumn(
            'release_year',
            'ALTER TABLE new_tracks ADD COLUMN release_year SMALLINT UNSIGNED NULL AFTER playlist_id'
        );
        self::ensureColumn(
            'copy_title_count',
            'ALTER TABLE new_tracks ADD COLUMN copy_title_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER energy'
        );
        self::ensureColumn(
            'image_url',
            'ALTER TABLE new_tracks ADD COLUMN image_url TEXT NULL AFTER copy_title_count'
        );
        self::ensureGenreImagesTable();
    }

    private static function migrateLegacyGenreData(): void
    {
        if (!self::columnExists('genre')) {
            return;
        }

        $pdo = Db::connection();
        self::ensureGenreImagesTable();
        $genreImages = $pdo->query('SELECT genre, image_url FROM genre_images')->fetchAll();
        foreach ($genreImages as $row) {
            $genre = trim((string) ($row['genre'] ?? ''));
            $imageUrl = trim((string) ($row['image_url'] ?? ''));
            if ($genre !== '') {
                self::upsertPlaylist($genre, $imageUrl !== '' ? $imageUrl : null);
            }
        }

        $genres = $pdo->query(
            "SELECT DISTINCT genre FROM new_tracks WHERE genre IS NOT NULL AND TRIM(genre) != ''"
        )->fetchAll();
        foreach ($genres as $row) {
            $genre = trim((string) ($row['genre'] ?? ''));
            if ($genre !== '') {
                self::upsertPlaylist($genre, null);
            }
        }

        $pdo->exec(
            'UPDATE new_tracks nt '
            . 'INNER JOIN playlist p ON p.name = nt.genre '
            . 'SET nt.playlist_id = p.id '
            . 'WHERE nt.playlist_id IS NULL AND nt.genre IS NOT NULL'
        );
    }

    private static function dropGenreColumn(): void
    {
        if (!self::columnExists('genre')) {
            return;
        }

        Db::connection()->exec('ALTER TABLE new_tracks DROP COLUMN genre');
    }

    private static function backfillPlaylistArtwork(): void
    {
        Db::connection()->exec(
            'UPDATE playlist p '
            . 'INNER JOIN ('
            . '  SELECT nt.playlist_id, MIN(nt.id) AS first_id '
            . '  FROM new_tracks nt '
            . '  WHERE nt.image_url IS NOT NULL AND nt.playlist_id IS NOT NULL '
            . '  GROUP BY nt.playlist_id'
            . ') picked ON picked.playlist_id = p.id '
            . 'INNER JOIN new_tracks nt ON nt.id = picked.first_id '
            . "SET p.artwork_url = nt.image_url "
            . "WHERE p.artwork_url IS NULL OR TRIM(p.artwork_url) = ''"
        );
    }

    private static function ensureGenreImagesTable(): void
    {
        Db::connection()->exec(
            'CREATE TABLE IF NOT EXISTS genre_images ('
            . 'genre VARCHAR(512) NOT NULL PRIMARY KEY, '
            . 'image_url TEXT NOT NULL'
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );
    }

    private static function columnExists(string $columnName): bool
    {
        $pdo = Db::connection();
        $stmt = $pdo->query(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            . "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            . "AND COLUMN_NAME = '" . $columnName . "'"
        );
        $row = $stmt->fetch();

        return (int) ($row['cnt'] ?? 0) > 0;
    }

    private static function ensureColumn(string $columnName, string $alterSql): void
    {
        if (!self::columnExists($columnName)) {
            Db::connection()->exec($alterSql);
        }
    }
}
