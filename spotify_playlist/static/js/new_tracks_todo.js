const genreView = document.getElementById("genre-view");
const genreHubView = document.getElementById("genre-hub-view");
const tracksView = document.getElementById("tracks-view");
const settingsView = document.getElementById("settings-view");
const startView = document.getElementById("start-view");
const statisticsView = document.getElementById("statistics-view");
const fetchView = document.getElementById("fetch-view");
const fetchTitle = document.getElementById("fetch-title");
const fetchMessage = document.getElementById("fetch-message");
const fetchProgressBar = document.getElementById("fetch-progress-bar");
const fetchProgressGlow = document.getElementById("fetch-progress-glow");
const fetchProgressWrap = document.querySelector(".fetch-progress-wrap");
const fetchProgressLabel = document.getElementById("fetch-progress-label");
const fetchProgressPercent = document.getElementById("fetch-progress-percent");
const fetchPlaylistCard = document.getElementById("fetch-playlist-card");
const fetchPlaylistArt = document.getElementById("fetch-playlist-art");
const fetchPlaylistPlaceholder = document.getElementById("fetch-playlist-placeholder");
const fetchPlaylistName = document.getElementById("fetch-playlist-name");
const fetchSteps = document.getElementById("fetch-steps");
const fetchResult = document.getElementById("fetch-result");
const fetchResultStats = document.getElementById("fetch-result-stats");
const fetchError = document.getElementById("fetch-error");
const fetchErrorMessage = document.getElementById("fetch-error-message");
const fetchParticles = document.getElementById("fetch-particles");
const fetchRunAgainBtn = document.getElementById("fetch-run-again");
const fetchRetryBtn = document.getElementById("fetch-retry");
const downloadView = document.getElementById("download-view");
const downloadTitle = document.getElementById("download-title");
const downloadMessage = document.getElementById("download-message");
const downloadProgressBar = document.getElementById("download-progress-bar");
const downloadProgressGlow = document.getElementById("download-progress-glow");
const downloadProgressWrap = downloadView?.querySelector(".fetch-progress-wrap");
const downloadProgressLabel = document.getElementById("download-progress-label");
const downloadProgressPercent = document.getElementById("download-progress-percent");
const downloadTrackCard = document.getElementById("download-track-card");
const downloadTrackName = document.getElementById("download-track-name");
const downloadSteps = document.getElementById("download-steps");
const downloadResult = document.getElementById("download-result");
const downloadResultStats = document.getElementById("download-result-stats");
const downloadError = document.getElementById("download-error");
const downloadErrorMessage = document.getElementById("download-error-message");
const downloadParticles = document.getElementById("download-particles");
const downloadRunAgainBtn = document.getElementById("download-run-again");
const downloadRetryBtn = document.getElementById("download-retry");
const syncView = document.getElementById("sync-view");
const syncTitle = document.getElementById("sync-title");
const syncMessage = document.getElementById("sync-message");
const syncProgressBar = document.getElementById("sync-progress-bar");
const syncProgressGlow = document.getElementById("sync-progress-glow");
const syncProgressWrap = syncView?.querySelector(".fetch-progress-wrap");
const syncProgressLabel = document.getElementById("sync-progress-label");
const syncProgressPercent = document.getElementById("sync-progress-percent");
const syncPlaylistCard = document.getElementById("sync-playlist-card");
const syncPlaylistArt = document.getElementById("sync-playlist-art");
const syncPlaylistPlaceholder = document.getElementById("sync-playlist-placeholder");
const syncPlaylistLabel = document.getElementById("sync-playlist-label");
const syncPlaylistName = document.getElementById("sync-playlist-name");
const syncSteps = document.getElementById("sync-steps");
const syncResult = document.getElementById("sync-result");
const syncResultStats = document.getElementById("sync-result-stats");
const syncError = document.getElementById("sync-error");
const syncErrorMessage = document.getElementById("sync-error-message");
const syncParticles = document.getElementById("sync-particles");
const syncRunAgainBtn = document.getElementById("sync-run-again");
const syncRetryBtn = document.getElementById("sync-retry");
const appGrid = document.getElementById("app-grid");
const statsSummary = document.getElementById("stats-summary");
const statsGenreBody = document.getElementById("stats-genre-body");
const genreGrid = document.getElementById("genre-grid");
const filterGrid = document.getElementById("filter-grid");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");
const pageCover = document.getElementById("page-cover");
const breadcrumbsBar = document.getElementById("breadcrumbs-bar");
const breadcrumbsList = document.getElementById("breadcrumbs-list");
const settingsLink = document.getElementById("settings-link");
const settingsForm = document.getElementById("settings-form");
const settingsDock = document.getElementById("settings-dock");
const settingsDockText = document.getElementById("settings-dock-text");
const sourcePlaylistsList = document.getElementById("source-playlists-list");
const trackingPlaylistsList = document.getElementById("tracking-playlists-list");
const addSourcePlaylistBtn = document.getElementById("add-source-playlist");
const addTrackingPlaylistBtn = document.getElementById("add-tracking-playlist");
const destinationPlaylistMeta = document.getElementById("destination-playlist-meta");
const columnDone = document.getElementById("column-done");
const columnTodo = document.getElementById("column-todo");
const listDone = document.getElementById("list-done");
const listTodo = document.getElementById("list-todo");
const tabWithUrl = document.getElementById("tab-with-url");
const tabWithoutUrl = document.getElementById("tab-without-url");
const statusEl = document.getElementById("status");
const copyToastEl = document.getElementById("copy-toast");
const bannerEl = document.getElementById("banner");
const FILTER_WITH_URL = "with-url";
const FILTER_WITHOUT_URL = "without-url";
const START_PATH = "/";
const TODO_PATH = "/todo";
const FETCH_PATH = "/fetch";
const SYNC_PATH = "/sync";
const DOWNLOAD_PATH = "/download";
const STATISTICS_PATH = "/statistics";
const SETTINGS_PATH = "/settings";
const APP_NAME = () => t("Release Finder");
const FILTER_LABELS = {
  [FILTER_WITH_URL]: () => t("Has reference URL"),
  [FILTER_WITHOUT_URL]: () => t("Needs reference URL"),
};
function getAppModules() {
  return [
    {
      label: t("Track to-do list"),
      description: t("Manage reference URLs for new tracks by genre."),
      icon: "✓",
      path: TODO_PATH,
      className: "app-card--todo",
    },
    {
      label: t("Fetch new tracks"),
      description: t("Scan tracking playlists for new additions and add them to your download to-do list."),
      icon: "↓",
      path: FETCH_PATH,
      className: "app-card--fetch",
    },
    {
      label: t("Sync playlists"),
      description: t("Pull new tracks from followed artists and source playlists into your destination playlist."),
      icon: "↻",
      path: SYNC_PATH,
      className: "app-card--sync",
    },
    {
      label: t("Download to AIFF"),
      description: t("Download tracks with YouTube URLs as AIFF files. Completed tracks are removed from your to-do list."),
      icon: "♫",
      path: DOWNLOAD_PATH,
      className: "app-card--download",
    },
    {
      label: t("Statistics"),
      description: t("Overview of tracks, completion, and activity."),
      icon: "📊",
      path: STATISTICS_PATH,
      className: "app-card--stats",
    },
  ];
}
let statusTimer = null;
let copyToastTimer = null;
let lastHighlightedName = null;
let currentGenre = null;
let currentFilter = null;
let cachedTracks = { with_url: [], without_url: [] };
let knownGenres = [];
let genreImageBySlug = {};
let currentView = "start";
const sourcePlaylistCount = document.getElementById("source-playlist-count");
const trackingPlaylistCount = document.getElementById("tracking-playlist-count");
const playlistLookupTimers = new WeakMap();
let savedSettingsSkin = "colorful";
let savedSettingsLocale = window.__LOCALE__ || "en";
let fetchPollTimer = null;
let fetchFinishTimer = null;
let fetchProgressRaf = null;
let activeFetchJobId = null;
let fetchStartedAt = 0;
let fetchDisplayPercent = 0;
let fetchTargetPercent = 0;
let pendingSuccessJob = null;
let lastFetchJobSnapshot = null;
let downloadPollTimer = null;
let downloadProgressRaf = null;
let activeDownloadJobId = null;
let downloadStartedAt = 0;
let downloadDisplayPercent = 0;
let downloadTargetPercent = 0;
let syncPollTimer = null;
let syncProgressRaf = null;
let activeSyncJobId = null;
let syncJobMissingPolls = 0;
let syncStartedAt = 0;
let syncLastJobUpdatedAt = 0;
let syncDisplayPercent = 0;
let syncTargetPercent = 0;

const FETCH_MIN_DURATION_MS = window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ? 0
  : 6500;
const FETCH_POLL_MS = 500;
const DOWNLOAD_POLL_MS = 500;
const SYNC_POLL_MS = 500;
const SYNC_PHASE_PROGRESS = {
  queued: 2,
  starting: 4,
  artists_start: 6,
  artists_scanning: 10,
  artists_done: 28,
  sources_start: 30,
  playlist_start: 32,
  fetching_tracks: 44,
  playlist_done: 58,
  playlist_error: 58,
  adding: 82,
  done: 100,
  error: 100,
};
const FETCH_PHASE_PROGRESS = {
  queued: 4,
  starting: 8,
  playlist_start: 18,
  fetching_tracks: 34,
  playlist_done: 48,
  playlist_skipped: 48,
  playlist_error: 48,
  fetching_energy: 72,
  saving: 88,
  done: 100,
  error: 100,
};

function setPlaylistMeta(metaEl, name, state = "resolved") {
  if (!metaEl) return;
  if (!name) {
    metaEl.hidden = true;
    metaEl.textContent = "";
    metaEl.className = "playlist-meta";
    return;
  }

  metaEl.hidden = false;
  metaEl.textContent = name;
  metaEl.className = `playlist-meta playlist-meta--${state}`;
}

function createPlaylistRow(entry = {}, { removable = true } = {}) {
  const row = document.createElement("div");
  row.className = "playlist-input-row";

  const field = document.createElement("label");
  field.className = "settings-field playlist-input-row__field";

  const input = document.createElement("input");
  input.type = "text";
  input.className = "playlist-id-input";
  input.placeholder = "https://open.spotify.com/playlist/…";
  input.value = entry?.spotify_id || entry || "";

  const meta = document.createElement("span");
  meta.className = "playlist-meta";
  meta.hidden = true;

  field.append(meta, input);

  const actions = document.createElement("div");
  actions.className = "playlist-input-row__actions";

  if (removable) {
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "playlist-remove-btn";
    removeBtn.title = t("Remove playlist");
    removeBtn.setAttribute("aria-label", t("Remove playlist"));
    removeBtn.textContent = "×";
    removeBtn.addEventListener("click", () => {
      row.remove();
      updateSettingsCounts();
      markSettingsDirty();
    });
    actions.appendChild(removeBtn);
  }

  row.append(field, actions);

  if (entry?.name) {
    setPlaylistMeta(meta, entry.name);
  }

  input.addEventListener("input", () => {
    setPlaylistMeta(meta, "");
    updateSettingsCounts();
    markSettingsDirty();
    schedulePlaylistLookup(input, meta);
  });

  input.addEventListener("blur", () => {
    lookupPlaylistForInput(input, meta);
  });

  return row;
}

function renderPlaylistList(container, entries) {
  container.innerHTML = "";
  const items = entries?.length ? entries : [{}];
  for (const entry of items) {
    container.appendChild(createPlaylistRow(entry));
  }
}

function collectPlaylistValues(container) {
  return [...container.querySelectorAll(".playlist-id-input")]
    .map((input) => input.value.trim())
    .filter(Boolean);
}

function schedulePlaylistLookup(input, metaEl) {
  const existing = playlistLookupTimers.get(input);
  if (existing) clearTimeout(existing);

  const timer = setTimeout(() => {
    lookupPlaylistForInput(input, metaEl);
  }, 450);
  playlistLookupTimers.set(input, timer);
}

