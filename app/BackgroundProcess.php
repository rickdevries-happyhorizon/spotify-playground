<?php

declare(strict_types=1);

final class BackgroundProcess
{
    public static function spawnShell(string $command): void
    {
        $handle = popen($command, 'r');
        if ($handle === false) {
            throw new RuntimeException('Could not start background process.');
        }

        pclose($handle);
    }
}
