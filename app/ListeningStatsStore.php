<?php

declare(strict_types=1);

final class ListeningStatsStore
{
    public static function load(): array
    {
        $python = self::findPythonExecutable();
        if ($python === null) {
            throw new RuntimeException('Python 3 is not available');
        }

        $root = project_root();
        $command = 'cd '
            . escapeshellarg($root)
            . ' && '
            . escapeshellarg($python)
            . ' -m spotify_playlist.listening_stats_cli 2>&1';
        $output = shell_exec($command);
        if (!is_string($output) || trim($output) === '') {
            throw new RuntimeException('Failed to load listening stats from Spotify');
        }

        $decoded = json_decode(trim($output), true);
        if (!is_array($decoded)) {
            throw new RuntimeException('Invalid listening stats response');
        }

        if (!empty($decoded['error'])) {
            $message = (string) $decoded['error'];
            if (stripos($message, 'spotify') !== false || stripos($message, 'login') !== false) {
                throw new InvalidArgumentException($message);
            }

            throw new RuntimeException($message);
        }

        return $decoded;
    }

    private static function findPythonExecutable(): ?string
    {
        $root = project_root();
        $candidates = [
            $root . '/.venv/bin/python3',
            $root . '/venv/bin/python3',
            'python3',
        ];

        foreach ($candidates as $candidate) {
            if ($candidate === 'python3') {
                $which = trim((string) shell_exec('command -v python3 2>/dev/null'));
                if ($which !== '' && is_executable($which)) {
                    return $which;
                }
                continue;
            }

            if (is_executable($candidate)) {
                return $candidate;
            }
        }

        return null;
    }
}
