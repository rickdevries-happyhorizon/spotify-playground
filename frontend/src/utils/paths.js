export const FILTER_WITH_URL = 'with-url';
export const FILTER_WITHOUT_URL = 'without-url';

export function toUrlSlug(name) {
  if (!name) return '';
  return name.split('/').map((part) => part.replace(/ /g, '-')).join('/');
}

export function resolveGenreSlug(urlSlug, knownGenres) {
  if (!urlSlug) return null;
  if (knownGenres.includes(urlSlug)) return urlSlug;
  for (const genre of knownGenres) {
    if (toUrlSlug(genre) === urlSlug) return genre;
  }
  return urlSlug.replace(/-/g, ' ');
}

export function genrePath(slug, filter = null) {
  if (!slug) return '/todo';
  const base = `/todo/${toUrlSlug(slug)}`;
  if (filter === FILTER_WITH_URL) return `${base}/${FILTER_WITH_URL}`;
  if (filter === FILTER_WITHOUT_URL) return `${base}/${FILTER_WITHOUT_URL}`;
  return base;
}

export async function copyToClipboard(text) {
  if (!text) return false;
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
