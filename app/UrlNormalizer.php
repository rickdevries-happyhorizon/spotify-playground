<?php

declare(strict_types=1);

final class UrlNormalizer
{
    public static function normalize(?string $url): ?string
    {
        if ($url === null) {
            return null;
        }

        $cleaned = trim($url);
        if ($cleaned === '') {
            return null;
        }

        $parts = parse_url($cleaned);
        if ($parts === false) {
            return $cleaned;
        }

        $host = strtolower($parts['host'] ?? '');
        if (str_starts_with($host, 'www.')) {
            $host = substr($host, 4);
        }

        $videoId = null;
        $path = $parts['path'] ?? '';

        if (in_array($host, ['youtube.com', 'm.youtube.com', 'music.youtube.com'], true)) {
            if ($path === '/watch') {
                parse_str($parts['query'] ?? '', $query);
                $videoId = $query['v'] ?? null;
            } elseif (str_starts_with($path, '/shorts/')) {
                $segments = array_values(array_filter(explode('/', $path)));
                if (($segments[0] ?? null) === 'shorts' && isset($segments[1])) {
                    $videoId = $segments[1];
                }
            }
        } elseif ($host === 'youtu.be') {
            $segments = array_values(array_filter(explode('/', ltrim($path, '/'))));
            $videoId = $segments[0] ?? null;
        }

        if ($videoId) {
            return 'https://www.youtube.com/watch?v=' . $videoId;
        }

        return $cleaned;
    }
}
