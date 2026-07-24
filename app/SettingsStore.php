<?php

declare(strict_types=1);

final class SettingsStore
{
    private const VALID_SKINS = ['light', 'dark', 'retroui', 'winxp'];

    public static function load(): array
    {
        self::ensureSchema();

        $config = self::loadPlaylistsConfig();
        $destination = trim((string) ($config['destination_playlist'] ?? ''));
        $sourcePlaylists = $config['source_playlists'] ?? [];
        $trackingPlaylists = $config['tracking_playlists'] ?? [];
        $startDate = self::loadTrackingStartDate();
        $syncStartDate = self::loadSyncStartDate();

        $allIds = [];
        if ($destination !== '') {
            $allIds[] = $destination;
        }
        $allIds = array_merge($allIds, $sourcePlaylists, $trackingPlaylists);
        $names = self::playlistNamesBySpotifyId($allIds);

        return [
            'ui_skin' => AppConfig::loadUiSkin(),
            'locale' => AppConfig::loadLocale(),
            'destination_playlist' => $destination !== ''
                ? self::formatPlaylistEntry($destination, $names)
                : null,
            'source_playlists' => array_map(
                static fn (string $spotifyId): array => self::formatPlaylistEntry($spotifyId, $names),
                $sourcePlaylists
            ),
            'tracking_playlists' => array_map(
                static fn (string $spotifyId): array => self::formatPlaylistEntry($spotifyId, $names),
                $trackingPlaylists
            ),
            'tracking_start_date' => $startDate,
            'sync_start_date' => $syncStartDate,
        ];
    }

    public static function patch(array $data): array
    {
        self::ensureSchema();

        if (array_key_exists('ui_skin', $data)) {
            $skin = $data['ui_skin'];
            if (!is_string($skin)) {
                throw new InvalidArgumentException('ui_skin must be a string');
            }

            $normalized = strtolower(trim($skin));
            if ($normalized === 'neon' || $normalized === 'colorful') {
                $normalized = 'winxp';
            } elseif ($normalized === 'simple') {
                $normalized = 'light';
            }
            if (!in_array($normalized, self::VALID_SKINS, true)) {
                throw new InvalidArgumentException("ui_skin must be 'light', 'dark', 'retroui', or 'winxp'");
            }

            AppConfig::saveUiSkin($normalized);
        }

        if (array_key_exists('locale', $data)) {
            $locale = $data['locale'];
            if (!is_string($locale)) {
                throw new InvalidArgumentException('locale must be a string');
            }

            $normalized = strtolower(trim($locale));
            if (!in_array($normalized, ['en', 'nl', 'brab'], true)) {
                throw new InvalidArgumentException("locale must be 'en', 'nl', or 'brab'");
            }

            AppConfig::saveLocale($normalized);
        }

        $config = self::loadPlaylistsConfig();
        $configChanged = false;

        if (array_key_exists('destination_playlist', $data)) {
            $destination = $data['destination_playlist'];
            if ($destination === null || $destination === '') {
                $config['destination_playlist'] = '';
            } elseif (is_string($destination)) {
                $spotifyId = self::parseSpotifyPlaylistId($destination);
                if ($spotifyId === '') {
                    throw new InvalidArgumentException('Invalid destination playlist');
                }
                $config['destination_playlist'] = $spotifyId;
            } else {
                throw new InvalidArgumentException('destination_playlist must be a string or null');
            }
            $configChanged = true;
        }

        if (array_key_exists('source_playlists', $data)) {
            if (!is_array($data['source_playlists'])) {
                throw new InvalidArgumentException('source_playlists must be an array');
            }
            $config['source_playlists'] = self::parsePlaylistList($data['source_playlists'], 'source_playlists');
            $configChanged = true;
        }

        if (array_key_exists('tracking_playlists', $data)) {
            if (!is_array($data['tracking_playlists'])) {
                throw new InvalidArgumentException('tracking_playlists must be an array');
            }
            $config['tracking_playlists'] = self::parsePlaylistList($data['tracking_playlists'], 'tracking_playlists');
            $configChanged = true;
        }

        if ($configChanged) {
            $playlistDetails = self::resolvePlaylistDetailsForConfig($config);
            self::savePlaylistsConfig($config, $playlistDetails);
        }

        if (array_key_exists('sync_start_date', $data)) {
            $syncStartDate = $data['sync_start_date'];
            if ($syncStartDate === null || $syncStartDate === '') {
                self::saveSyncStartDate(null);
            } elseif (is_string($syncStartDate)) {
                self::saveSyncStartDate(trim($syncStartDate));
            } else {
                throw new InvalidArgumentException('sync_start_date must be a string or null');
            }
        }

        if (array_key_exists('tracking_start_date', $data)) {
            $trackingStartDate = $data['tracking_start_date'];
            if ($trackingStartDate === null || $trackingStartDate === '') {
                self::saveTrackingStartDate(null);
            } elseif (is_string($trackingStartDate)) {
                self::saveTrackingStartDate(trim($trackingStartDate));
            } else {
                throw new InvalidArgumentException('tracking_start_date must be a string or null');
            }
        }

        return self::load();
    }

