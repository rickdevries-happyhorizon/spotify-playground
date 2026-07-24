<?php

declare(strict_types=1);

final class BackgroundProcess
{
    public static function spawnShell(string $command): void
    {
        // PHP/web servers often omit Homebrew from PATH; prepend common bins.
        $path = getenv('PATH') ?: '/usr/bin:/bin:/usr/sbin:/sbin';
        foreach (['/opt/homebrew/bin', '/usr/local/bin'] as $bin) {
            if (is_dir($bin) && !str_contains($path, $bin)) {
                $path = $bin . PATH_SEPARATOR . $path;
            }
        }

        $wrapped = 'PATH=' . escapeshellarg($path) . ' ' . $command;
        $handle = popen($wrapped, 'r');
        if ($handle === false) {
            throw new RuntimeException('Could not start background process.');
        }

        pclose($handle);
    }
}