async function lookupPlaylistForInput(input, metaEl) {
  const value = input.value.trim();
  if (!value) {
    setPlaylistMeta(metaEl, "");
    return;
  }

  setPlaylistMeta(metaEl, "Looking up playlist…", "loading");

  try {
    const response = await fetch(`/api/playlists/lookup?id=${encodeURIComponent(value)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Could not look up playlist");
    }

    if (input.value.trim() !== value) {
      return;
    }

    if (data.name && data.name !== data.spotify_id) {
      setPlaylistMeta(metaEl, data.name);
    } else {
      setPlaylistMeta(metaEl, "Playlist not found", "error");
    }
  } catch (error) {
    if (input.value.trim() === value) {
      setPlaylistMeta(metaEl, error.message || "Could not look up playlist", "error");
    }
  }
}

async function lookupDestinationPlaylist() {
  const value = settingsForm.destination_playlist.value.trim();
  if (!value) {
    setPlaylistMeta(destinationPlaylistMeta, "");
    return;
  }

  setPlaylistMeta(destinationPlaylistMeta, "Looking up playlist…", "loading");

  try {
    const response = await fetch(`/api/playlists/lookup?id=${encodeURIComponent(value)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Could not look up playlist");
    }

    if (settingsForm.destination_playlist.value.trim() !== value) {
      return;
    }

    if (data.name && data.name !== data.spotify_id) {
      setPlaylistMeta(destinationPlaylistMeta, data.name);
    } else {
      setPlaylistMeta(destinationPlaylistMeta, "Playlist not found", "error");
    }
  } catch (error) {
    if (settingsForm.destination_playlist.value.trim() === value) {
      setPlaylistMeta(destinationPlaylistMeta, error.message || "Could not look up playlist", "error");
    }
  }
}

function scheduleDestinationLookup() {
  const input = settingsForm.destination_playlist;
  const existing = playlistLookupTimers.get(input);
  if (existing) clearTimeout(existing);

  const timer = setTimeout(() => {
    lookupDestinationPlaylist();
  }, 450);
  playlistLookupTimers.set(input, timer);
}

function setPageCover(imageUrl) {
  if (imageUrl) {
    pageCover.src = imageUrl;
    pageCover.hidden = false;
  } else {
    pageCover.removeAttribute("src");
    pageCover.hidden = true;
  }
}

function artMarkup(imageUrl, className = "track-art", label = "") {
  if (imageUrl) {
    const alt = label ? ` alt="${escapeHtml(label)}"` : ' alt=""';
    return `<img class="${className}" src="${escapeHtml(imageUrl)}"${alt} loading="lazy" />`;
  }
  return `<span class="art-placeholder ${className}" aria-hidden="true">♪</span>`;
}

function toUrlSlug(name) {
  return name.split("/").map((part) => part.replace(/ /g, "-")).join("/");
}

function resolveGenreSlug(urlSlug) {
  if (!urlSlug) return null;
  if (knownGenres.includes(urlSlug)) return urlSlug;
  for (const genre of knownGenres) {
    if (toUrlSlug(genre) === urlSlug) return genre;
  }
  return urlSlug.replace(/-/g, " ");
}

function genrePath(slug, filter = null) {
  const base = `${TODO_PATH}/${toUrlSlug(slug)}`;
  if (filter === FILTER_WITH_URL) return `${base}/${FILTER_WITH_URL}`;
  if (filter === FILTER_WITHOUT_URL) return `${base}/${FILTER_WITHOUT_URL}`;
  return base;
}

function parsePath(pathname) {
  const path = pathname.replace(/\/+$/, "") || START_PATH;
  if (path === SETTINGS_PATH) {
    return { view: "settings", genre: null, filter: null };
  }
  if (path === STATISTICS_PATH) {
    return { view: "statistics", genre: null, filter: null };
  }
  if (path === FETCH_PATH) {
    return { view: "fetch", genre: null, filter: null };
  }
  if (path === SYNC_PATH) {
    return { view: "sync", genre: null, filter: null };
  }
  if (path === DOWNLOAD_PATH) {
    return { view: "download", genre: null, filter: null };
  }
  if (path === START_PATH) {
    return { view: "start", genre: null, filter: null };
  }
  if (path === TODO_PATH) {
    return { view: "home", genre: null, filter: null };
  }

  let segments;
  let usesTodoPrefix = false;
  if (path.startsWith(`${TODO_PATH}/`)) {
    usesTodoPrefix = true;
    segments = path
      .slice(TODO_PATH.length + 1)
      .split("/")
      .map((segment) => decodeURIComponent(segment.replace(/\+/g, " ")));
  } else {
    segments = path
      .slice(1)
      .split("/")
      .map((segment) => decodeURIComponent(segment.replace(/\+/g, " ")));
  }

  const last = segments[segments.length - 1];
  if (last === FILTER_WITH_URL || last === FILTER_WITHOUT_URL) {
    const genre = segments.slice(0, -1).join("/");
    return {
      view: "tracks",
      genre: genre || null,
      filter: last,
      legacy: !usesTodoPrefix,
    };
  }

  return {
    view: "genre",
    genre: segments.join("/"),
    filter: null,
    legacy: !usesTodoPrefix,
  };
}

async function ensureKnownGenres() {
  if (knownGenres.length) return;
  const response = await fetch("/api/genres");
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || t("Could not load genres"));
  }
  knownGenres = (data.genres || []).map((genre) => genre.slug);
}

function normalizeRoutePath(genre, filter = null) {
  const canonicalPath = genrePath(genre, filter);
  if (window.location.pathname !== canonicalPath) {
    history.replaceState({ genre, filter }, "", canonicalPath);
  }
}

function setSettingsLinkActive(active) {
  settingsLink.classList.toggle("settings-link--active", active);
  if (active) {
    settingsLink.setAttribute("aria-current", "page");
  } else {
    settingsLink.removeAttribute("aria-current");
  }
}

function hideAllViews() {
  startView.hidden = true;
  genreView.hidden = true;
  genreHubView.hidden = true;
  tracksView.hidden = true;
  settingsView.hidden = true;
  statisticsView.hidden = true;
  fetchView.hidden = true;
  if (syncView) syncView.hidden = true;
  if (downloadView) downloadView.hidden = true;
}

function handleAppModuleClick(event, path) {
  event.preventDefault();
  if (path === TODO_PATH) {
    navigateToTodo();
    return;
  }
  if (path === FETCH_PATH) {
    navigateToFetch();
    return;
  }
  if (path === SYNC_PATH) {
    navigateToSync();
    return;
  }
  if (path === DOWNLOAD_PATH) {
    navigateToDownload();
    return;
  }
  if (path === STATISTICS_PATH) {
    navigateToStatistics();
  }
}

function renderStartScreen() {
  if (appGrid.childElementCount) return;

  for (const module of getAppModules()) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.className = `app-card ${module.className}`;
    link.href = module.path;
    link.innerHTML = `
      <span class="app-card__icon" aria-hidden="true">${module.icon}</span>
      <span class="app-card__body">
        <span class="app-card__name">${escapeHtml(module.label)}</span>
        <span class="app-card__desc">${escapeHtml(module.description)}</span>
      </span>
    `;
    link.addEventListener("click", (event) => handleAppModuleClick(event, module.path));
    item.appendChild(link);
    appGrid.appendChild(item);
  }
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "—";
  return `${Math.round(value)}%`;
}

function formatEnergy(value) {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  return Number(value).toFixed(2);
}

function renderStatistics({ genres, withUrl, withoutUrl }) {
  const total = withUrl.length + withoutUrl.length;
  const completion = total ? (withUrl.length / total) * 100 : 0;
  const copyClicks = [...withUrl, ...withoutUrl].reduce(
    (sum, track) => sum + Number(track.copy_title_count || 0),
    0
  );
  const energyValues = [...withUrl, ...withoutUrl]
    .map((track) => track.energy)
    .filter((value) => value != null && Number.isFinite(Number(value)));
  const avgEnergy = energyValues.length
    ? energyValues.reduce((sum, value) => sum + Number(value), 0) / energyValues.length
    : null;

  statsSummary.innerHTML = `
    <article class="stats-card">
      <span class="stats-card__label">${t("Total tracks")}</span>
      <strong class="stats-card__value">${total}</strong>
    </article>
    <article class="stats-card stats-card--done">
      <span class="stats-card__label">${t("Has reference URL")}</span>
      <strong class="stats-card__value">${withUrl.length}</strong>
    </article>
    <article class="stats-card stats-card--todo">
      <span class="stats-card__label">${t("Needs reference URL")}</span>
      <strong class="stats-card__value">${withoutUrl.length}</strong>
    </article>
    <article class="stats-card">
      <span class="stats-card__label">${t("Completion")}</span>
      <strong class="stats-card__value">${formatPercent(completion)}</strong>
    </article>
    <article class="stats-card">
      <span class="stats-card__label">${t("Title copy clicks")}</span>
      <strong class="stats-card__value">${copyClicks}</strong>
    </article>
    <article class="stats-card">
      <span class="stats-card__label">${t("Average energy")}</span>
      <strong class="stats-card__value">${formatEnergy(avgEnergy)}</strong>
    </article>
  `;

  const genreStats = new Map();
  for (const track of withUrl) {
    const genre = (track.genre || "").trim() || t("Uncategorized");
    const entry = genreStats.get(genre) || { withUrl: 0, withoutUrl: 0 };
    entry.withUrl += 1;
    genreStats.set(genre, entry);
  }
  for (const track of withoutUrl) {
    const genre = (track.genre || "").trim() || t("Uncategorized");
    const entry = genreStats.get(genre) || { withUrl: 0, withoutUrl: 0 };
    entry.withoutUrl += 1;
    genreStats.set(genre, entry);
  }

  const genreOrder = (genres || []).map((genre) => genre.label);
  for (const genre of genreStats.keys()) {
    if (!genreOrder.includes(genre)) {
      genreOrder.push(genre);
    }
  }

  statsGenreBody.replaceChildren();
  if (!genreOrder.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.className = "stats-table__empty";
    cell.textContent = t("No tracks found.");
    row.appendChild(cell);
    statsGenreBody.appendChild(row);
    return;
  }

  for (const genre of genreOrder) {
    const entry = genreStats.get(genre);
    if (!entry) continue;
    const genreTotal = entry.withUrl + entry.withoutUrl;
    const row = document.createElement("tr");
    row.innerHTML = `
      <th scope="row">${escapeHtml(genre)}</th>
      <td>${genreTotal}</td>
      <td>${entry.withUrl}</td>
      <td>${entry.withoutUrl}</td>
      <td>${formatPercent(genreTotal ? (entry.withUrl / genreTotal) * 100 : 0)}</td>
    `;
    statsGenreBody.appendChild(row);
  }
}

async function loadStatistics() {
  setBanner(t("Loading statistics…"), "loading");
  try {
    const [genresResponse, tracksResponse] = await Promise.all([
      fetch("/api/genres"),
      fetch("/api/tracks"),
    ]);
    const genresData = await genresResponse.json().catch(() => ({}));
    const tracksData = await tracksResponse.json().catch(() => ({}));
    if (!genresResponse.ok) {
      throw new Error(genresData.error || t("Could not load genres"));
    }
    if (!tracksResponse.ok) {
      throw new Error(tracksData.error || t("Could not load tracks"));
    }

    renderStatistics({
      genres: genresData.genres || [],
      withUrl: tracksData.with_url || [],
      withoutUrl: tracksData.without_url || [],
    });
    setBanner("");
  } catch (error) {
    setBanner(t("Failed to load statistics: {message}", { message: error.message }), "error");
    showStatus(error.message, "error");
  }
}

function handleBreadcrumbClick(event, href) {
  event.preventDefault();
  if (href === START_PATH) {
    navigateToStart();
    return;
  }
  if (href === TODO_PATH) {
    navigateToTodo();
    return;
  }
  if (href === STATISTICS_PATH) {
    navigateToStatistics();
    return;
  }
  if (href === FETCH_PATH) {
    navigateToFetch();
    return;
  }
  if (href === SYNC_PATH) {
    navigateToSync();
    return;
  }
  if (href === DOWNLOAD_PATH) {
    navigateToDownload();
    return;
  }
  if (href === SETTINGS_PATH) {
    navigateToSettings();
    return;
  }

  const { genre: urlSlug, filter } = parsePath(href);
  const genre = resolveGenreSlug(urlSlug);
  if (!genre) {
    navigateToTodo();
    return;
  }
  if (filter) {
    navigateToFilter(genre, filter);
    return;
  }
  navigateToGenre(genre);
}

