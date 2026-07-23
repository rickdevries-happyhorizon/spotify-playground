<?php

declare(strict_types=1);

final class Router
{
    public static function handle(string $method, string $path): void
    {
        if ($path === '/' && $method === 'GET') {
            self::servePage();
            return;
        }

        if ($path === '/api/tracks' && $method === 'GET') {
            self::listTracks();
            return;
        }

        if ($path === '/api/tracks' && $method === 'POST') {
            self::createTrack();
            return;
        }

        if (preg_match('#^/api/tracks/(\d+)/copy-title$#', $path, $matches) === 1) {
            $trackId = (int) $matches[1];

            if ($method === 'POST') {
                self::recordCopyTitle($trackId);
                return;
            }
        }

        if (preg_match('#^/api/tracks/(\d+)$#', $path, $matches) === 1) {
            $trackId = (int) $matches[1];

            if ($method === 'PATCH') {
                self::patchTrack($trackId);
                return;
            }

            if ($method === 'DELETE') {
                self::deleteTrack($trackId);
                return;
            }
        }

        self::json(['error' => 'Not found'], 404);
    }

    private static function servePage(): void
    {
        $template = project_root() . '/spotify_playlist/templates/new_tracks_todo.html';
        if (!is_readable($template)) {
            http_response_code(500);
            echo 'Template not found.';
            return;
        }

        header('Content-Type: text/html; charset=UTF-8');
        readfile($template);
    }

    private static function listTracks(): void
    {
        try {
            $tracks = TrackStore::loadAll();
        } catch (Throwable $e) {
            self::json(['error' => $e->getMessage()], 500);
            return;
        }

        $withUrl = array_values(array_filter($tracks, static fn (array $track): bool => !empty($track['reference_url'])));
        $withoutUrl = array_values(array_filter($tracks, static fn (array $track): bool => empty($track['reference_url'])));

        self::json([
            'with_url' => $withUrl,
            'without_url' => $withoutUrl,
            'total' => count($tracks),
        ]);
    }

    private static function createTrack(): void
    {
        $data = self::jsonBody();
        $track = $data['track'] ?? null;

        if (!is_string($track) || trim($track) === '') {
            self::json(['error' => 'track is required'], 400);
            return;
        }

        $referenceUrl = $data['reference_url'] ?? null;
        if ($referenceUrl !== null && !is_string($referenceUrl)) {
            self::json(['error' => 'reference_url must be a string or null'], 400);
            return;
        }

        try {
            $created = TrackStore::create($track, $referenceUrl);
        } catch (InvalidArgumentException $e) {
            $status = stripos($e->getMessage(), 'already exists') !== false ? 409 : 400;
            self::json(['error' => $e->getMessage()], $status);
            return;
        } catch (Throwable $e) {
            self::json(['error' => $e->getMessage()], 500);
            return;
        }

        self::json([
            ...$created,
            'has_url' => !empty($created['reference_url']),
        ], 201);
    }

    private static function patchTrack(int $trackId): void
    {
        $data = self::jsonBody();
        if (!array_key_exists('reference_url', $data)) {
            self::json(['error' => 'reference_url is required'], 400);
            return;
        }

        $referenceUrl = $data['reference_url'];
        if ($referenceUrl !== null && !is_string($referenceUrl)) {
            self::json(['error' => 'reference_url must be a string or null'], 400);
            return;
        }

        try {
            $url = TrackStore::updateReferenceUrl($trackId, $referenceUrl);
        } catch (Throwable $e) {
            self::json(['error' => $e->getMessage()], 500);
            return;
        }

        if ($url === null) {
            self::json(['error' => 'Track not found'], 404);
            return;
        }

        self::json([
            'id' => $trackId,
            'reference_url' => $url,
            'has_url' => $url !== null && $url !== '',
        ]);
    }

    private static function recordCopyTitle(int $trackId): void
    {
        try {
            $count = TrackStore::incrementCopyTitleCount($trackId);
        } catch (Throwable $e) {
            self::json(['error' => $e->getMessage()], 500);
            return;
        }

        if ($count === null) {
            self::json(['error' => 'Track not found'], 404);
            return;
        }

        self::json([
            'id' => $trackId,
            'copy_title_count' => $count,
        ]);
    }

    private static function deleteTrack(int $trackId): void
    {
        try {
            $deleted = TrackStore::delete($trackId);
        } catch (Throwable $e) {
            self::json(['error' => $e->getMessage()], 500);
            return;
        }

        if (!$deleted) {
            self::json(['error' => 'Track not found'], 404);
            return;
        }

        self::json(['id' => $trackId, 'deleted' => true]);
    }

    private static function jsonBody(): array
    {
        $raw = file_get_contents('php://input');
        if ($raw === false || trim($raw) === '') {
            return [];
        }

        $decoded = json_decode($raw, true);
        return is_array($decoded) ? $decoded : [];
    }

    private static function json(array $payload, int $status = 200): void
    {
        http_response_code($status);
        header('Content-Type: application/json; charset=UTF-8');
        echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }
}