    public static function lookupPlaylist(string $rawId): array
    {
        self::ensureSchema();

        $spotifyId = self::parseSpotifyPlaylistId($rawId);
        if ($spotifyId === '') {
            throw new InvalidArgumentException('Invalid playlist ID');
        }

        $names = self::playlistNamesBySpotifyId([$spotifyId]);
        if (isset($names[$spotifyId]) && $names[$spotifyId] !== $spotifyId) {
            return [
                'spotify_id' => $spotifyId,
                'name' => $names[$spotifyId],
            ];
        }

        $details = self::fetchPlaylistFromSpotify($rawId);
        if ($details !== null) {
            return [
                'spotify_id' => $details['spotify_id'] ?? $spotifyId,
                'name' => $details['name'] ?? null,
            ];
        }

        return [
            'spotify_id' => $spotifyId,
            'name' => $names[$spotifyId] ?? null,
        ];
    }

    public static function parseSpotifyPlaylistId(string $text): string
    {
        $value = trim($text);
        if ($value === '') {
            return '';
        }

        if (str_starts_with($value, 'spotify:playlist:')) {
            return trim(explode('?', str_replace('spotify:playlist:', '', $value))[0]);
        }

        if (str_contains($value, 'open.spotify.com') && str_contains($value, '/playlist/')) {
            $tail = explode('/playlist/', $value, 2)[1];
            return trim(explode('?', explode('/', $tail)[0])[0]);
        }

        return $value;
    }

    private static function formatPlaylistEntry(string $spotifyId, array $names): array
    {
        return [
            'spotify_id' => $spotifyId,
            'name' => $names[$spotifyId] ?? null,
        ];
    }

    private static function parsePlaylistList(array $values, string $fieldName): array
    {
        $parsed = [];
        foreach ($values as $item) {
            if (!is_string($item)) {
                throw new InvalidArgumentException("{$fieldName} items must be strings");
            }

            $spotifyId = self::parseSpotifyPlaylistId($item);
            if ($spotifyId === '') {
                throw new InvalidArgumentException("Invalid playlist in {$fieldName}: {$item}");
            }

            if (!in_array($spotifyId, $parsed, true)) {
                $parsed[] = $spotifyId;
            }
        }

        return $parsed;
    }

    private static function resolvePlaylistDetailsForConfig(array $config): array
    {
        $spotifyIds = [];
        $destination = trim((string) ($config['destination_playlist'] ?? ''));
        if ($destination !== '') {
            $spotifyIds[] = $destination;
        }

        foreach (['source_playlists', 'tracking_playlists'] as $field) {
            foreach ($config[$field] ?? [] as $spotifyId) {
                $spotifyId = trim((string) $spotifyId);
                if ($spotifyId !== '' && !in_array($spotifyId, $spotifyIds, true)) {
                    $spotifyIds[] = $spotifyId;
                }
            }
        }

        if ($spotifyIds === []) {
            return [];
        }

        $details = self::resolvePlaylistsFromSpotify($spotifyIds);
        if ($details === null) {
            return [];
        }

        return $details;
    }

    private static function findPythonExecutable(): ?string
    {
        $root = project_root();
        $candidates = [
            $root . '/.venv/bin/python3',
            $root . '/venv/bin/python3',
            'python3',
        ];

        foreach ($candidates as $candidate) {
            if ($candidate === 'python3') {
                $which = trim((string) shell_exec('command -v python3 2>/dev/null'));
                if ($which !== '' && is_executable($which)) {
                    return $which;
                }
                continue;
            }

            if (is_executable($candidate)) {
                return $candidate;
            }
        }

        return null;
    }