function createBreadcrumbItem(label, href, { current = false } = {}) {
  const item = document.createElement("li");
  item.className = "breadcrumbs__item";

  if (current) {
    item.classList.add("breadcrumbs__item--current");
    item.setAttribute("aria-current", "page");
    const currentEl = document.createElement("span");
    currentEl.className = "breadcrumbs__current";
    currentEl.textContent = label;
    item.appendChild(currentEl);
    return item;
  }

  const link = document.createElement("a");
  link.className = "breadcrumbs__link";
  link.href = href;
  link.textContent = label;
  link.addEventListener("click", (event) => handleBreadcrumbClick(event, href));
  item.appendChild(link);
  return item;
}

function updateBreadcrumbs() {
  breadcrumbsList.replaceChildren();

  if (currentView === "start") {
    breadcrumbsBar.hidden = true;
    return;
  }

  breadcrumbsBar.hidden = false;
  const crumbs = [{ label: t("Home"), href: START_PATH }];

  if (currentView === "settings") {
    crumbs.push({ label: t("Settings"), href: SETTINGS_PATH, current: true });
  } else if (currentView === "statistics") {
    crumbs.push({ label: t("Statistics"), href: STATISTICS_PATH, current: true });
  } else if (currentView === "fetch") {
    crumbs.push({ label: t("Fetch tracks"), href: FETCH_PATH, current: true });
  } else if (currentView === "sync") {
    crumbs.push({ label: t("Sync playlists"), href: SYNC_PATH, current: true });
  } else if (currentView === "download") {
    crumbs.push({ label: t("Download to AIFF"), href: DOWNLOAD_PATH, current: true });
  } else if (currentView === "home") {
    crumbs.push({ label: t("Track to-do"), href: TODO_PATH, current: true });
  } else if (currentView === "genre" && currentGenre) {
    crumbs.push({ label: t("Track to-do"), href: TODO_PATH });
    crumbs.push({ label: currentGenre, href: genrePath(currentGenre), current: true });
  } else if (currentView === "tracks" && currentGenre) {
    crumbs.push({ label: t("Track to-do"), href: TODO_PATH });
    crumbs.push({ label: currentGenre, href: genrePath(currentGenre) });
    crumbs.push({
      label: (FILTER_LABELS[currentFilter] || (() => currentFilter))(),
      href: genrePath(currentGenre, currentFilter),
      current: true,
    });
  }

  for (const crumb of crumbs) {
    breadcrumbsList.appendChild(
      createBreadcrumbItem(crumb.label, crumb.href, { current: Boolean(crumb.current) })
    );
  }
}

function showStartView() {
  restoreSettingsSkinIfNeeded();
  currentView = "start";
  currentGenre = null;
  currentFilter = null;
  document.title = APP_NAME();
  pageTitle.textContent = APP_NAME();
  pageSubtitle.textContent = t("Choose a tool to get started.");
  setPageCover(null);
  setSettingsLinkActive(false);
  hideAllViews();
  startView.hidden = false;
  renderStartScreen();
  setBanner("");
  updateBreadcrumbs();
}

function showGenreView() {
  restoreSettingsSkinIfNeeded();
  currentView = "home";
  currentGenre = null;
  currentFilter = null;
  document.title = t("Track to-do — {app_name}", { app_name: APP_NAME() });
  pageTitle.textContent = t("Track to-do");
  pageSubtitle.textContent = t("Choose a genre to manage reference URLs for its tracks.");
  setPageCover(null);
  setSettingsLinkActive(false);
  hideAllViews();
  genreView.hidden = false;
  updateBreadcrumbs();
}

function showStatisticsView() {
  restoreSettingsSkinIfNeeded();
  currentView = "statistics";
  currentGenre = null;
  currentFilter = null;
  document.title = t("Statistics — {app_name}", { app_name: APP_NAME() });
  pageTitle.textContent = t("Statistics");
  pageSubtitle.textContent = t("Overview of your new tracks and reference URL progress.");
  setPageCover(null);
  setSettingsLinkActive(false);
  hideAllViews();
  statisticsView.hidden = false;
  updateBreadcrumbs();
}

function renderFetchParticles() {
  if (!fetchParticles || fetchParticles.childElementCount) return;
  for (let i = 0; i < 10; i += 1) {
    const particle = document.createElement("li");
    particle.className = "fetch-particle";
    particle.style.left = `${12 + Math.random() * 76}%`;
    particle.style.top = `${12 + Math.random() * 76}%`;
    particle.style.animationDelay = `${Math.random() * 1.8}s`;
    fetchParticles.appendChild(particle);
  }
}

function resetFetchScreen() {
  stopFetchPolling();
  stopFetchFinishSequence();
  stopFetchProgressAnimation();
  activeFetchJobId = null;
  pendingSuccessJob = null;
  lastFetchJobSnapshot = null;
  fetchStartedAt = 0;
  fetchDisplayPercent = 0;
  fetchTargetPercent = 0;
  fetchView.classList.remove("is-success", "is-error");
  fetchTitle.textContent = t("Fetching new tracks");
  fetchMessage.textContent = t("Connecting to Spotify…");
  fetchProgressBar.style.width = "0%";
  fetchProgressGlow.style.left = "0%";
  fetchProgressWrap?.classList.add("is-active");
  fetchProgressLabel.textContent = t("Starting…");
  fetchProgressPercent.textContent = "0%";
  fetchPlaylistCard.hidden = true;
  fetchResult.hidden = true;
  fetchError.hidden = true;
  fetchResultStats.innerHTML = "";
  for (const step of fetchSteps.querySelectorAll(".fetch-step")) {
    step.classList.remove("is-active", "is-done");
  }
  fetchSteps.querySelector('[data-step="starting"]')?.classList.add("is-active");
}

function setFetchStepState(phase) {
  const stepGroups = {
    starting: ["starting"],
    playlist_start: ["starting", "playlists"],
    fetching_tracks: ["starting", "playlists"],
    playlist_done: ["starting", "playlists"],
    playlist_skipped: ["starting", "playlists"],
    playlist_error: ["starting", "playlists"],
    fetching_energy: ["starting", "playlists", "energy"],
    saving: ["starting", "playlists", "energy", "saving"],
    done: ["starting", "playlists", "energy", "saving", "done"],
    error: ["starting", "playlists", "energy", "saving", "done"],
  };
  const activeKeys = new Set(stepGroups[phase] || ["starting"]);
  const order = ["starting", "playlists", "energy", "saving", "done"];
  let reachedActive = false;

  for (const key of order) {
    const step = fetchSteps.querySelector(`[data-step="${key}"]`);
    if (!step) continue;
    step.classList.remove("is-active", "is-done");
    if (activeKeys.has(key)) {
      if (!reachedActive) {
        step.classList.add("is-active");
        reachedActive = true;
      } else {
        step.classList.add("is-done");
      }
    } else if (phase === "done") {
      step.classList.add("is-done");
    }
  }
}

function computeFetchPercent(job) {
  const phase = job.phase || "starting";
  let percent = FETCH_PHASE_PROGRESS[phase] ?? 8;

  if (
    phase === "playlist_start"
    || phase === "fetching_tracks"
    || phase === "playlist_done"
  ) {
    const index = Number(job.playlist_index || 0);
    const total = Number(job.playlist_total || 1);
    const sliceStart = FETCH_PHASE_PROGRESS.playlist_start;
    const sliceEnd = FETCH_PHASE_PROGRESS.playlist_done;
    const slice = sliceEnd - sliceStart;
    const playlistProgress = total ? Math.min(1, Math.max(0, (index - 1) / total)) : 0;
    percent = Math.round(sliceStart + slice * playlistProgress);
    if (phase === "fetching_tracks") {
      percent = Math.min(sliceEnd - 4, percent + Math.round(slice / total / 2));
    }
    if (phase === "playlist_done") {
      percent = Math.round(sliceStart + slice * Math.min(1, index / total));
    }
  }

  return percent;
}

function applyFetchJobPresentation(job) {
  const phase = job.phase || "starting";
  const percent = computeFetchPercent(job);
  fetchTargetPercent = Math.max(fetchTargetPercent, percent);
  fetchProgressLabel.textContent = job.message || t("Working…");
  fetchMessage.textContent = job.message || t("Working…");
  setFetchStepState(phase);

  if (job.playlist_name) {
    fetchPlaylistCard.hidden = false;
    fetchPlaylistName.textContent = job.playlist_name;
    if (job.playlist_image_url) {
      fetchPlaylistArt.src = job.playlist_image_url;
      fetchPlaylistArt.hidden = false;
      fetchPlaylistPlaceholder.hidden = true;
    } else {
      fetchPlaylistArt.hidden = true;
      fetchPlaylistPlaceholder.hidden = false;
    }
  }
}

function stopFetchProgressAnimation() {
  if (fetchProgressRaf) {
    cancelAnimationFrame(fetchProgressRaf);
    fetchProgressRaf = null;
  }
}

function startFetchProgressAnimation() {
  stopFetchProgressAnimation();

  const tick = () => {
    if (fetchDisplayPercent < fetchTargetPercent) {
      const delta = Math.max(0.35, (fetchTargetPercent - fetchDisplayPercent) * 0.08);
      fetchDisplayPercent = Math.min(fetchTargetPercent, fetchDisplayPercent + delta);
    }

    fetchProgressBar.style.width = `${fetchDisplayPercent}%`;
    fetchProgressGlow.style.left = `${fetchDisplayPercent}%`;
    fetchProgressPercent.textContent = `${Math.round(fetchDisplayPercent)}%`;
    fetchProgressRaf = requestAnimationFrame(tick);
  };

  fetchProgressRaf = requestAnimationFrame(tick);
}

function stopFetchFinishSequence() {
  if (fetchFinishTimer) {
    clearTimeout(fetchFinishTimer);
    fetchFinishTimer = null;
  }
}

function delay(ms) {
  return new Promise((resolve) => {
    fetchFinishTimer = setTimeout(resolve, ms);
  });
}

function buildFetchFinishSteps(job) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pace = reducedMotion ? 0.15 : 1;
  const playlistTotal = Number(
    job.playlist_total
    ?? job.result?.playlist_count
    ?? job.result?.playlists_checked
    ?? 0
  );
  const playlistLabel = playlistTotal
    ? `${playlistTotal} playlist${playlistTotal === 1 ? "" : "s"}`
    : "your playlists";
  const found = Number(job.tracks_found ?? job.result?.tracks_found ?? 0);
  const sinceDate = job.since_date ?? job.result?.since_date;
  const untilDate = job.until_date ?? job.result?.until_date;
  const dateRange = sinceDate && untilDate ? ` (${sinceDate} → ${untilDate})` : "";

  return [
    {
      phase: "playlists",
      message: `Scanning ${playlistLabel}${dateRange}…`,
      percent: 42,
      ms: Math.round(1400 * pace),
    },
    {
      phase: "playlists",
      message: found
        ? `Found ${found} track${found === 1 ? "" : "s"} across ${playlistLabel}`
        : `No new tracks in ${playlistLabel}${dateRange}`,
      percent: 58,
      ms: Math.round(1200 * pace),
    },
    {
      phase: "energy",
      message: found ? "Fetching track energy from Spotify…" : "Verifying track metadata…",
      percent: 74,
      ms: Math.round(1100 * pace),
    },
    {
      phase: "saving",
      message: found ? "Saving new tracks to your to-do list…" : "Updating tracking date…",
      percent: 88,
      ms: Math.round(1000 * pace),
    },
    {
      phase: "done",
      message: "Wrapping up…",
      percent: 96,
      ms: Math.round(800 * pace),
    },
  ];
}

async function scheduleFetchSuccess(job) {
  const jobId = job.job_id ?? activeFetchJobId;
  if (pendingSuccessJob || activeFetchJobId !== jobId) {
    return;
  }

  pendingSuccessJob = job;
  stopFetchPolling();
  fetchPlaylistCard.hidden = true;

  const elapsed = Date.now() - fetchStartedAt;
  const skippedAhead = elapsed < 2200 || fetchDisplayPercent < 36;
  const steps = skippedAhead ? buildFetchFinishSteps(job) : buildFetchFinishSteps(job).slice(2);

  for (const step of steps) {
    if (activeFetchJobId !== jobId) {
      return;
    }
    fetchTargetPercent = Math.max(fetchTargetPercent, step.percent);
    setFetchStepState(step.phase);
    fetchProgressLabel.textContent = step.message;
    fetchMessage.textContent = step.message;
    await delay(step.ms);
  }

  const totalElapsed = Date.now() - fetchStartedAt;
  if (totalElapsed < FETCH_MIN_DURATION_MS) {
    await delay(FETCH_MIN_DURATION_MS - totalElapsed);
  }

  if (activeFetchJobId !== jobId) {
    return;
  }

  fetchTargetPercent = 100;
  setFetchStepState("done");
  fetchProgressLabel.textContent = t("Import complete");
  fetchMessage.textContent = t("Import complete");
  await delay(450);

  stopFetchProgressAnimation();
  fetchDisplayPercent = 100;
  fetchProgressBar.style.width = "100%";
  fetchProgressGlow.style.left = "100%";
  fetchProgressPercent.textContent = "100%";

  const completedJob = pendingSuccessJob;
  pendingSuccessJob = null;
  renderFetchSuccess(completedJob);
}

