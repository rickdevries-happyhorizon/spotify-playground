<?php

declare(strict_types=1);

final class TrackNormalizer
{
    public static function normalize(string $name): string
    {
        $cleaned = preg_replace(
            '/(?:\s*-\s*radio\s+(?:edit|mix)|\s*\(radio\s+(?:edit|mix)\))\s*$/iu',
            '',
            $name
        );

        if ($cleaned === null) {
            return trim($name);
        }

        return trim(preg_replace('/\s+/u', ' ', $cleaned) ?? $cleaned);
    }
}
