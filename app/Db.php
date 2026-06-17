<?php

declare(strict_types=1);

final class Db
{
    private static ?PDO $pdo = null;

    public static function connection(): PDO
    {
        if (self::$pdo instanceof PDO) {
            return self::$pdo;
        }

        $host = env('MYSQL_HOST', '127.0.0.1');
        $port = env('MYSQL_PORT', '3306');
        $user = env('MYSQL_USER', 'root');
        $password = env('MYSQL_PASSWORD', '');
        $database = env('MYSQL_DATABASE', 'spotify_playground');

        $dsn = sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
            $host,
            $port,
            $database
        );

        self::$pdo = new PDO($dsn, $user, $password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);

        return self::$pdo;
    }
}