function updateFetchProgress(job) {
  lastFetchJobSnapshot = { ...job, job_id: job.job_id ?? activeFetchJobId };
  applyFetchJobPresentation(job);
}

function renderFetchSuccess(job) {
  fetchView.classList.add("is-success");
  fetchView.classList.remove("is-error");
  fetchTitle.textContent = t("Import complete");

  const inserted = Number(job.inserted ?? job.result?.inserted ?? 0);
  const skipped = Number(job.skipped ?? job.result?.skipped ?? 0);
  const found = Number(job.tracks_found ?? job.result?.tracks_found ?? 0);
  const playlistCount = Number(
    job.playlist_total
    ?? job.result?.playlist_count
    ?? job.result?.playlists_checked
    ?? 0
  );
  const sinceDate = job.since_date ?? job.result?.since_date;
  const untilDate = job.until_date ?? job.result?.until_date;

  if (inserted > 0) {
    fetchMessage.textContent = tn(
      "1 new track added to your to-do list.",
      "{count} new tracks added to your to-do list.",
      inserted
    );
  } else if (found > 0 && skipped > 0) {
    fetchMessage.textContent = found === 1
      ? t("Found 1 track, but {skipped} already existed in your list.", { skipped })
      : t("Found {found} tracks, but {skipped} already existed in your list.", { found, skipped });
  } else if (sinceDate && untilDate) {
    if (!playlistCount) {
      fetchMessage.textContent = t(
        "Scanned your playlists — no new tracks between {since_date} and {until_date}.",
        { since_date: sinceDate, until_date: untilDate }
      );
    } else if (playlistCount === 1) {
      fetchMessage.textContent = t(
        "Scanned 1 playlist — no new tracks between {since_date} and {until_date}.",
        { since_date: sinceDate, until_date: untilDate }
      );
    } else {
      fetchMessage.textContent = t(
        "Scanned {count} playlists — no new tracks between {since_date} and {until_date}.",
        { count: playlistCount, since_date: sinceDate, until_date: untilDate }
      );
    }
  } else {
    fetchMessage.textContent = job.message || t("Your to-do list is up to date.");
  }

  fetchProgressBar.style.width = "100%";
  fetchProgressGlow.style.left = "100%";
  fetchProgressPercent.textContent = "100%";
  fetchProgressLabel.textContent = t("Done");
  fetchProgressWrap?.classList.remove("is-active");
  fetchPlaylistCard.hidden = true;
  fetchResult.hidden = false;
  fetchError.hidden = true;
  setFetchStepState("done");

  fetchResultStats.innerHTML = `
    <article class="fetch-stat">
      <span class="fetch-stat__label">Playlists scanned</span>
      <strong class="fetch-stat__value">${playlistCount || "—"}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">New tracks</span>
      <strong class="fetch-stat__value">${inserted}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">Tracks found</span>
      <strong class="fetch-stat__value">${found}</strong>
    </article>
  `;

  if (inserted > 0) {
    launchConfetti(window.innerWidth / 2, window.innerHeight / 3);
  }
}

function renderFetchError(message) {
  stopFetchProgressAnimation();
  stopFetchFinishSequence();
  fetchView.classList.add("is-error");
  fetchView.classList.remove("is-success");
  fetchTitle.textContent = t("Import failed");
  fetchMessage.textContent = message || t("Something went wrong while fetching tracks.");
  fetchProgressWrap?.classList.remove("is-active");
  fetchPlaylistCard.hidden = true;
  fetchResult.hidden = true;
  fetchError.hidden = false;
  fetchErrorMessage.textContent = message || t("Something went wrong while fetching tracks.");
}

function stopFetchPolling() {
  if (fetchPollTimer) {
    clearTimeout(fetchPollTimer);
    fetchPollTimer = null;
  }
}

async function pollFetchJob(jobId) {
  try {
    const response = await fetch(`/api/import/tracks/${encodeURIComponent(jobId)}`);
    const job = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(job.error || "Could not read import progress");
    }

    if (activeFetchJobId !== jobId) {
      return;
    }

    updateFetchProgress(job);

    if (job.status === "done") {
      scheduleFetchSuccess({ ...job, job_id: jobId });
      return;
    }

    if (job.status === "error") {
      stopFetchPolling();
      stopFetchFinishSequence();
      stopFetchProgressAnimation();
      renderFetchError(job.error || job.message || "Import failed");
      return;
    }

    fetchPollTimer = setTimeout(() => {
      pollFetchJob(jobId);
    }, FETCH_POLL_MS);
  } catch (error) {
    stopFetchPolling();
    renderFetchError(error.message || "Could not read import progress");
  }
}

async function startTrackImport() {
  if (!fetchView) {
    showStatus(t("Fetch screen is unavailable. Restart the web server."), "error");
    return;
  }

  resetFetchScreen();
  renderFetchParticles();
  fetchStartedAt = Date.now();
  startFetchProgressAnimation();
  fetchMessage.textContent = t("Connecting to Spotify…");

  try {
    const introDelay = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 700;
    await delay(introDelay);
    if (currentView !== "fetch") {
      stopFetchProgressAnimation();
      return;
    }

    const response = await fetch("/api/import/tracks", { method: "POST" });
    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      throw new Error(
        response.ok
          ? "Unexpected response from server"
          : `Server error (${response.status}). Restart the web server and use .venv/bin/python3 run_new_tracks_todo.py`
      );
    }
    if (!response.ok) {
      throw new Error(data.error || `Could not start import (${response.status})`);
    }

    activeFetchJobId = data.job_id;
    fetchMessage.textContent = t("Import started…");
    fetchTargetPercent = Math.max(fetchTargetPercent, FETCH_PHASE_PROGRESS.starting);
    pollFetchJob(data.job_id);
  } catch (error) {
    stopFetchProgressAnimation();
    renderFetchError(error.message || "Could not start import");
  }
}

function showFetchView() {
  restoreSettingsSkinIfNeeded();
  currentView = "fetch";
  currentGenre = null;
  currentFilter = null;
  document.title = t("Fetch tracks — {app_name}", { app_name: APP_NAME() });
  pageTitle.textContent = t("Fetch new tracks");
  pageSubtitle.textContent = t("Scanning tracking playlists for new tracks to download.");
  setPageCover(null);
  setSettingsLinkActive(false);
  hideAllViews();
  fetchView.hidden = false;
  setBanner("");
  updateBreadcrumbs();
  renderFetchParticles();
  startTrackImport();
}

function navigateToFetch({ replace = false } = {}) {
  const state = { view: "fetch", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", FETCH_PATH);
  } else {
    history.pushState(state, "", FETCH_PATH);
  }
  showFetchView();
}

function renderDownloadParticles() {
  if (!downloadParticles || downloadParticles.childElementCount) return;
  for (let i = 0; i < 10; i += 1) {
    const particle = document.createElement("li");
    particle.className = "fetch-particle";
    particle.style.left = `${12 + Math.random() * 76}%`;
    particle.style.top = `${12 + Math.random() * 76}%`;
    particle.style.animationDelay = `${Math.random() * 1.8}s`;
    downloadParticles.appendChild(particle);
  }
}

function resetDownloadScreen() {
  stopDownloadPolling();
  stopDownloadProgressAnimation();
  activeDownloadJobId = null;
  downloadStartedAt = 0;
  downloadDisplayPercent = 0;
  downloadTargetPercent = 0;
  downloadView.classList.remove("is-success", "is-error");
  downloadTitle.textContent = t("Downloading tracks");
  downloadMessage.textContent = t("Preparing download…");
  downloadProgressBar.style.width = "0%";
  downloadProgressGlow.style.left = "0%";
  downloadProgressWrap?.classList.add("is-active");
  downloadProgressLabel.textContent = t("Starting…");
  downloadProgressPercent.textContent = "0%";
  downloadTrackCard.hidden = true;
  downloadResult.hidden = true;
  downloadError.hidden = true;
  downloadResultStats.innerHTML = "";
  for (const step of downloadSteps.querySelectorAll(".fetch-step")) {
    step.classList.remove("is-active", "is-done");
  }
  downloadSteps.querySelector('[data-step="starting"]')?.classList.add("is-active");
}

function setDownloadStepState(phase) {
  const stepGroups = {
    starting: ["starting"],
    downloading: ["starting", "downloading"],
    done: ["starting", "downloading", "done"],
    error: ["starting", "downloading", "done"],
  };
  const activeKeys = new Set(stepGroups[phase] || ["starting"]);
  const order = ["starting", "downloading", "done"];
  let reachedActive = false;

  for (const key of order) {
    const step = downloadSteps.querySelector(`[data-step="${key}"]`);
    if (!step) continue;
    step.classList.remove("is-active", "is-done");
    if (activeKeys.has(key)) {
      if (!reachedActive) {
        step.classList.add("is-active");
        reachedActive = true;
      } else {
        step.classList.add("is-done");
      }
    } else if (phase === "done") {
      step.classList.add("is-done");
    }
  }
}

function computeDownloadPercent(job) {
  const phase = job.phase || "starting";
  if (phase === "starting" || phase === "queued") {
    return 8;
  }
  if (phase === "done") {
    return 100;
  }

  const index = Number(job.track_index || 0);
  const total = Number(job.track_total || 1);
  const sliceStart = 12;
  const sliceEnd = 96;
  const progress = total ? Math.min(1, Math.max(0, index / total)) : 0;
  return Math.round(sliceStart + (sliceEnd - sliceStart) * progress);
}

function stopDownloadProgressAnimation() {
  if (downloadProgressRaf) {
    cancelAnimationFrame(downloadProgressRaf);
    downloadProgressRaf = null;
  }
}

function startDownloadProgressAnimation() {
  stopDownloadProgressAnimation();

  const tick = () => {
    if (downloadDisplayPercent < downloadTargetPercent) {
      const delta = Math.max(0.35, (downloadTargetPercent - downloadDisplayPercent) * 0.08);
      downloadDisplayPercent = Math.min(downloadTargetPercent, downloadDisplayPercent + delta);
    }

    downloadProgressBar.style.width = `${downloadDisplayPercent}%`;
    downloadProgressGlow.style.left = `${downloadDisplayPercent}%`;
    downloadProgressPercent.textContent = `${Math.round(downloadDisplayPercent)}%`;
    downloadProgressRaf = requestAnimationFrame(tick);
  };

  downloadProgressRaf = requestAnimationFrame(tick);
}

function updateDownloadProgress(job) {
  const percent = computeDownloadPercent(job);
  downloadTargetPercent = Math.max(downloadTargetPercent, percent);
  downloadProgressLabel.textContent = job.message || t("Working…");
  downloadMessage.textContent = job.message || t("Working…");
  setDownloadStepState(job.phase || "starting");

  if (job.track_name) {
    downloadTrackCard.hidden = false;
    downloadTrackName.textContent = job.track_name;
  }
}

function renderDownloadSuccess(job) {
  downloadView.classList.add("is-success");
  downloadView.classList.remove("is-error");
  downloadTitle.textContent = t("Download complete");

  const successCount = Number(job.success_count ?? job.result?.success_count ?? 0);
  const errorCount = Number(job.error_count ?? job.result?.error_count ?? 0);
  const total = Number(job.track_total ?? successCount + errorCount);

  if (successCount > 0) {
    downloadMessage.textContent = tn(
      "1 track downloaded as AIFF.",
      "{count} tracks downloaded as AIFF.",
      successCount
    );
  } else {
    downloadMessage.textContent = t("No tracks were downloaded.");
  }

  downloadProgressBar.style.width = "100%";
  downloadProgressGlow.style.left = "100%";
  downloadProgressPercent.textContent = "100%";
  downloadProgressLabel.textContent = t("Done");
  downloadProgressWrap?.classList.remove("is-active");
  downloadTrackCard.hidden = true;
  downloadResult.hidden = false;
  downloadError.hidden = true;
  setDownloadStepState("done");

  downloadResultStats.innerHTML = `
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("Downloaded")}</span>
      <strong class="fetch-stat__value">${successCount}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("Failed")}</span>
      <strong class="fetch-stat__value">${errorCount}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("Total tracks")}</span>
      <strong class="fetch-stat__value">${total || "—"}</strong>
    </article>
  `;

  if (successCount > 0) {
    launchConfetti(window.innerWidth / 2, window.innerHeight / 3);
  }
}

