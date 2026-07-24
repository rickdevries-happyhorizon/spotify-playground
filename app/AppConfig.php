<?php

declare(strict_types=1);

final class AppConfig
{
    private const VALID_SKINS = ['light', 'dark', 'retroui', 'winxp'];
    private const VALID_LOCALES = ['en', 'nl', 'brab'];

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

    public static function loadLocale(): string
    {
        self::ensureSchema();

        $stmt = Db::connection()->query(
            'SELECT locale FROM app_config WHERE singleton = 1 LIMIT 1'
        );
        $row = $stmt->fetch();

        return self::normalizeLocale(is_array($row) ? ($row['locale'] ?? null) : null);
    }

    public static function saveLocale(string $locale): void
    {
        $normalized = self::normalizeLocale($locale);
        self::ensureSchema();

        $stmt = Db::connection()->prepare(
            'INSERT INTO app_config (singleton, locale) VALUES (1, :locale) '
            . 'ON DUPLICATE KEY UPDATE locale = VALUES(locale)'
        );
        $stmt->execute(['locale' => $normalized]);
    }

    public static function ensureSchema(): void
    {
        SettingsStore::ensureSchema();
    }

    private static function normalizeUiSkin(?string $skin): string
    {
        $value = strtolower(trim((string) ($skin ?? 'light')));

        if ($value === 'neon' || $value === 'colorful') {
            $value = 'winxp';
        } elseif ($value === 'simple') {
            $value = 'light';
        }

        return in_array($value, self::VALID_SKINS, true) ? $value : 'light';
    }

    private static function normalizeLocale(?string $locale): string
    {
        $value = strtolower(trim((string) ($locale ?? 'en')));

        return in_array($value, self::VALID_LOCALES, true) ? $value : 'en';
    }
}
