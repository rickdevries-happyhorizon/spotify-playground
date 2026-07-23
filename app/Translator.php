<?php

declare(strict_types=1);

final class Translator
{
    private const VALID_LOCALES = ['en', 'nl', 'brab'];

    private const LOCALE_LABELS = [
        'en' => 'English',
        'nl' => 'Dutch',
        'brab' => 'Brabants',
    ];

    private static ?string $locale = null;

    /** @var array<string, array<string, string>> */
    private static array $catalogs = [];

    public static function normalizeLocale(?string $locale): string
    {
        $value = strtolower(trim((string) ($locale ?? 'en')));
        return in_array($value, self::VALID_LOCALES, true) ? $value : 'en';
    }

    public static function localeLabel(string $locale): string
    {
        $normalized = self::normalizeLocale($locale);
        return self::LOCALE_LABELS[$normalized] ?? $normalized;
    }

    public static function htmlLang(string $locale): string
    {
        $normalized = self::normalizeLocale($locale);
        return $normalized === 'brab' ? 'nl-BE' : $normalized;
    }

    public static function setLocale(?string $locale): void
    {
        self::$locale = self::normalizeLocale($locale);
    }

    public static function getLocale(): string
    {
        if (self::$locale === null) {
            self::$locale = AppConfig::loadLocale();
        }

        return self::$locale;
    }

    public static function gettext(string $msgid): string
    {
        $locale = self::getLocale();
        $catalog = self::loadCatalog($locale);
        return $catalog[$msgid] ?? $msgid;
    }

    /** @return array<string, string> */
    public static function exportJsonCatalog(?string $locale = null): array
    {
        return self::loadCatalog(self::normalizeLocale($locale ?? self::getLocale()));
    }

    /** @return array<string, string> */
    private static function loadCatalog(string $locale): array
    {
        $locale = self::normalizeLocale($locale);
        if (isset(self::$catalogs[$locale])) {
            return self::$catalogs[$locale];
        }

        $catalog = self::parsePoFile(self::poPath('en'));
        if ($locale !== 'en') {
            $catalog = array_merge($catalog, self::parsePoFile(self::poPath($locale)));
        }

        self::$catalogs[$locale] = $catalog;
        return $catalog;
    }

    private static function poPath(string $locale): string
    {
        return project_root()
            . '/spotify_playlist/locale/'
            . self::normalizeLocale($locale)
            . '/LC_MESSAGES/messages.po';
    }

    /** @return array<string, string> */
    private static function parsePoFile(string $path): array
    {
        if (!is_readable($path)) {
            return [];
        }

        $entries = [];
        $msgid = [];
        $msgstr = [];
        $state = null;

        $flush = static function () use (&$entries, &$msgid, &$msgstr, &$state): void {
            if ($msgid !== []) {
                $key = implode('', $msgid);
                if ($key !== '') {
                    $entries[$key] = implode('', $msgstr) !== '' ? implode('', $msgstr) : $key;
                }
            }
            $msgid = [];
            $msgstr = [];
            $state = null;
        };

        $lines = file($path, FILE_IGNORE_NEW_LINES);
        if ($lines === false) {
            return [];
        }

        foreach ($lines as $line) {
            $line = trim($line);
            if ($line === '' || str_starts_with($line, '#')) {
                continue;
            }

            if (str_starts_with($line, 'msgid ')) {
                $flush();
                $state = 'msgid';
                $msgid[] = self::parsePoString(substr($line, 6));
                continue;
            }

            if (str_starts_with($line, 'msgstr ')) {
                $state = 'msgstr';
                $msgstr[] = self::parsePoString(substr($line, 7));
                continue;
            }

            if (str_starts_with($line, '"') && ($state === 'msgid' || $state === 'msgstr')) {
                $chunk = self::parsePoString($line);
                if ($state === 'msgid') {
                    $msgid[] = $chunk;
                } else {
                    $msgstr[] = $chunk;
                }
            }
        }

        $flush();
        return $entries;
    }

    private static function parsePoString(string $value): string
    {
        $value = trim($value);
        if ($value === '' || $value[0] !== '"') {
            return $value;
        }

        $decoded = stripcslashes(substr($value, 1, -1));
        return is_string($decoded) ? $decoded : '';
    }
}