function renderDownloadError(message) {
  stopDownloadProgressAnimation();
  downloadView.classList.add("is-error");
  downloadView.classList.remove("is-success");
  downloadTitle.textContent = t("Download failed");
  downloadMessage.textContent = message || t("Something went wrong while downloading tracks.");
  downloadProgressWrap?.classList.remove("is-active");
  downloadTrackCard.hidden = true;
  downloadResult.hidden = true;
  downloadError.hidden = false;
  downloadErrorMessage.textContent = message || t("Something went wrong while downloading tracks.");
}

function stopDownloadPolling() {
  if (downloadPollTimer) {
    clearTimeout(downloadPollTimer);
    downloadPollTimer = null;
  }
}

async function pollDownloadJob(jobId) {
  try {
    const response = await fetch(`/api/download/tracks/${encodeURIComponent(jobId)}`);
    const job = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(job.error || "Could not read download progress");
    }

    if (activeDownloadJobId !== jobId) {
      return;
    }

    updateDownloadProgress(job);

    if (job.status === "done") {
      stopDownloadPolling();
      stopDownloadProgressAnimation();
      downloadDisplayPercent = 100;
      const successCount = Number(job.success_count ?? job.result?.success_count ?? 0);
      const errorCount = Number(job.error_count ?? job.result?.error_count ?? 0);
      if (successCount === 0 && errorCount > 0) {
        renderDownloadError(
          job.last_error || job.error || job.message || t("No tracks were downloaded.")
        );
        return;
      }
      renderDownloadSuccess(job);
      return;
    }

    if (job.status === "error") {
      stopDownloadPolling();
      stopDownloadProgressAnimation();
      renderDownloadError(job.error || job.message || "Download failed");
      return;
    }

    downloadPollTimer = setTimeout(() => {
      pollDownloadJob(jobId);
    }, DOWNLOAD_POLL_MS);
  } catch (error) {
    stopDownloadPolling();
    renderDownloadError(error.message || "Could not read download progress");
  }
}

async function startTrackDownload() {
  if (!downloadView) {
    showStatus(t("Download screen is unavailable. Restart the web server."), "error");
    return;
  }

  resetDownloadScreen();
  renderDownloadParticles();
  downloadStartedAt = Date.now();
  startDownloadProgressAnimation();
  downloadMessage.textContent = t("Preparing download…");

  try {
    const response = await fetch("/api/download/tracks", { method: "POST" });
    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      throw new Error(
        response.ok
          ? "Unexpected response from server"
          : `Server error (${response.status}). Restart the web server and use .venv/bin/python3 run_new_tracks_todo.py`
      );
    }
    if (!response.ok) {
      const fallback = response.status === 404
        ? t("Download API not found. Restart the web server.")
        : `Could not start download (${response.status})`;
      throw new Error(data.error || fallback);
    }

    activeDownloadJobId = data.job_id;
    downloadMessage.textContent = t("Download started…");
    downloadTargetPercent = Math.max(downloadTargetPercent, 12);
    pollDownloadJob(data.job_id);
  } catch (error) {
    stopDownloadProgressAnimation();
    renderDownloadError(error.message || "Could not start download");
  }
}

function showDownloadView() {
  restoreSettingsSkinIfNeeded();
  currentView = "download";
  currentGenre = null;
  currentFilter = null;
  document.title = t("Download to AIFF — {app_name}", { app_name: APP_NAME() });
  pageTitle.textContent = t("Download to AIFF");
  pageSubtitle.textContent = t("Download tracks with YouTube URLs as AIFF files.");
  setPageCover(null);
  setSettingsLinkActive(false);
  hideAllViews();
  downloadView.hidden = false;
  setBanner("");
  updateBreadcrumbs();
  renderDownloadParticles();
  startTrackDownload();
}

function navigateToDownload({ replace = false } = {}) {
  const state = { view: "download", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", DOWNLOAD_PATH);
  } else {
    history.pushState(state, "", DOWNLOAD_PATH);
  }
  showDownloadView();
}

function renderSyncParticles() {
  if (!syncParticles) return;
  syncParticles.innerHTML = "";
  for (let i = 0; i < 10; i += 1) {
    const particle = document.createElement("li");
    particle.style.setProperty("--delay", `${(i * 0.28).toFixed(2)}s`);
    particle.style.setProperty("--x", `${20 + ((i * 37) % 60)}%`);
    syncParticles.appendChild(particle);
  }
}

function resetSyncPresentation() {
  stopSyncPolling();
  stopSyncProgressAnimation();
  activeSyncJobId = null;
  syncJobMissingPolls = 0;
  syncStartedAt = 0;
  syncLastJobUpdatedAt = 0;
  syncDisplayPercent = 0;
  syncTargetPercent = 0;
  syncView.classList.remove("is-success", "is-error");
  syncTitle.textContent = t("Syncing playlists");
  syncMessage.textContent = t("Connecting to Spotify…");
  syncProgressBar.style.width = "0%";
  syncProgressGlow.style.left = "0%";
  syncProgressWrap?.classList.add("is-active");
  syncProgressLabel.textContent = t("Starting…");
  syncProgressPercent.textContent = "0%";
  syncPlaylistCard.hidden = true;
  syncResult.hidden = true;
  syncError.hidden = true;
  syncResultStats.innerHTML = "";
  for (const step of syncSteps.querySelectorAll(".fetch-step")) {
    step.classList.remove("is-active", "is-done");
  }
  syncSteps.querySelector('[data-step="starting"]')?.classList.add("is-active");
}

function setSyncStepState(phase) {
  const stepGroups = {
    starting: ["starting"],
    queued: ["starting"],
    artists_start: ["starting", "artists"],
    artists_scanning: ["starting", "artists"],
    artists_done: ["starting", "artists"],
    artists: ["starting", "artists"],
    sources_start: ["starting", "artists", "sources"],
    playlist_start: ["starting", "artists", "sources"],
    fetching_tracks: ["starting", "artists", "sources"],
    playlist_done: ["starting", "artists", "sources"],
    playlist_error: ["starting", "artists", "sources"],
    sources: ["starting", "artists", "sources"],
    adding: ["starting", "artists", "sources", "adding"],
    done: ["starting", "artists", "sources", "adding", "done"],
    error: ["starting", "artists", "sources", "adding", "done"],
  };
  const activeKeys = new Set(stepGroups[phase] || ["starting"]);
  const order = ["starting", "artists", "sources", "adding", "done"];
  let reachedActive = false;

  for (const key of order) {
    const step = syncSteps.querySelector(`[data-step="${key}"]`);
    if (!step) continue;
    step.classList.remove("is-active", "is-done");
    if (activeKeys.has(key)) {
      if (!reachedActive) {
        step.classList.add("is-active");
        reachedActive = true;
      } else {
        step.classList.add("is-done");
      }
    } else if (phase === "done") {
      step.classList.add("is-done");
    }
  }
}

function computeSyncPercent(job) {
  const phase = job.phase || "starting";
  let percent = SYNC_PHASE_PROGRESS[phase] ?? 8;

  if (phase === "artists_scanning" || phase === "artists_start") {
    const index = Number(job.artist_index || 0);
    const total = Number(job.artist_total || 1);
    const sliceStart = SYNC_PHASE_PROGRESS.artists_start;
    const sliceEnd = SYNC_PHASE_PROGRESS.artists_done;
    const slice = sliceEnd - sliceStart;
    const artistProgress = total ? Math.min(1, Math.max(0, index / total)) : 0;
    percent = Math.round(sliceStart + slice * artistProgress);
  }

  if (
    phase === "playlist_start"
    || phase === "fetching_tracks"
    || phase === "playlist_done"
  ) {
    const index = Number(job.playlist_index || 0);
    const total = Number(job.playlist_total || 1);
    const sliceStart = SYNC_PHASE_PROGRESS.playlist_start;
    const sliceEnd = SYNC_PHASE_PROGRESS.playlist_done;
    const slice = sliceEnd - sliceStart;
    const playlistProgress = total ? Math.min(1, Math.max(0, (index - 1) / total)) : 0;
    percent = Math.round(sliceStart + slice * playlistProgress);
    if (phase === "fetching_tracks") {
      percent = Math.min(sliceEnd - 4, percent + Math.round(slice / total / 2));
    }
    if (phase === "playlist_done") {
      percent = Math.round(sliceStart + slice * Math.min(1, index / total));
    }
  }

  return percent;
}

function stopSyncProgressAnimation() {
  if (syncProgressRaf) {
    cancelAnimationFrame(syncProgressRaf);
    syncProgressRaf = null;
  }
}

function startSyncProgressAnimation() {
  stopSyncProgressAnimation();

  const tick = () => {
    if (syncDisplayPercent < syncTargetPercent) {
      const delta = Math.max(0.35, (syncTargetPercent - syncDisplayPercent) * 0.08);
      syncDisplayPercent = Math.min(syncTargetPercent, syncDisplayPercent + delta);
    }

    syncProgressBar.style.width = `${syncDisplayPercent}%`;
    syncProgressGlow.style.left = `${syncDisplayPercent}%`;
    syncProgressPercent.textContent = `${Math.round(syncDisplayPercent)}%`;
    syncProgressRaf = requestAnimationFrame(tick);
  };

  syncProgressRaf = requestAnimationFrame(tick);
}

function formatSyncMessage(job) {
  const base = job.message || t("Working…");
  if (job.status !== "running" || !syncLastJobUpdatedAt) {
    return base;
  }
  const staleMs = Date.now() - syncLastJobUpdatedAt;
  if (staleMs > 20000) {
    return `${base} — ${t("Waiting for Spotify…")}`;
  }
  return base;
}

function updateSyncProgress(job) {
  if (job.updated_at) {
    const parsed = Date.parse(job.updated_at);
    if (!Number.isNaN(parsed)) {
      syncLastJobUpdatedAt = parsed;
    }
  }

  const percent = computeSyncPercent(job);
  syncTargetPercent = Math.max(syncTargetPercent, percent);
  const message = formatSyncMessage(job);
  syncProgressLabel.textContent = message;
  syncMessage.textContent = message;
  setSyncStepState(job.phase || "starting");

  const isArtistPhase = String(job.phase || "").startsWith("artists");
  const cardName = isArtistPhase
    ? (job.artist_name || job.playlist_name)
    : job.playlist_name;

  if (syncPlaylistLabel) {
    syncPlaylistLabel.textContent = isArtistPhase
      ? t("Current artist")
      : t("Current playlist");
  }

  if (cardName) {
    syncPlaylistCard.hidden = false;
    syncPlaylistName.textContent = cardName;
    if (!isArtistPhase && job.playlist_image_url) {
      syncPlaylistArt.src = job.playlist_image_url;
      syncPlaylistArt.hidden = false;
      syncPlaylistPlaceholder.hidden = true;
    } else {
      syncPlaylistArt.hidden = true;
      syncPlaylistPlaceholder.hidden = false;
    }
  }
}

