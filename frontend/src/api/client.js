/** Thin fetch wrapper for the PHP REST API. */

async function parseJson(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    if (text.trimStart().startsWith('<!')) {
      throw new Error(
        'API returned HTML instead of JSON. Restart the Vite dev server (npm run dev) and ensure the PHP API is running on port 8080.',
      );
    }
    throw new Error('API returned an invalid JSON response.');
  }
}

export async function apiGet(path) {
  const response = await fetch(path);
  const data = await parseJson(response);
  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}

export async function apiMutate(path, { method = 'POST', body } = {}) {
  const response = await fetch(path, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await parseJson(response);
  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}

// --- Tracks ---

export function fetchGenres() {
  return apiGet('/api/genres');
}

export function fetchTracks(genre) {
  const query = genre ? `?genre=${encodeURIComponent(genre)}` : '';
  return apiGet(`/api/tracks${query}`);
}

export function createTrack(payload) {
  return apiMutate('/api/tracks', { method: 'POST', body: payload });
}

export function updateTrackUrl(trackId, referenceUrl) {
  return apiMutate(`/api/tracks/${trackId}`, {
    method: 'PATCH',
    body: { reference_url: referenceUrl },
  });
}

export function deleteTrack(trackId) {
  return apiMutate(`/api/tracks/${trackId}`, { method: 'DELETE' });
}

export function recordCopyTitle(trackId) {
  return apiMutate(`/api/tracks/${trackId}/copy-title`, { method: 'POST' });
}

// --- Settings ---

export function fetchSettings() {
  return apiGet('/api/settings');
}

export function saveSettings(payload) {
  return apiMutate('/api/settings', { method: 'PATCH', body: payload });
}

export function lookupPlaylist(id) {
  return apiGet(`/api/playlists/lookup?id=${encodeURIComponent(id)}`);
}

export function fetchListeningStats() {
  return apiGet('/api/listening-stats');
}

// --- Jobs ---

export function startImport() {
  return apiMutate('/api/import/tracks', { method: 'POST' });
}

export function fetchImportStatus(jobId) {
  return apiGet(`/api/import/tracks/${encodeURIComponent(jobId)}`);
}

export function startSync(force = false) {
  const suffix = force ? '?force=1' : '';
  return apiMutate(`/api/sync/playlists${suffix}`, { method: 'POST' });
}

export function fetchActiveSync() {
  return fetch('/api/sync/playlists/active').then(async (response) => {
    if (response.status === 404) return null;
    const data = await parseJson(response);
    if (!response.ok) throw new Error(data.error || 'Sync status failed');
    return data;
  });
}

export function fetchSyncStatus(jobId) {
  return apiGet(`/api/sync/playlists/${encodeURIComponent(jobId)}`);
}

export function startDownload() {
  return apiMutate('/api/download/tracks', { method: 'POST' });
}

export function fetchDownloadStatus(jobId) {
  return apiGet(`/api/download/tracks/${encodeURIComponent(jobId)}`);
}
