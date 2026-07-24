<?php

declare(strict_types=1);

final class SyncStore
{
    private static function jobsDir(): string
    {
        $dir = project_root() . '/.sync_jobs';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException('Could not create sync jobs directory.');
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

    /** @return array<string, mixed>|null */
    public static function findActive(): ?array
    {
        $dir = self::jobsDir();
        $activeJobs = [];

        foreach (glob($dir . '/*.json') ?: [] as $path) {
            if (!is_readable($path) || str_ends_with($path, '.json.tmp')) {
                continue;
            }

            $raw = file_get_contents($path);
            if ($raw === false || trim($raw) === '') {
                continue;
            }

            $job = json_decode($raw, true);
            if (!is_array($job) || ($job['status'] ?? '') !== 'running') {
                continue;
            }

            if (!self::jobProcessAlive($job)) {
                self::markJobInterrupted($job['job_id'] ?? '');
                continue;
            }

            $activeJobs[] = $job;
        }

        if ($activeJobs === []) {
            return null;
        }

        usort($activeJobs, static function (array $a, array $b): int {
            return strcmp($b['updated_at'] ?? '', $a['updated_at'] ?? '');
        });

        return $activeJobs[0];
    }

    private static function jobProcessAlive(array $job): bool
    {
        $pid = $job['worker_pid'] ?? null;
        if (!is_int($pid) || $pid <= 0) {
            return false;
        }

        if (function_exists('posix_kill')) {
            return @posix_kill($pid, 0);
        }

        $output = [];
        $exitCode = 1;
        exec('kill -0 ' . (int) $pid . ' 2>/dev/null', $output, $exitCode);

        return $exitCode === 0;
    }

    private static function markJobInterrupted(string $jobId): void
    {
        if ($jobId === '') {
            return;
        }

        $path = self::jobPath($jobId);
        if (!is_readable($path)) {
            return;
        }

        $raw = file_get_contents($path);
        if ($raw === false) {
            return;
        }

        $job = json_decode($raw, true);
        if (!is_array($job) || ($job['status'] ?? '') !== 'running') {
            return;
        }

        $job['status'] = 'error';
        $job['phase'] = 'error';
        $job['message'] = 'Sync interrupted';
        $job['error'] = 'Sync interrupted';
        $job['updated_at'] = gmdate('c');

        file_put_contents(
            $path,
            json_encode($job, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        );
    }

    /** @return array{job_id: string} */
    public static function start(bool $force = false): array
    {
        if (!$force) {
            $active = self::findActive();
            if ($active !== null) {
                return ['job_id' => $active['job_id']];
            }
        }

        $settings = SettingsStore::load();
        $sourcePlaylists = $settings['source_playlists'] ?? [];
        $destination = $settings['destination_playlist']['spotify_id'] ?? '';
        if ($destination === '') {
            throw new InvalidArgumentException(
                'No destination playlist configured. Set it in Settings first.'
            );
        }
        if ($sourcePlaylists === []) {
            throw new InvalidArgumentException(
                'No source playlists configured. Add source playlists in Settings first.'
            );
        }

        $jobId = self::generateUuid();
        $now = gmdate('c');
        $job = [
            'job_id' => $jobId,
            'status' => 'running',
            'phase' => 'queued',
            'message' => 'Preparing sync…',
            'created_at' => $now,
            'updated_at' => $now,
            'result' => null,
            'error' => null,
        ];

        $path = self::jobPath($jobId);
        if (file_put_contents($path, json_encode($job, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) === false) {
            throw new RuntimeException('Could not create sync job.');
        }

        $python = self::resolvePythonExecutable();
        $root = project_root();
        $command = 'cd '
            . escapeshellarg($root)
            . ' && '
            . escapeshellarg($python)
            . ' -m spotify_playlist.run_web_sync '
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