function renderSyncSuccess(job) {
  syncView.classList.add("is-success");
  syncView.classList.remove("is-error");
  syncTitle.textContent = t("Sync complete");

  const tracksAdded = Number(job.tracks_added ?? job.result?.tracks_added ?? 0);
  const tracksNew = Number(job.tracks_new ?? job.result?.tracks_new ?? 0);
  const artistNew = Number(job.artist_releases_new ?? job.result?.artist_releases_new ?? 0);
  const playlistsChecked = Number(
    job.playlists_checked
    ?? job.result?.playlists_checked
    ?? job.playlist_total
    ?? job.result?.playlist_count
    ?? 0
  );
  const sinceDate = job.since_date ?? job.result?.since_date;

  if (tracksAdded > 0) {
    syncMessage.textContent = tn(
      "1 track added to your destination playlist.",
      "{count} tracks added to your destination playlist.",
      tracksAdded
    );
  } else if (tracksNew > 0) {
    syncMessage.textContent = t("New tracks were already in your destination playlist.");
  } else {
    syncMessage.textContent = sinceDate
      ? t("No new source tracks found since {since_date}.", { since_date: sinceDate })
      : t("No new source tracks found.");
  }

  syncProgressBar.style.width = "100%";
  syncProgressGlow.style.left = "100%";
  syncProgressPercent.textContent = "100%";
  syncProgressLabel.textContent = t("Done");
  syncProgressWrap?.classList.remove("is-active");
  syncPlaylistCard.hidden = true;
  syncResult.hidden = false;
  syncError.hidden = true;
  setSyncStepState("done");

  syncResultStats.innerHTML = `
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("Added")}</span>
      <strong class="fetch-stat__value">${tracksAdded}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("New found")}</span>
      <strong class="fetch-stat__value">${tracksNew}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("From artists")}</span>
      <strong class="fetch-stat__value">${artistNew}</strong>
    </article>
    <article class="fetch-stat">
      <span class="fetch-stat__label">${t("Sources")}</span>
      <strong class="fetch-stat__value">${playlistsChecked || "—"}</strong>
    </article>
  `;

  if (tracksAdded > 0) {
    launchConfetti(window.innerWidth / 2, window.innerHeight / 3);
  }
}

function renderSyncError(message) {
  stopSyncProgressAnimation();
  syncView.classList.add("is-error");
  syncView.classList.remove("is-success");
  syncTitle.textContent = t("Sync failed");
  syncMessage.textContent = message || t("Something went wrong while syncing playlists.");
  syncProgressWrap?.classList.remove("is-active");
  syncPlaylistCard.hidden = true;
  syncResult.hidden = true;
  syncError.hidden = false;
  syncErrorMessage.textContent = message || t("Something went wrong while syncing playlists.");
}

function stopSyncPolling() {
  if (syncPollTimer) {
    clearTimeout(syncPollTimer);
    syncPollTimer = null;
  }
}

async function pollSyncJob(jobId) {
  try {
    const response = await fetch(`/api/sync/playlists/${encodeURIComponent(jobId)}`);
    const job = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 404 && syncJobMissingPolls < 12) {
        syncJobMissingPolls += 1;
        syncPollTimer = setTimeout(() => pollSyncJob(jobId), SYNC_POLL_MS);
        return;
      }
      throw new Error(job.error || "Could not read sync progress");
    }

    syncJobMissingPolls = 0;

    if (activeSyncJobId !== jobId) {
      return;
    }

    updateSyncProgress(job);

    if (job.status === "done") {
      stopSyncPolling();
      stopSyncProgressAnimation();
      syncDisplayPercent = 100;
      renderSyncSuccess(job);
      return;
    }

    if (job.status === "error") {
      stopSyncPolling();
      renderSyncError(job.error || job.message || t("Sync failed"));
      return;
    }

    syncPollTimer = setTimeout(() => pollSyncJob(jobId), SYNC_POLL_MS);
  } catch (error) {
    if (activeSyncJobId !== jobId) {
      return;
    }
    stopSyncPolling();
    renderSyncError(error.message || t("Sync failed"));
  }
}

async function resumeOrStartPlaylistSync({ force = false } = {}) {
  if (!syncView) {
    showStatus(t("Sync screen is unavailable. Restart the web server."), "error");
    return;
  }

  resetSyncPresentation();
  syncStartedAt = Date.now();
  startSyncProgressAnimation();
  syncTargetPercent = Math.max(syncTargetPercent, SYNC_PHASE_PROGRESS.starting);
  syncProgressLabel.textContent = t("Sync started…");
  syncMessage.textContent = t("Connecting to Spotify…");

  try {
    if (!force) {
      const activeResponse = await fetch("/api/sync/playlists/active");
      if (activeResponse.ok) {
        const activeJob = await activeResponse.json();
        if (activeJob?.job_id) {
          activeSyncJobId = activeJob.job_id;
          syncMessage.textContent = t("Resuming sync…");
          updateSyncProgress(activeJob);
          pollSyncJob(activeJob.job_id);
          return;
        }
      }
    }

    const response = await fetch(
      force ? "/api/sync/playlists?force=1" : "/api/sync/playlists",
      { method: "POST" },
    );
    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = {};
    }
    if (!response.ok) {
      throw new Error(data.error || raw || "Could not start sync");
    }
    if (!data.job_id) {
      throw new Error("Sync job id missing from response");
    }
    activeSyncJobId = data.job_id;
    pollSyncJob(data.job_id);
  } catch (error) {
    stopSyncProgressAnimation();
    renderSyncError(error.message || t("Could not start sync"));
  }
}

async function startPlaylistSync({ force = false } = {}) {
  return resumeOrStartPlaylistSync({ force });
}

function showSyncView() {
  restoreSettingsSkinIfNeeded();
  currentView = "sync";
  currentGenre = null;
  currentFilter = null;
  document.title = t("Sync playlists — {app_name}", { app_name: APP_NAME() });
  pageTitle.textContent = t("Sync playlists");
  pageSubtitle.textContent = t("Scanning followed artists and source playlists since your sync start date.");
  setPageCover(null);
  setSettingsLinkActive(false);
  hideAllViews();
  syncView.hidden = false;
  setBanner("");
  updateBreadcrumbs();
  renderSyncParticles();
  resumeOrStartPlaylistSync();
}

function navigateToSync({ replace = false } = {}) {
  const state = { view: "sync", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", SYNC_PATH);
  } else {
    history.pushState(state, "", SYNC_PATH);
  }
  showSyncView();
}

function showSettingsView() {
  currentView = "settings";
  currentGenre = null;
  currentFilter = null;
  document.title = t("Settings — {app_name}", { app_name: APP_NAME() });
  pageTitle.textContent = t("Settings");
  pageSubtitle.textContent = t("Customize your sync workflow and visual style.");
  setPageCover(null);
  setSettingsLinkActive(true);
  hideAllViews();
  settingsView.hidden = false;
  updateBreadcrumbs();
}

function formatPlaylistCount(count) {
  return tn("1 playlist", "{count} playlists", count);
}

function updateSettingsCounts() {
  const sourceCount = collectPlaylistValues(sourcePlaylistsList).length;
  const trackingCount = collectPlaylistValues(trackingPlaylistsList).length;
  sourcePlaylistCount.textContent = formatPlaylistCount(sourceCount);
  trackingPlaylistCount.textContent = formatPlaylistCount(trackingCount);
}

function markSettingsDirty() {
  settingsDock.classList.add("is-dirty");
  settingsDockText.textContent = t("Unsaved changes");
}

function markSettingsClean(message = t("Ready to save")) {
  settingsDock.classList.remove("is-dirty");
  settingsDockText.textContent = message;
}

function previewSelectedTheme() {
  const selectedSkin = settingsForm.querySelector('input[name="ui_skin"]:checked')?.value || "colorful";
  document.documentElement.dataset.skin = selectedSkin;
}

function showGenreHub(genre) {
  restoreSettingsSkinIfNeeded();
  currentView = "genre";
  currentGenre = genre;
  currentFilter = null;
  document.title = t("{genre} — Track to-do — {app_name}", { genre, app_name: APP_NAME() });
  pageTitle.textContent = genre;
  pageSubtitle.textContent = t("Choose whether to view tracks with or without a reference URL.");
  setPageCover(genreImageBySlug[genre] || null);
  setSettingsLinkActive(false);
  hideAllViews();
  genreHubView.hidden = false;
  updateBreadcrumbs();
}

function showTracksView(genre, filter) {
  restoreSettingsSkinIfNeeded();
  currentView = "tracks";
  currentGenre = genre;
  currentFilter = filter;
  const filterLabel = filter === FILTER_WITH_URL
    ? t("tracks with a reference URL")
    : t("tracks still missing a reference URL");
  document.title = t("{genre} — Track to-do — {app_name}", { genre, app_name: APP_NAME() });
  pageTitle.textContent = genre;
  pageSubtitle.textContent = t("Showing {filter_label}.", { filter_label: filterLabel });
  setPageCover(genreImageBySlug[genre] || null);
  setSettingsLinkActive(false);
  hideAllViews();
  tracksView.hidden = false;
  applyFilterView();
  updateBreadcrumbs();
}

function applyFilterView() {
  const showDone = currentFilter === FILTER_WITH_URL;
  columnDone.hidden = !showDone;
  columnTodo.hidden = showDone;
  tabWithUrl.classList.toggle("active", showDone);
  tabWithoutUrl.classList.toggle("active", !showDone);
  tabWithUrl.href = genrePath(currentGenre, FILTER_WITH_URL);
  tabWithoutUrl.href = genrePath(currentGenre, FILTER_WITHOUT_URL);
}

function navigateToGenre(genre, { replace = false } = {}) {
  cachedTracks = { with_url: [], without_url: [] };
  const path = genrePath(genre);
  const state = { genre, filter: null };
  if (replace) {
    history.replaceState(state, "", path);
  } else {
    history.pushState(state, "", path);
  }
  showGenreHub(genre);
  loadGenreHub(genre);
}

function updateCounts() {
  const doneCount = cachedTracks.with_url.length;
  const todoCount = cachedTracks.without_url.length;
  document.getElementById("count-done").textContent = String(
    listDone.querySelectorAll(".track-item").length
  );
  document.getElementById("count-todo").textContent = String(
    listTodo.querySelectorAll(".track-item").length
  );
  document.getElementById("tab-count-done").textContent = String(doneCount);
  document.getElementById("tab-count-todo").textContent = String(todoCount);
}

function renderCurrentFilterLists() {
  renderList(
    listDone,
    currentFilter === FILTER_WITH_URL ? cachedTracks.with_url : []
  );
  renderList(
    listTodo,
    currentFilter === FILTER_WITHOUT_URL ? cachedTracks.without_url : []
  );
  updateCounts();
}

function navigateToFilter(genre, filter, { replace = false } = {}) {
  const path = genrePath(genre, filter);
  const state = { genre, filter };
  if (replace) {
    history.replaceState(state, "", path);
  } else {
    history.pushState(state, "", path);
  }
  showTracksView(genre, filter);
  if (cachedTracks.with_url.length || cachedTracks.without_url.length) {
    renderCurrentFilterLists();
  } else {
    loadTracks(genre);
  }
}

function navigateToStart({ replace = false } = {}) {
  const state = { view: "start", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", START_PATH);
  } else {
    history.pushState(state, "", START_PATH);
  }
  showStartView();
}

function navigateToTodo({ replace = false } = {}) {
  const state = { view: "home", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", TODO_PATH);
  } else {
    history.pushState(state, "", TODO_PATH);
  }
  showGenreView();
  loadGenres();
}

function navigateToStatistics({ replace = false } = {}) {
  const state = { view: "statistics", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", STATISTICS_PATH);
  } else {
    history.pushState(state, "", STATISTICS_PATH);
  }
  showStatisticsView();
  loadStatistics();
}

function navigateToSettings({ replace = false } = {}) {
  const state = { view: "settings", genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", SETTINGS_PATH);
  } else {
    history.pushState(state, "", SETTINGS_PATH);
  }
  showSettingsView();
  loadSettings();
}

function restoreSettingsSkinIfNeeded() {
  if (settingsDock.classList.contains("is-dirty")) {
    document.documentElement.dataset.skin = savedSettingsSkin;
  }
}

function populateSettingsForm(settings) {
  const skin = settings.ui_skin || "colorful";
  const locale = settings.locale || "en";
  savedSettingsSkin = skin;
  savedSettingsLocale = locale;
  for (const input of settingsForm.querySelectorAll('input[name="ui_skin"]')) {
    input.checked = input.value === skin;
  }
  for (const input of settingsForm.querySelectorAll('input[name="locale"]')) {
    input.checked = input.value === locale;
  }

  settingsForm.destination_playlist.value = settings.destination_playlist?.spotify_id || "";
  if (settings.destination_playlist?.name) {
    setPlaylistMeta(destinationPlaylistMeta, settings.destination_playlist.name);
  } else {
    setPlaylistMeta(destinationPlaylistMeta, "");
  }

  renderPlaylistList(sourcePlaylistsList, settings.source_playlists);
  renderPlaylistList(trackingPlaylistsList, settings.tracking_playlists);
  settingsForm.sync_start_date.value = settings.sync_start_date || "";
  settingsForm.tracking_start_date.value = settings.tracking_start_date || "";
  updateSettingsCounts();
  markSettingsClean();
}

