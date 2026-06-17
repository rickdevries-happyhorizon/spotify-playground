<?php

declare(strict_types=1);

final class TrackStore
{
    public static function loadAll(): array
    {
        $stmt = Db::connection()->query(
            'SELECT id, track, reference_url FROM new_tracks ORDER BY track ASC'
        );

        $tracks = [];
        foreach ($stmt->fetchAll() as $row) {
            $tracks[] = [
                'id' => (int) $row['id'],
                'track' => $row['track'],
                'reference_url' => $row['reference_url'] ?: null,
            ];
        }

        return $tracks;
    }

    public static function create(string $track, ?string $referenceUrl = null): array
    {
        $trackName = trim($track);
        if ($trackName === '') {
            throw new InvalidArgumentException('Track name is required');
        }

        $url = UrlNormalizer::normalize($referenceUrl);
        $pdo = Db::connection();

        try {
            $stmt = $pdo->prepare(
                'INSERT INTO new_tracks (track, reference_url) VALUES (:track, :reference_url)'
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
        ];
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
}
