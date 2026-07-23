<?php

declare(strict_types=1);

final class DownloadStore
{
    private static function jobsDir(): string
    {
        $dir = project_root() . '/.download_jobs';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException('Could not create download jobs directory.');
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

    private static function resolveDownloadDir(): string
    {
        $python = self::resolvePythonExecutable();
        $root = project_root();
        $script = <<<'PY'
import json
import sys
from spotify_playlist.download_job_manager import resolve_output_dir
directory, error = resolve_output_dir()
print(json.dumps({"dir": directory, "error": error}, ensure_ascii=False))
sys.exit(0 if directory else 1)
PY;
        $command = 'cd '
            . escapeshellarg($root)
            . ' && '
            . escapeshellarg($python)
            . ' -c '
            . escapeshellarg($script);

        $output = shell_exec($command);
        if (!is_string($output) || trim($output) === '') {
            throw new RuntimeException('Could not resolve the download directory.');
        }

        $payload = json_decode(trim($output), true);
        if (!is_array($payload)) {
            throw new RuntimeException('Could not resolve the download directory.');
        }

        $error = $payload['error'] ?? null;
        if (is_string($error) && $error !== '') {
            throw new InvalidArgumentException($error);
        }

        $directory = $payload['dir'] ?? null;
        if (!is_string($directory) || $directory === '') {
            throw new RuntimeException('Could not resolve the download directory.');
        }

        return $directory;
    }

    private static function countTracksWithUrl(): int
    {
        $stmt = Db::connection()->query(
            "SELECT COUNT(*) AS cnt FROM new_tracks "
            . "WHERE reference_url IS NOT NULL AND TRIM(reference_url) <> ''"
        );
        $row = $stmt->fetch();

        return is_array($row) ? (int) ($row['cnt'] ?? 0) : 0;
    }

    /** @return array{job_id: string} */
    public static function start(): array
    {
        $outputDir = self::resolveDownloadDir();
        $trackCount = self::countTracksWithUrl();
        if ($trackCount === 0) {
            throw new InvalidArgumentException(
                'No tracks with YouTube URL found in the app. '
                . 'Add reference URLs in the new tracks todo first.'
            );
        }

        $jobId = self::generateUuid();
        $now = gmdate('c');
        $job = [
            'job_id' => $jobId,
            'status' => 'running',
            'phase' => 'queued',
            'message' => 'Preparing download…',
            'track_total' => $trackCount,
            'output_dir' => $outputDir,
            'created_at' => $now,
            'updated_at' => $now,
            'result' => null,
            'error' => null,
        ];

        $path = self::jobPath($jobId);
        if (file_put_contents($path, json_encode($job, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) === false) {
            throw new RuntimeException('Could not create download job.');
        }

        $python = self::resolvePythonExecutable();
        $root = project_root();
        $command = 'cd '
            . escapeshellarg($root)
            . ' && '
            . escapeshellarg($python)
            . ' -m spotify_playlist.run_web_download '
            . escapeshellarg($jobId)
            . ' > /dev/null 2>&1 &';

        exec($command);

        return ['job_id' => $jobId];
    }

    /** @return array<string, mixed>|null */
    public static function status(string $jobId): ?array
    {
        $path = self::jobPath($jobId);
        if (!is_readable($path)) {
            return null;
        }

        $raw = file_get_contents($path);
        if ($raw === false || trim($raw) === '') {
            return null;
        }

        $job = json_decode($raw, true);
        return is_array($job) ? $job : null;
    }

    private static function generateUuid(): string
    {
        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }
}