async function loadSettings() {
  setBanner(t("Loading settings…"), "loading");
  try {
    const response = await fetch("/api/settings");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || t("Could not load settings"));
    }

    populateSettingsForm(data);
    document.documentElement.dataset.skin = data.ui_skin || "colorful";
    setBanner("");
  } catch (error) {
    setBanner(t("Failed to load settings: {message}", { message: error.message }), "error");
    showStatus(error.message, "error");
  }
}

async function saveSettings(event) {
  event.preventDefault();
  const button = settingsForm.querySelector('button[type="submit"]');
  button.disabled = true;
  settingsDockText.textContent = t("Saving…");

  const selectedSkin = settingsForm.querySelector('input[name="ui_skin"]:checked')?.value || "colorful";
  const selectedLocale = settingsForm.querySelector('input[name="locale"]:checked')?.value || "en";
  const previousLocale = savedSettingsLocale;
  const payload = {
    ui_skin: selectedSkin,
    locale: selectedLocale,
    destination_playlist: settingsForm.destination_playlist.value.trim(),
    source_playlists: collectPlaylistValues(sourcePlaylistsList),
    tracking_playlists: collectPlaylistValues(trackingPlaylistsList),
    sync_start_date: settingsForm.sync_start_date.value.trim() || null,
    tracking_start_date: settingsForm.tracking_start_date.value.trim() || null,
  };

  try {
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || t("Could not save settings"));
    }

    populateSettingsForm(data);
    document.documentElement.dataset.skin = data.ui_skin || selectedSkin;
    savedSettingsSkin = data.ui_skin || selectedSkin;
    savedSettingsLocale = data.locale || selectedLocale;
    markSettingsClean(t("All changes saved"));
    showStatus(t("Settings saved"));
    if ((data.locale || selectedLocale) !== previousLocale) {
      window.location.reload();
      return;
    }
  } catch (error) {
    markSettingsDirty();
    showStatus(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

function navigateToGenreHub({ replace = false } = {}) {
  if (!currentGenre) {
    navigateToTodo({ replace });
    return;
  }
  const path = genrePath(currentGenre);
  const state = { genre: currentGenre, filter: null };
  if (replace) {
    history.replaceState(state, "", path);
  } else {
    history.pushState(state, "", path);
  }
  showGenreHub(currentGenre);
  loadGenreHub(currentGenre);
}

function renderFilterChoices(withUrlCount, withoutUrlCount) {
  filterGrid.innerHTML = "";
  const genreImageUrl = genreImageBySlug[currentGenre] || null;

  const choices = [
    {
      filter: FILTER_WITH_URL,
      label: t("Has reference URL"),
      count: withUrlCount,
      className: "filter-card--done",
    },
    {
      filter: FILTER_WITHOUT_URL,
      label: t("Needs reference URL"),
      count: withoutUrlCount,
      className: "filter-card--todo",
    },
  ];

  for (const choice of choices) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.className = `filter-card ${choice.className}`;
    link.href = genrePath(currentGenre, choice.filter);
    link.innerHTML = `
      ${artMarkup(genreImageUrl, "card-art", currentGenre || "")}
      <span class="filter-card__body">
        <span class="filter-card__name">${escapeHtml(choice.label)}</span>
        <span class="filter-card__count">${tn("1 track", "{count} tracks", choice.count)}</span>
      </span>
    `;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      navigateToFilter(currentGenre, choice.filter);
    });
    item.appendChild(link);
    filterGrid.appendChild(item);
  }
}

async function loadGenreHub(genre = currentGenre) {
  setBanner(t("Loading track counts…"), "loading");
  try {
    const response = await fetch(`/api/tracks?genre=${encodeURIComponent(genre)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || t("Could not load tracks"));
    }

    cachedTracks = {
      with_url: data.with_url || [],
      without_url: data.without_url || [],
    };
    if (data.genre_image_url) {
      genreImageBySlug[genre] = data.genre_image_url;
      setPageCover(data.genre_image_url);
    }
    renderFilterChoices(cachedTracks.with_url.length, cachedTracks.without_url.length);

    if (!data.total) {
      setBanner(t("No tracks found for {genre}.", { genre }), "error");
    } else {
      setBanner("");
    }
  } catch (error) {
    setBanner(t("Failed to load tracks: {message}", { message: error.message }), "error");
    showStatus(error.message, "error");
  }
}

function renderGenreList(genres) {
  genreGrid.innerHTML = "";
  genreImageBySlug = {};
  if (!genres.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = t("No genres found.");
    genreGrid.appendChild(empty);
    return;
  }

  for (const genre of genres) {
    if (genre.image_url) {
      genreImageBySlug[genre.slug] = genre.image_url;
    }
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.className = "genre-card";
    link.href = genrePath(genre.slug);
    link.innerHTML = `
      ${artMarkup(genre.image_url, "card-art", genre.label)}
      <span class="genre-card__body">
        <span class="genre-card__name">${escapeHtml(genre.label)}</span>
        <span class="genre-card__count">${tn("1 track", "{count} tracks", genre.track_count)}</span>
      </span>
    `;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      navigateToGenre(genre.slug);
    });
    item.appendChild(link);
    genreGrid.appendChild(item);
  }
}

async function loadGenres() {
  setBanner(t("Loading genres…"), "loading");
  try {
    const response = await fetch("/api/genres");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || t("Could not load genres"));
    }

    renderGenreList(data.genres || []);
    knownGenres = (data.genres || []).map((genre) => genre.slug);
    if (!data.total) {
      setBanner(t("No tracks found in new_tracks table."), "error");
    } else {
      setBanner("");
    }
  } catch (error) {
    setBanner(t("Failed to load genres: {message}", { message: error.message }), "error");
    showStatus(error.message, "error");
  }
}

function setCopyTitleCount(nameEl, count) {
  nameEl.dataset.count = String(count);
  let countEl = nameEl.querySelector(".track-name-count");
  if (count > 0) {
    if (!countEl) {
      countEl = document.createElement("span");
      countEl.className = "track-name-count";
      countEl.setAttribute("aria-hidden", "true");
      nameEl.appendChild(countEl);
    }
    countEl.textContent = ` (${count})`;
  } else if (countEl) {
    countEl.remove();
  }
}

function getCopyTitleCount(item) {
  return Number(item.querySelector(".track-name")?.dataset.count || 0);
}

async function recordCopyTitleClick(item, trackId) {
  const nameEl = item.querySelector(".track-name");
  const previous = Number(nameEl.dataset.count || 0);
  const optimistic = previous + 1;
  setCopyTitleCount(nameEl, optimistic);

  try {
    const response = await fetch(`/api/tracks/${trackId}/copy-title`, {
      method: "POST",
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || t("Could not record click"));
    }

    setCopyTitleCount(nameEl, Number(data.copy_title_count || optimistic));
  } catch (error) {
    setCopyTitleCount(nameEl, previous);
    showStatus(error.message || t("Could not save click count"), "error");
  }
}

function highlightTrackTitle(trackItem) {
  if (lastHighlightedName) {
    lastHighlightedName.classList.remove("track-name--highlight");
  }
  const nameEl = trackItem.querySelector(".track-name");
  if (!nameEl) return;
  void nameEl.offsetWidth;
  nameEl.classList.add("track-name--highlight");
  lastHighlightedName = nameEl;
}

function applyListSpacing(container) {
  const items = container.querySelectorAll(".track-item");
  items.forEach((item, index) => {
    const groupIndex = Math.floor(index / 5);
    item.classList.toggle("group-break", index > 0 && index % 5 === 0);
    item.classList.toggle("zebra-a", groupIndex % 2 === 0);
    item.classList.toggle("zebra-b", groupIndex % 2 === 1);

    let indexEl = item.querySelector(".track-index");
    if (!indexEl) {
      indexEl = document.createElement("span");
      indexEl.className = "track-index";
      indexEl.setAttribute("aria-hidden", "true");
      item.appendChild(indexEl);
    }
    indexEl.textContent = String(index + 1);
  });
}

function applyAllListSpacing() {
  applyListSpacing(listDone);
  applyListSpacing(listTodo);
}

function setBanner(message, type = "loading") {
  bannerEl.textContent = message;
  bannerEl.className = `banner ${type}`;
  bannerEl.hidden = !message;
}

function showStatus(message, type = "success") {
  statusEl.textContent = message;
  statusEl.className = `status visible ${type}`;
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => {
    statusEl.classList.remove("visible");
  }, 2200);
}

function showCopyToast(message) {
  copyToastEl.textContent = message;
  copyToastEl.classList.add("visible");
  clearTimeout(copyToastTimer);
  copyToastTimer = setTimeout(() => {
    copyToastEl.classList.remove("visible");
  }, 1400);
}

function launchConfetti(x, y) {
  const canvas = document.createElement("canvas");
  canvas.className = "confetti-canvas";
  document.body.appendChild(canvas);
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const skin = document.documentElement.dataset.skin || "colorful";
  const colors = skin === "light"
    ? ["#000000", "#333333", "#666666", "#999999", "#cccccc", "#ffffff"]
    : skin === "dark"
      ? ["#444444", "#666666", "#888888", "#aaaaaa", "#cccccc", "#f0f0f0"]
      : ["#39ff14", "#a855ff", "#ff2bd6", "#c8ffb8", "#ff9de8", "#f4f0ff"];
  const particles = Array.from({ length: 90 }, () => ({
    x,
    y,
    vx: (Math.random() - 0.5) * 14,
    vy: Math.random() * -12 - 4,
    size: Math.random() * 7 + 4,
    color: colors[Math.floor(Math.random() * colors.length)],
    rotation: Math.random() * Math.PI * 2,
    spin: (Math.random() - 0.5) * 0.3,
    life: 1,
  }));

  let frame = 0;
  const maxFrames = 110;

  function tick() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.28;
      p.vx *= 0.99;
      p.rotation += p.spin;
      p.life = Math.max(0, 1 - frame / maxFrames);
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rotation);
      ctx.globalAlpha = p.life;
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
      ctx.restore();
    }
    frame += 1;
    if (frame < maxFrames) {
      requestAnimationFrame(tick);
    } else {
      canvas.remove();
    }
  }

  requestAnimationFrame(tick);
}

async function copyText(text, label) {
  if (!text) {
    showCopyToast(t("Nothing to copy"));
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    showCopyToast(t("{label} copied", { label }));
  } catch (error) {
    showCopyToast(t("Could not copy {label}", { label: label.toLowerCase() }));
  }
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function createTrackItem(track) {
  const li = document.createElement("li");
  li.className = "track-item";
  li.dataset.id = String(track.id);

  const safeUrl = track.reference_url ? escapeHtml(track.reference_url) : "";
  const copyTitleCount = Number(track.copy_title_count || 0);
  const genreHtml = !currentGenre && track.genre
    ? `<div class="track-genre">${escapeHtml(track.genre)}</div>`
    : "";
  const energyHtml = track.energy != null
    ? `<div class="track-energy">${t("Energy: {value}", { value: Number(track.energy).toFixed(2) })}</div>`
    : "";

  li.innerHTML = `
    <div class="track-main">
      ${artMarkup(track.image_url, "track-art", track.track)}
      <div class="track-body">
        <div class="track-heading">
          <div class="track-name" data-count="${copyTitleCount}" role="button" tabindex="0" title="${t('Click to copy title')}">${escapeHtml(track.track)}</div>
          ${genreHtml}
          ${energyHtml}
        </div>
        <form class="track-form">
          <input type="url" name="reference_url" placeholder="https://..." value="${safeUrl}" />
          <button type="submit">${t("Save")}</button>
          <button type="button" class="remove">${t("Remove")}</button>
        </form>
      </div>
    </div>
  `;

  const nameEl = li.querySelector(".track-name");
  if (copyTitleCount > 0) {
    setCopyTitleCount(nameEl, copyTitleCount);
  }

  function handleTitleCopy() {
    highlightTrackTitle(li);
    copyText(track.track, t("Title"));
    recordCopyTitleClick(li, track.id);
  }

  nameEl.addEventListener("click", handleTitleCopy);
  nameEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleTitleCopy();
    }
  });

  const form = li.querySelector("form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    highlightTrackTitle(li);
    const button = form.querySelector("button");
    const input = form.querySelector("input");
    button.disabled = true;

    try {
      const response = await fetch(`/api/tracks/${track.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference_url: input.value.trim() }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || t("Save failed"));
      }

      const updated = await response.json();
      moveTrackItem(li, updated.has_url, {
        id: track.id,
        track: track.track,
        reference_url: updated.reference_url,
        genre: track.genre,
        energy: track.energy,
        image_url: track.image_url,
        copy_title_count: getCopyTitleCount(li),
      });
      showStatus(updated.has_url ? t("Saved — moved to Has URL list") : t("Cleared — moved to Needs URL list"));
    } catch (error) {
      showStatus(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });

  const removeButton = li.querySelector("button.remove");
  removeButton.addEventListener("click", () => {
    highlightTrackTitle(li);
    removeTrackItem(li, track);
  });

  return li;
}