    private static function fetchPlaylistFromSpotify(string $rawId): ?array
    {
        $python = self::findPythonExecutable();
        if ($python === null) {
            return null;
        }

        $root = project_root();
        $command = 'cd '
            . escapeshellarg($root)
            . ' && '
            . escapeshellarg($python)
            . ' -m spotify_playlist.lookup_playlist_cli '
            . escapeshellarg($rawId)
            . ' 2>/dev/null';
        $output = shell_exec($command);
        if (!is_string($output) || trim($output) === '') {
            return null;
        }

        $decoded = json_decode(trim($output), true);
        if (!is_array($decoded) || !empty($decoded['error'])) {
            return null;
        }

        return $decoded;
    }

    private static function resolvePlaylistsFromSpotify(array $spotifyIds): ?array
    {
        $python = self::findPythonExecutable();
        if ($python === null) {
            return null;
        }

        $payload = json_encode(array_values($spotifyIds), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        if ($payload === false) {
            return null;
        }

        $root = project_root();
        $command = 'cd '
            . escapeshellarg($root)
            . ' && printf %s '
            . escapeshellarg($payload)
            . ' | '
            . escapeshellarg($python)
            . ' -m spotify_playlist.resolve_playlists_cli'
            . ' 2>/dev/null';
        $output = shell_exec($command);
        if (!is_string($output) || trim($output) === '') {
            return null;
        }

        $decoded = json_decode(trim($output), true);
        if (!is_array($decoded) || !empty($decoded['error'])) {
            return null;
        }

        return $decoded;
    }

    private static function playlistNamesBySpotifyId(array $spotifyIds): array
    {
        $uniqueIds = array_values(array_unique(array_filter($spotifyIds, static fn ($id): bool => is_string($id) && $id !== '')));
        if ($uniqueIds === []) {
            return [];
        }

        $placeholders = implode(', ', array_fill(0, count($uniqueIds), '?'));
        $stmt = Db::connection()->prepare(
            "SELECT spotify_id, name FROM playlist WHERE spotify_id IN ({$placeholders})"
        );
        $stmt->execute($uniqueIds);

        $names = [];
        foreach ($stmt->fetchAll() as $row) {
            if (!empty($row['spotify_id']) && !empty($row['name'])) {
                $names[$row['spotify_id']] = $row['name'];
            }
        }

        return $names;
    }

    private static function loadPlaylistsConfig(): array
    {
        self::ensureSchema();

        $stmt = Db::connection()->query(
            'SELECT p.spotify_id '
            . 'FROM app_config ac '
            . 'LEFT JOIN playlist p ON p.id = ac.destination_playlist_ref_id '
            . 'WHERE ac.singleton = 1 LIMIT 1'
        );
        $destinationRow = $stmt->fetch();
        $destination = is_array($destinationRow) ? (string) ($destinationRow['spotify_id'] ?? '') : '';

        $stmt = Db::connection()->query(
            'SELECT p.spotify_id '
            . 'FROM playlist_source ps '
            . 'INNER JOIN playlist p ON p.id = ps.playlist_ref_id '
            . 'ORDER BY ps.sort_order ASC, p.spotify_id ASC'
        );
        $sourcePlaylists = [];
        foreach ($stmt->fetchAll() as $row) {
            if (!empty($row['spotify_id'])) {
                $sourcePlaylists[] = $row['spotify_id'];
            }
        }

        $stmt = Db::connection()->query(
            'SELECT p.spotify_id '
            . 'FROM playlist_tracking pt '
            . 'INNER JOIN playlist p ON p.id = pt.playlist_ref_id '
            . 'ORDER BY pt.sort_order ASC, p.spotify_id ASC'
        );
        $trackingPlaylists = [];
        foreach ($stmt->fetchAll() as $row) {
            if (!empty($row['spotify_id'])) {
                $trackingPlaylists[] = $row['spotify_id'];
            }
        }

        return [
            'source_playlists' => $sourcePlaylists,
            'destination_playlist' => $destination,
            'tracking_playlists' => $trackingPlaylists,
        ];
    }

    private static function savePlaylistsConfig(array $config, array $playlistDetails = []): void
    {
        $pdo = Db::connection();
        $pdo->beginTransaction();

        try {
            $destination = trim((string) ($config['destination_playlist'] ?? ''));
            $sources = is_array($config['source_playlists'] ?? null) ? $config['source_playlists'] : [];
            $tracking = is_array($config['tracking_playlists'] ?? null) ? $config['tracking_playlists'] : [];
            $keptRefIds = [];

            $destinationRefId = null;
            if ($destination !== '') {
                $destinationRefId = self::upsertPlaylist($destination, $playlistDetails[$destination] ?? null);
                $keptRefIds[] = $destinationRefId;
            }

            $stmt = $pdo->prepare(
                'INSERT INTO app_config (singleton, destination_playlist_ref_id) VALUES (1, :playlist_ref_id) '
                . 'ON DUPLICATE KEY UPDATE destination_playlist_ref_id = VALUES(destination_playlist_ref_id)'
            );
            $stmt->execute(['playlist_ref_id' => $destinationRefId]);

            $pdo->exec('DELETE FROM playlist_source');
            foreach (array_values($sources) as $index => $spotifyId) {
                $spotifyId = trim((string) $spotifyId);
                if ($spotifyId === '') {
                    continue;
                }

                $refId = self::upsertPlaylist($spotifyId, $playlistDetails[$spotifyId] ?? null);
                $keptRefIds[] = $refId;
                $stmt = $pdo->prepare(
                    'INSERT INTO playlist_source (sort_order, playlist_ref_id) VALUES (:sort_order, :playlist_ref_id)'
                );
                $stmt->execute([
                    'sort_order' => $index,
                    'playlist_ref_id' => $refId,
                ]);
            }

            $pdo->exec('DELETE FROM playlist_tracking');
            foreach (array_values($tracking) as $index => $spotifyId) {
                $spotifyId = trim((string) $spotifyId);
                if ($spotifyId === '') {
                    continue;
                }

                $refId = self::upsertPlaylist($spotifyId, $playlistDetails[$spotifyId] ?? null);
                $keptRefIds[] = $refId;
                $stmt = $pdo->prepare(
                    'INSERT INTO playlist_tracking (sort_order, playlist_ref_id) VALUES (:sort_order, :playlist_ref_id)'
                );
                $stmt->execute([
                    'sort_order' => $index,
                    'playlist_ref_id' => $refId,
                ]);
            }

            self::pruneUnusedConfigPlaylists($keptRefIds);
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
    }

    private static function upsertPlaylist(string $spotifyId, ?array $details = null): int
    {
        $pdo = Db::connection();
        $resolvedName = trim((string) ($details['name'] ?? ''));
        $artworkUrl = trim((string) ($details['artwork_url'] ?? '')) ?: null;

        $stmt = $pdo->prepare('SELECT id, name, artwork_url FROM playlist WHERE spotify_id = :spotify_id LIMIT 1');
        $stmt->execute(['spotify_id' => $spotifyId]);
        $row = $stmt->fetch();
        if (is_array($row) && isset($row['id'])) {
            $playlistId = (int) $row['id'];
            $updates = [];
            $params = [];
            if (
                $resolvedName !== ''
                && $resolvedName !== $spotifyId
                && $resolvedName !== ($row['name'] ?? '')
            ) {
                $updates[] = 'name = :name';
                $params['name'] = $resolvedName;
            }
            if ($artworkUrl !== null && $artworkUrl !== ($row['artwork_url'] ?? '')) {
                $updates[] = 'artwork_url = :artwork_url';
                $params['artwork_url'] = $artworkUrl;
            }
            if ($updates !== []) {
                $params['id'] = $playlistId;
                $stmt = $pdo->prepare(
                    'UPDATE playlist SET ' . implode(', ', $updates) . ' WHERE id = :id'
                );
                $stmt->execute($params);
            }

            return $playlistId;
        }

        $insertName = ($resolvedName !== '' && $resolvedName !== $spotifyId)
            ? $resolvedName
            : $spotifyId;

        $stmt = $pdo->prepare(
            'INSERT INTO playlist (spotify_id, name, artwork_url) VALUES (:spotify_id, :name, :artwork_url)'
        );
        $stmt->execute([
            'spotify_id' => $spotifyId,
            'name' => $insertName,
            'artwork_url' => $artworkUrl,
        ]);

        return (int) $pdo->lastInsertId();
    }

    private static function pruneUnusedConfigPlaylists(array $keptRefIds): void
    {
        $pdo = Db::connection();
        $protected = array_fill_keys($keptRefIds, true);

        $stmt = $pdo->query(
            'SELECT DISTINCT playlist_id FROM new_tracks WHERE playlist_id IS NOT NULL'
        );
        foreach ($stmt->fetchAll() as $row) {
            if (!empty($row['playlist_id'])) {
                $protected[(int) $row['playlist_id']] = true;
            }
        }

        $stmt = $pdo->query(
            'SELECT id FROM playlist WHERE spotify_id IS NOT NULL AND TRIM(spotify_id) != \'\''
        );
        foreach ($stmt->fetchAll() as $row) {
            $playlistId = (int) $row['id'];
            if (!isset($protected[$playlistId])) {
                $delete = $pdo->prepare('DELETE FROM playlist WHERE id = :id');
                $delete->execute(['id' => $playlistId]);
            }
        }
    }

    private static function loadSyncStartDate(): ?string
    {
        $stmt = Db::connection()->query(
            'SELECT sync_start_date FROM app_config WHERE singleton = 1 LIMIT 1'
        );
        $row = $stmt->fetch();
        if (!is_array($row) || empty($row['sync_start_date'])) {
            return null;
        }

        $timestamp = strtotime((string) $row['sync_start_date']);
        if ($timestamp === false) {
            return null;
        }

        return date('Y-m-d', $timestamp);
    }

    private static function saveSyncStartDate(?string $startDate): void
    {
        $now = date('Y-m-d H:i:s');
        if ($startDate === null || trim($startDate) === '') {
            $stmt = Db::connection()->prepare(
                'INSERT INTO app_config (singleton, sync_start_date, sync_start_updated) '
                . 'VALUES (1, NULL, :sync_start_updated) '
                . 'ON DUPLICATE KEY UPDATE sync_start_date = NULL, '
                . 'sync_start_updated = VALUES(sync_start_updated)'
            );
            $stmt->execute(['sync_start_updated' => $now]);
            return;
        }

        $timestamp = strtotime($startDate);
        if ($timestamp === false) {
            throw new InvalidArgumentException('Invalid sync_start_date');
        }

        $stmt = Db::connection()->prepare(
            'INSERT INTO app_config (singleton, sync_start_date, sync_start_updated) '
            . 'VALUES (1, :sync_start_date, :sync_start_updated) '
            . 'ON DUPLICATE KEY UPDATE sync_start_date = VALUES(sync_start_date), '
            . 'sync_start_updated = VALUES(sync_start_updated)'
        );
        $stmt->execute([
            'sync_start_date' => date('Y-m-d 00:00:00', $timestamp),
            'sync_start_updated' => $now,
        ]);
    }

    private static function loadTrackingStartDate(): ?string
    {
        $stmt = Db::connection()->query(
            'SELECT tracking_start_date FROM app_config WHERE singleton = 1 LIMIT 1'
        );
        $row = $stmt->fetch();
        if (!is_array($row) || empty($row['tracking_start_date'])) {
            return null;
        }

        $timestamp = strtotime((string) $row['tracking_start_date']);
        if ($timestamp === false) {
            return null;
        }

        return date('Y-m-d', $timestamp);
    }

    private static function saveTrackingStartDate(?string $startDate): void
    {
        $now = date('Y-m-d H:i:s');
        if ($startDate === null || trim($startDate) === '') {
            $stmt = Db::connection()->prepare(
                'INSERT INTO app_config (singleton, tracking_start_date, tracking_start_updated) '
                . 'VALUES (1, NULL, :tracking_start_updated) '
                . 'ON DUPLICATE KEY UPDATE tracking_start_date = NULL, '
                . 'tracking_start_updated = VALUES(tracking_start_updated)'
            );
            $stmt->execute(['tracking_start_updated' => $now]);
            return;
        }

        $timestamp = strtotime($startDate);
        if ($timestamp === false) {
            throw new InvalidArgumentException('Invalid tracking_start_date');
        }

        $stmt = Db::connection()->prepare(
            'INSERT INTO app_config (singleton, tracking_start_date, tracking_start_updated) '
            . 'VALUES (1, :tracking_start_date, :tracking_start_updated) '
            . 'ON DUPLICATE KEY UPDATE tracking_start_date = VALUES(tracking_start_date), '
            . 'tracking_start_updated = VALUES(tracking_start_updated)'
        );
        $stmt->execute([
            'tracking_start_date' => date('Y-m-d 00:00:00', $timestamp),
            'tracking_start_updated' => $now,
        ]);
    }

    public static function ensureSchema(): void
    {
        $pdo = Db::connection();
        $pdo->exec(
            'CREATE TABLE IF NOT EXISTS playlist ('
            . 'id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            . 'spotify_id VARCHAR(64) NULL UNIQUE, '
            . 'name VARCHAR(512) NOT NULL, '
            . 'artwork_url TEXT NULL'
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );
        $pdo->exec(
            'CREATE TABLE IF NOT EXISTS app_config ('
            . 'singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY, '
            . 'ui_skin VARCHAR(32) NOT NULL DEFAULT \'light\''
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );
        $pdo->exec("INSERT IGNORE INTO app_config (singleton, ui_skin) VALUES (1, 'light')");
        $pdo->exec("UPDATE app_config SET ui_skin = 'winxp' WHERE ui_skin IN ('colorful', 'neon')");

        self::ensureAppConfigColumn($pdo, 'destination_playlist_ref_id', 'INT UNSIGNED NULL');
        self::ensureAppConfigColumn($pdo, 'tracking_start_date', 'DATETIME NULL');
        self::ensureAppConfigColumn($pdo, 'tracking_start_updated', 'DATETIME NULL');
        self::ensureAppConfigColumn($pdo, 'sync_start_date', 'DATETIME NULL');
        self::ensureAppConfigColumn($pdo, 'sync_start_updated', 'DATETIME NULL');
        self::ensureAppConfigColumn($pdo, 'locale', "VARCHAR(16) NOT NULL DEFAULT 'en'");

        $pdo->exec(
            'CREATE TABLE IF NOT EXISTS playlist_source ('
            . 'sort_order INT UNSIGNED NOT NULL, '
            . 'playlist_ref_id INT UNSIGNED NOT NULL, '
            . 'PRIMARY KEY (playlist_ref_id), '
            . 'KEY idx_playlist_source_sort (sort_order), '
            . 'CONSTRAINT fk_playlist_source FOREIGN KEY (playlist_ref_id) '
            . 'REFERENCES playlist(id) ON DELETE CASCADE'
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );
        $pdo->exec(
            'CREATE TABLE IF NOT EXISTS playlist_tracking ('
            . 'sort_order INT UNSIGNED NOT NULL, '
            . 'playlist_ref_id INT UNSIGNED NOT NULL, '
            . 'PRIMARY KEY (playlist_ref_id), '
            . 'KEY idx_playlist_tracking_sort (sort_order), '
            . 'CONSTRAINT fk_playlist_tracking FOREIGN KEY (playlist_ref_id) '
            . 'REFERENCES playlist(id) ON DELETE CASCADE'
            . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
        );

        self::migrateLegacyAppConfigTables($pdo);
    }

    private static function ensureAppConfigColumn(PDO $pdo, string $column, string $definition): void
    {
        $stmt = $pdo->prepare(
            'SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS '
            . 'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = \'app_config\' AND COLUMN_NAME = :column'
        );
        $stmt->execute(['column' => $column]);
        $row = $stmt->fetch();
        if (is_array($row) && (int) ($row['cnt'] ?? 0) === 0) {
            $pdo->exec("ALTER TABLE app_config ADD COLUMN {$column} {$definition}");
        }
    }

    private static function migrateLegacyAppConfigTables(PDO $pdo): void
    {
        $tables = $pdo->query(
            'SELECT TABLE_NAME FROM information_schema.TABLES '
            . 'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (\'destination_config\', \'tracking_start\')'
        )->fetchAll(PDO::FETCH_COLUMN);

        if (in_array('destination_config', $tables, true)) {
            $row = $pdo->query(
                'SELECT playlist_ref_id FROM destination_config WHERE singleton = 1 LIMIT 1'
            )->fetch();
            if (is_array($row) && !empty($row['playlist_ref_id'])) {
                $stmt = $pdo->prepare(
                    'UPDATE app_config SET destination_playlist_ref_id = :playlist_ref_id '
                    . 'WHERE singleton = 1 AND destination_playlist_ref_id IS NULL'
                );
                $stmt->execute(['playlist_ref_id' => (int) $row['playlist_ref_id']]);
            }
            $pdo->exec('DROP TABLE destination_config');
        }

        if (in_array('tracking_start', $tables, true)) {
            $row = $pdo->query(
                'SELECT start_date, last_updated FROM tracking_start WHERE singleton = 1 LIMIT 1'
            )->fetch();
            if (is_array($row)) {
                $stmt = $pdo->prepare(
                    'UPDATE app_config SET tracking_start_date = :tracking_start_date, '
                    . 'tracking_start_updated = :tracking_start_updated WHERE singleton = 1'
                );
                $stmt->execute([
                    'tracking_start_date' => $row['start_date'] ?? null,
                    'tracking_start_updated' => $row['last_updated'] ?? null,
                ]);
            }
            $pdo->exec('DROP TABLE tracking_start');
        }
    }
}
