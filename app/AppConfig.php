<?php

declare(strict_types=1);

final class AppConfig
{
    private const VALID_SKINS = ['light', 'dark', 'colorful'];

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

    public static function ensureSchema(): void
    {
        SettingsStore::ensureSchema();
    }

    private static function normalizeUiSkin(?string $skin): string
    {
        $value = strtolower(trim((string) ($skin ?? 'colorful')));

        if ($value === 'neon') {
            $value = 'colorful';
        } elseif ($value === 'simple') {
            $value = 'light';
        }

        return in_array($value, self::VALID_SKINS, true) ? $value : 'colorful';
    }
}
