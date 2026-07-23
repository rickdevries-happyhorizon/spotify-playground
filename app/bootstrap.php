<?php

declare(strict_types=1);

function project_root(): string
{
    return dirname(__DIR__);
}

function load_env_file(string $path): void
{
    if (!is_readable($path)) {
        return;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($lines === false) {
        return;
    }

    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) {
            continue;
        }

        if (!str_contains($line, '=')) {
            continue;
        }

        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value);

        if ($key === '' || getenv($key) !== false) {
            continue;
        }

        if (
            (str_starts_with($value, '"') && str_ends_with($value, '"'))
            || (str_starts_with($value, "'") && str_ends_with($value, "'"))
        ) {
            $value = substr($value, 1, -1);
        }

        putenv("{$key}={$value}");
        $_ENV[$key] = $value;
    }
}

function env(string $key, ?string $default = null): ?string
{
    $value = getenv($key);
    if ($value === false) {
        return $default;
    }

    return $value;
}

load_env_file(project_root() . '/.env');

require_once __DIR__ . '/UrlNormalizer.php';
require_once __DIR__ . '/TrackNormalizer.php';
require_once __DIR__ . '/Db.php';
require_once __DIR__ . '/TrackStore.php';
require_once __DIR__ . '/AppConfig.php';
require_once __DIR__ . '/SettingsStore.php';
require_once __DIR__ . '/Router.php';
