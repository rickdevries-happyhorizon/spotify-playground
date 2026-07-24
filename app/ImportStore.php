<?php

declare(strict_types=1);

final class ImportStore
{
    private static function jobsDir(): string
    {
        $dir = project_root() . '/.import_jobs';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException('Could not create import jobs directory.');
        }

        return $dir;
    }

    private static function jobPath(string $jobId): string
    {
        $safeId = preg_replace('/[^a-zA-Z0-9-]/', '', $jobId) ?? '';
        if ($safeId === '') {
            throw new InvalidArgumentException('Invalid job id.');
        }

        return self::jobsDir() . '/' . $safeId . '.json';
    }

    private static function resolvePythonExecutable(): string
    {
        $root = project_root();
        $candidates = [
            $root . '/.venv/bin/python3',
            $root . '/venv/bin/python3',
        ];

        foreach ($candidates as $candidate) {
            if (is_executable($candidate)) {
                return $candidate;
            }
        }

        return 'python3';
    }

    /** @return array{job_id: string} */
    public static function start(): array
    {
        $settings = SettingsStore::load();
        $trackingPlaylists = $settings['tracking_playlists'] ?? [];
        if ($trackingPlaylists === []) {
            throw new InvalidArgumentException(
                'No tracking playlists configured. Add them in Settings first.'
            );
        }

        $jobId = self::generateUuid();
        $now = gmdate('c');
        $job = [
            'job_id' => $jobId,
            'status' => 'running',
            'phase' => 'queued',
            'message' => 'Preparing import…',
            'created_at' => $now,
            'updated_at' => $now,
            'result' => null,
            'error' => null,
        ];

        $path = self::jobPath($jobId);
        if (file_put_contents($path, json_encode($job, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) === false) {
            throw new RuntimeException('Could not create import job.');
        }

        $python = self::resolvePythonExecutable();
        $root = project_root();
        $command = 'cd '
            . escapeshellarg($root)
            . ' && '
            . escapeshellarg($python)
            . ' -m spotify_playlist.run_web_import '
            . escapeshellarg($jobId)
            . ' > /dev/null 2>&1 &';

        BackgroundProcess::spawnShell($command);

        return ['job_id' => $jobId];
    }

    /** @return array<string, mixed>|null */
    public static function status(string $jobId): ?array
    {
        $path = self::jobPath($jobId);
        if (!is_readable($path)) {
            return null;
        }

        for ($attempt = 0; $attempt < 5; $attempt++) {
            $raw = file_get_contents($path);
            if ($raw === false || trim($raw) === '') {
                usleep(50000);
                continue;
            }

            $job = json_decode($raw, true);
            if (is_array($job)) {
                return $job;
            }

            usleep(50000);
        }

        return null;
    }

    private static function generateUuid(): string
    {
        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }
}
