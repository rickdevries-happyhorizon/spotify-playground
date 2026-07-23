<?php

declare(strict_types=1);

final class TrackStore
{
    public static function loadAll(): array
    {
        self::ensureOptionalColumns();

        $stmt = Db::connection()->query(
            'SELECT id, track, reference_url, genre, release_year, copy_title_count FROM new_tracks ORDER BY track ASC'
        );

        $tracks = [];
        foreach ($stmt->fetchAll() as $row) {
            $tracks[] = [
                'id' => (int) $row['id'],
                'track' => $row['track'],
                'reference_url' => $row['reference_url'] ?: null,
                'genre' => !empty($row['genre']) ? $row['genre'] : null,
                'release_year' => isset($row['release_year']) ? (int) $row['release_year'] : null,
                'copy_title_count' => (int) ($row['copy_title_count'] ?? 0),
            ];
        }

        return $tracks;
    }

    public static function create(string $track, ?string $referenceUrl = null): array
    {
        self::ensureOptionalColumns();

        $trackName = TrackNormalizer::normalize(trim($track));
        if ($trackName === '') {
            throw new InvalidArgumentException('Track name is required');
        }

        $url = UrlNormalizer::normalize($referenceUrl);
        $pdo = Db::connection();

        try {
            $stmt = $pdo->prepare(
                'INSERT INTO new_tracks (track, reference_url, genre) VALUES (:track, :reference_url, NULL)'
            );
            $stmt->execute([
                'track' => $trackName,
                'reference_url' => $url,
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
            'genre' => null,
            'release_year' => null,
            'copy_title_count' => 0,
        ];
    }

    public static function incrementCopyTitleCount(int $trackId): ?int
    {
        self::ensureOptionalColumns();

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

    private static function ensureOptionalColumns(): void
    {
        self::ensureColumn('genre', 'ALTER TABLE new_tracks ADD COLUMN genre VARCHAR(512) NULL AFTER reference_url');
        self::ensureColumn(
            'release_year',
            'ALTER TABLE new_tracks ADD COLUMN release_year SMALLINT UNSIGNED NULL AFTER genre'
        );
        self::ensureColumn(
            'copy_title_count',
            'ALTER TABLE new_tracks ADD COLUMN copy_title_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER energy'
        );
    }

    private static function ensureColumn(string $columnName, string $alterSql): void
    {
        $pdo = Db::connection();
        $stmt = $pdo->query(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            . "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            . "AND COLUMN_NAME = '" . $columnName . "'"
        );
        $row = $stmt->fetch();
        if ((int) ($row['cnt'] ?? 0) === 0) {
            $pdo->exec($alterSql);
        }
    }
}