async function removeTrackItem(item, track) {
  const ok = window.confirm(t('Remove "{track}" from the list?', { track: track.track }));
  if (!ok) return;

  try {
    const response = await fetch(`/api/tracks/${track.id}`, { method: "DELETE" });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || t("Remove failed"));
    }

    const rect = item.getBoundingClientRect();
    const originX = rect.left + rect.width / 2;
    const originY = rect.top + rect.height / 3;
    item.classList.add("track-item--removing");
    launchConfetti(originX, originY);

    await new Promise((resolve) => setTimeout(resolve, 450));
    item.remove();
    cachedTracks.with_url = cachedTracks.with_url.filter((entry) => entry.id !== track.id);
    cachedTracks.without_url = cachedTracks.without_url.filter((entry) => entry.id !== track.id);
    if (lastHighlightedName && !document.contains(lastHighlightedName)) {
      lastHighlightedName = null;
    }
    updateEmptyStates();
    updateCounts();
    applyAllListSpacing();
    showStatus(t("Track removed"));
  } catch (error) {
    showStatus(error.message, "error");
  }
}

function moveTrackItem(item, hasUrl, track) {
  const wasHighlighted = item.querySelector(".track-name--highlight") !== null;
  const sourceList = item.parentElement;
  item.remove();

  if (hasUrl) {
    cachedTracks.with_url = insertTrackSorted(cachedTracks.with_url, track);
    cachedTracks.without_url = cachedTracks.without_url.filter((entry) => entry.id !== track.id);
  } else {
    cachedTracks.without_url = insertTrackSorted(cachedTracks.without_url, track);
    cachedTracks.with_url = cachedTracks.with_url.filter((entry) => entry.id !== track.id);
  }

  const staysVisible = (hasUrl && currentFilter === FILTER_WITH_URL)
    || (!hasUrl && currentFilter === FILTER_WITHOUT_URL);

  if (staysVisible) {
    const target = hasUrl ? listDone : listTodo;
    const replacement = createTrackItem(track);
    target.appendChild(replacement);
    if (wasHighlighted) highlightTrackTitle(replacement);
  } else if (sourceList) {
    updateEmptyStates();
  }

  updateCounts();
  applyAllListSpacing();
}

function insertTrackSorted(tracks, track) {
  const next = tracks.filter((entry) => entry.id !== track.id);
  const name = track.track.toLowerCase();
  const index = next.findIndex((entry) => entry.track.toLowerCase() > name);
  if (index === -1) {
    next.push(track);
  } else {
    next.splice(index, 0, track);
  }
  return next;
}

function appendTrackItem(track) {
  if (track.reference_url) {
    cachedTracks.with_url = insertTrackSorted(cachedTracks.with_url, track);
  } else {
    cachedTracks.without_url = insertTrackSorted(cachedTracks.without_url, track);
  }

  const matchesFilter = (track.reference_url && currentFilter === FILTER_WITH_URL)
    || (!track.reference_url && currentFilter === FILTER_WITHOUT_URL);
  if (!matchesFilter) {
    updateCounts();
    return;
  }

  const target = track.reference_url ? listDone : listTodo;
  const item = createTrackItem(track);
  const empty = target.querySelector(".empty");
  if (empty) empty.remove();

  const items = [...target.querySelectorAll(".track-item")];
  const name = track.track.toLowerCase();
  let inserted = false;
  for (const existing of items) {
    const existingName = existing.querySelector(".track-name").textContent.toLowerCase();
    if (name < existingName) {
      target.insertBefore(item, existing);
      inserted = true;
      break;
    }
  }
  if (!inserted) target.appendChild(item);
  updateCounts();
  applyAllListSpacing();
}

function renderList(container, tracks) {
  container.innerHTML = "";
  if (!tracks.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = container === listDone
      ? t("No tracks with a URL yet.")
      : t("All tracks have a reference URL.");
    container.appendChild(empty);
    return;
  }

  for (const track of tracks) {
    container.appendChild(createTrackItem(track));
  }
  applyListSpacing(container);
}

function updateEmptyStates() {
  for (const list of [listDone, listTodo]) {
    const items = list.querySelectorAll(".track-item");
    const empty = list.querySelector(".empty");
    if (items.length === 0 && !empty) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = list === listDone
        ? "No tracks with a URL yet."
        : "All tracks have a reference URL.";
      list.appendChild(li);
    } else if (items.length > 0 && empty) {
      empty.remove();
    }
  }
}

function updateCounts() {
  const doneCount = cachedTracks.with_url.length;
  const todoCount = cachedTracks.without_url.length;
  document.getElementById("count-done").textContent = String(
    currentFilter === FILTER_WITH_URL
      ? listDone.querySelectorAll(".track-item").length
      : doneCount
  );
  document.getElementById("count-todo").textContent = String(
    currentFilter === FILTER_WITHOUT_URL
      ? listTodo.querySelectorAll(".track-item").length
      : todoCount
  );
  document.getElementById("tab-count-done").textContent = String(doneCount);
  document.getElementById("tab-count-todo").textContent = String(todoCount);
}

async function loadTracks(genre = currentGenre) {
  setBanner(t("Loading tracks from database…"), "loading");
  try {
    const query = genre ? `?genre=${encodeURIComponent(genre)}` : "";
    const response = await fetch(`/api/tracks${query}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || t("Could not load tracks"));
    }

    cachedTracks = {
      with_url: data.with_url || [],
      without_url: data.without_url || [],
    };
    if (data.genre_image_url) {
      genreImageBySlug[genre] = data.genre_image_url;
      setPageCover(data.genre_image_url);
    }
    renderCurrentFilterLists();

    if (!data.total) {
      setBanner(t("No tracks found for {genre}.", { genre }), "error");
    } else {
      setBanner("");
    }
  } catch (error) {
    setBanner(t("Failed to load tracks: {message}", { message: error.message }), "error");
    showStatus(error.message, "error");
  }
}

async function bootFromPath() {
  const { view, genre: urlSlug, filter } = parsePath(window.location.pathname);
  if (view === "settings") {
    showSettingsView();
    loadSettings();
    return;
  }
  if (view === "statistics") {
    showStatisticsView();
    loadStatistics();
    return;
  }
  if (view === "fetch") {
    showFetchView();
    return;
  }
  if (view === "sync") {
    showSyncView();
    return;
  }
  if (view === "download") {
    showDownloadView();
    return;
  }
  if (view === "start") {
    showStartView();
    return;
  }
  if (view === "home") {
    showGenreView();
    loadGenres();
    return;
  }

  try {
    await ensureKnownGenres();
  } catch (error) {
    showGenreView();
    setBanner(t("Failed to load genres: {message}", { message: error.message }), "error");
    return;
  }

  const genre = resolveGenreSlug(urlSlug);
  normalizeRoutePath(genre, filter || null);

  if (genre && filter) {
    showTracksView(genre, filter);
    loadTracks(genre);
  } else if (genre) {
    showGenreHub(genre);
    loadGenreHub(genre);
  } else {
    showGenreView();
    loadGenres();
  }
}

bootFromPath();

fetchRunAgainBtn?.addEventListener("click", () => {
  startTrackImport();
});

fetchRetryBtn?.addEventListener("click", () => {
  startTrackImport();
});

document.getElementById("fetch-go-todo")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToTodo();
});

document.getElementById("fetch-go-home")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToStart();
});

document.getElementById("fetch-go-settings")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToSettings();
});

syncRunAgainBtn?.addEventListener("click", () => {
  startPlaylistSync({ force: true });
});

syncRetryBtn?.addEventListener("click", () => {
  startPlaylistSync({ force: true });
});

document.getElementById("sync-go-home")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToStart();
});

document.getElementById("sync-go-settings")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToSettings();
});

document.getElementById("sync-error-settings")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToSettings();
});

downloadRunAgainBtn?.addEventListener("click", () => {
  startTrackDownload();
});

downloadRetryBtn?.addEventListener("click", () => {
  startTrackDownload();
});

document.getElementById("download-go-todo")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToTodo();
});

document.getElementById("download-go-home")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToStart();
});

document.getElementById("download-go-settings")?.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToSettings();
});

settingsLink.addEventListener("click", (event) => {
  event.preventDefault();
  navigateToSettings();
});

settingsForm.addEventListener("submit", saveSettings);

settingsForm.addEventListener("input", (event) => {
  if (event.target.name === "destination_playlist") {
    setPlaylistMeta(destinationPlaylistMeta, "");
    scheduleDestinationLookup();
  }
  markSettingsDirty();
});

settingsForm.addEventListener("change", (event) => {
  if (event.target.name === "ui_skin") {
    previewSelectedTheme();
  }
  if (event.target.name === "locale") {
    markSettingsDirty();
  }
  if (event.target.name === "destination_playlist") {
    lookupDestinationPlaylist();
  }
  markSettingsDirty();
});

addSourcePlaylistBtn.addEventListener("click", () => {
  const row = createPlaylistRow();
  sourcePlaylistsList.appendChild(row);
  row.querySelector(".playlist-id-input")?.focus();
  updateSettingsCounts();
  markSettingsDirty();
});

addTrackingPlaylistBtn.addEventListener("click", () => {
  const row = createPlaylistRow();
  trackingPlaylistsList.appendChild(row);
  row.querySelector(".playlist-id-input")?.focus();
  updateSettingsCounts();
  markSettingsDirty();
});

tabWithUrl.addEventListener("click", (event) => {
  event.preventDefault();
  if (currentGenre) {
    navigateToFilter(currentGenre, FILTER_WITH_URL);
  }
});

tabWithoutUrl.addEventListener("click", (event) => {
  event.preventDefault();
  if (currentGenre) {
    navigateToFilter(currentGenre, FILTER_WITHOUT_URL);
  }
});

window.addEventListener("popstate", async (event) => {
  const parsed = event.state ?? parsePath(window.location.pathname);
  const { view, genre: urlSlug, filter } = parsed;

  if (view === "settings") {
    showSettingsView();
    loadSettings();
    return;
  }

  if (view === "statistics") {
    showStatisticsView();
    loadStatistics();
    return;
  }

  if (view === "fetch") {
    showFetchView();
    return;
  }

  if (view === "sync") {
    showSyncView();
    return;
  }

  if (view === "download") {
    showDownloadView();
    return;
  }

  if (view === "start") {
    showStartView();
    return;
  }

  if (view === "home") {
    showGenreView();
    loadGenres();
    return;
  }

  try {
    await ensureKnownGenres();
  } catch (error) {
    showStatus(error.message, "error");
    return;
  }

  const genre = resolveGenreSlug(urlSlug);
  if (genre && filter) {
    showTracksView(genre, filter);
    loadTracks(genre);
  } else if (genre) {
    showGenreHub(genre);
    loadGenreHub(genre);
  } else {
    showGenreView();
    loadGenres();
  }
});

document.getElementById("add-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button");
  const trackInput = form.querySelector('input[name="track"]');
  const urlInput = form.querySelector('input[name="reference_url"]');
  button.disabled = true;

  try {
    const payload = {
      track: trackInput.value.trim(),
      reference_url: urlInput.value.trim(),
    };
    if (currentGenre && currentGenre !== "Uncategorized") {
      payload.genre = currentGenre;
    }

    const response = await fetch("/api/tracks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Could not add track");
    }

    appendTrackItem(data);
    form.reset();
    showStatus(data.reference_url ? "Track added to Has URL list" : "Track added to Needs URL list");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    button.disabled = false;
    trackInput.focus();
  }
});
