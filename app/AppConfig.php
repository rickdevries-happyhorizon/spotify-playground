<?php

declare(strict_types=1);

final class AppConfig
{
    private const VALID_SKINS = ['neon', 'simple'];

    public static function loadUiSkin(): string
    {
        self::ensureSchema();

        $stmt = Db::connection()->query(
            'SELECT ui_skin FROM app_config WHERE singleton = 1 LIMIT 1'
        );
        $row = $stmt->fetch();

        return self::normalizeUiSkin(is_array($row) ? ($row['ui_skin'] ?? null) : null);
    }

    public static function saveUiSkin(string $skin): void
    {
        $normalized = self::normalizeUiSkin($skin);
        self::ensureSchema();

        $stmt = Db::connection()->prepare(
            'INSERT INTO app_config (singleton, ui_skin) VALUES (1, :ui_skin) '
            . 'ON DUPLICATE KEY UPDATE ui_skin = VALUES(ui_skin)'
        );
        $stmt->execute(['ui_skin' => $normalized]);
    }

    private static function normalizeUiSkin(?string $skin): string
    {
        $value = strtolower(trim((string) ($skin ?? 'neon')));

        return in_array($value, self::VALID_SKINS, true) ? $value : 'neon';
    }

    private static function ensureSchema(): void
    {
        Db::connection()->exec(
            'CREATE TABLE IF NOT EXISTS app_config ('
            . 'singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY, '
            . 'ui_skin VARCHAR(32) NOT NULL DEFAULT \'neon\''
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );

        Db::connection()->exec(
            "INSERT IGNORE INTO app_config (singleton, ui_skin) VALUES (1, 'neon')"
        );
    }
}
