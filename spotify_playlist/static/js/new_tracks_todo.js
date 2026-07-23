const genreView = document.getElementById("genre-view");
const genreHubView = document.getElementById("genre-hub-view");
const tracksView = document.getElementById("tracks-view");
const genreGrid = document.getElementById("genre-grid");
const filterGrid = document.getElementById("filter-grid");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");
const pageCover = document.getElementById("page-cover");
const backLink = document.getElementById("back-link");
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
let statusTimer = null;
let copyToastTimer = null;
let lastHighlightedName = null;
let currentGenre = null;
let currentFilter = null;
let cachedTracks = { with_url: [], without_url: [] };
let knownGenres = [];
let genreImageBySlug = {};

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
  const base = `/${toUrlSlug(slug)}`;
  if (filter === FILTER_WITH_URL) return `${base}/${FILTER_WITH_URL}`;
  if (filter === FILTER_WITHOUT_URL) return `${base}/${FILTER_WITHOUT_URL}`;
  return base;
}

function parsePath(pathname) {
  const path = pathname.replace(/\/+$/, "") || "/";
  if (path === "/") {
    return { genre: null, filter: null };
  }

  const segments = path.slice(1).split("/").map((segment) => decodeURIComponent(segment.replace(/\+/g, " ")));
  const last = segments[segments.length - 1];

  if (last === FILTER_WITH_URL || last === FILTER_WITHOUT_URL) {
    const genre = segments.slice(0, -1).join("/");
    return { genre: genre || null, filter: last };
  }

  return { genre: segments.join("/"), filter: null };
}

async function ensureKnownGenres() {
  if (knownGenres.length) return;
  const response = await fetch("/api/genres");
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Could not load genres");
  }
  knownGenres = (data.genres || []).map((genre) => genre.slug);
}

function normalizeRoutePath(genre, filter = null) {
  const canonicalPath = genrePath(genre, filter);
  if (window.location.pathname !== canonicalPath) {
    history.replaceState({ genre, filter }, "", canonicalPath);
  }
}

function showGenreView() {
  currentGenre = null;
  currentFilter = null;
  document.title = "New Tracks To-Do";
  pageTitle.textContent = "New Tracks To-Do";
  pageSubtitle.textContent = "Choose a genre to manage reference URLs for its tracks.";
  setPageCover(null);
  backLink.hidden = true;
  backLink.textContent = "← All genres";
  backLink.href = "/";
  genreView.hidden = false;
  genreHubView.hidden = true;
  tracksView.hidden = true;
}

function showGenreHub(genre) {
  currentGenre = genre;
  currentFilter = null;
  document.title = `${genre} — New Tracks To-Do`;
  pageTitle.textContent = genre;
  pageSubtitle.textContent = "Choose whether to view tracks with or without a reference URL.";
  setPageCover(genreImageBySlug[genre] || null);
  backLink.hidden = false;
  backLink.textContent = "← All genres";
  backLink.href = "/";
  genreView.hidden = true;
  genreHubView.hidden = false;
  tracksView.hidden = true;
}

function showTracksView(genre, filter) {
  currentGenre = genre;
  currentFilter = filter;
  const filterLabel = filter === FILTER_WITH_URL
    ? "tracks with a reference URL"
    : "tracks still missing a reference URL";
  document.title = `${genre} — New Tracks To-Do`;
  pageTitle.textContent = genre;
  pageSubtitle.textContent = `Showing ${filterLabel}.`;
  setPageCover(genreImageBySlug[genre] || null);
  backLink.hidden = false;
  backLink.textContent = "← Back to lists";
  backLink.href = genrePath(genre);
  genreView.hidden = true;
  genreHubView.hidden = true;
  tracksView.hidden = false;
  applyFilterView();
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

function navigateHome({ replace = false } = {}) {
  const state = { genre: null, filter: null };
  if (replace) {
    history.replaceState(state, "", "/");
  } else {
    history.pushState(state, "", "/");
  }
  showGenreView();
  loadGenres();
}

function navigateToGenreHub({ replace = false } = {}) {
  if (!currentGenre) {
    navigateHome({ replace });
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
      label: "Has reference URL",
      count: withUrlCount,
      className: "filter-card--done",
    },
    {
      filter: FILTER_WITHOUT_URL,
      label: "Needs reference URL",
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
        <span class="filter-card__count">${choice.count} track${choice.count === 1 ? "" : "s"}</span>
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
  setBanner("Loading track counts…", "loading");
  try {
    const response = await fetch(`/api/tracks?genre=${encodeURIComponent(genre)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Could not load tracks");
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
      setBanner(`No tracks found for ${genre}.`, "error");
    } else {
      setBanner("");
    }
  } catch (error) {
    setBanner(`Failed to load tracks: ${error.message}`, "error");
    showStatus(error.message, "error");
  }
}

function renderGenreList(genres) {
  genreGrid.innerHTML = "";
  genreImageBySlug = {};
  if (!genres.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "No genres found.";
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
        <span class="genre-card__count">${genre.track_count} track${genre.track_count === 1 ? "" : "s"}</span>
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
  setBanner("Loading genres…", "loading");
  try {
    const response = await fetch("/api/genres");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Could not load genres");
    }

    renderGenreList(data.genres || []);
    knownGenres = (data.genres || []).map((genre) => genre.slug);
    if (!data.total) {
      setBanner("No tracks found in new_tracks table.", "error");
    } else {
      setBanner("");
    }
  } catch (error) {
    setBanner(`Failed to load genres: ${error.message}`, "error");
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
      throw new Error(data.error || "Could not record click");
    }

    setCopyTitleCount(nameEl, Number(data.copy_title_count || optimistic));
  } catch (error) {
    setCopyTitleCount(nameEl, previous);
    showStatus(error.message || "Could not save click count", "error");
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

  const colors = ["#39ff14", "#00f5ff", "#ff2bd6", "#ffe600", "#a855ff", "#ffffff"];
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
    showCopyToast(`Nothing to copy`);
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    showCopyToast(`${label} copied`);
  } catch (error) {
    showCopyToast(`Could not copy ${label.toLowerCase()}`);
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
    ? `<div class="track-energy">Energy: ${Number(track.energy).toFixed(2)}</div>`
    : "";

  li.innerHTML = `
    <div class="track-main">
      ${artMarkup(track.image_url, "track-art", track.track)}
      <div class="track-body">
        <div class="track-heading">
          <div class="track-name" data-count="${copyTitleCount}" role="button" tabindex="0" title="Click to copy title">${escapeHtml(track.track)}</div>
          ${genreHtml}
          ${energyHtml}
        </div>
        <form class="track-form">
          <input type="url" name="reference_url" placeholder="https://..." value="${safeUrl}" />
          <button type="submit">Save</button>
          <button type="button" class="remove">Remove</button>
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
    copyText(track.track, "Title");
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
        throw new Error(err.error || "Save failed");
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
      showStatus(updated.has_url ? "Saved — moved to Has URL list" : "Cleared — moved to Needs URL list");
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
  const ok = window.confirm(`Remove "${track.track}" from the list?`);
  if (!ok) return;

  try {
    const response = await fetch(`/api/tracks/${track.id}`, { method: "DELETE" });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || "Remove failed");
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
    showStatus("Track removed");
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
      ? "No tracks with a URL yet."
      : "All tracks have a reference URL.";
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
  setBanner("Loading tracks from database…", "loading");
  try {
    const query = genre ? `?genre=${encodeURIComponent(genre)}` : "";
    const response = await fetch(`/api/tracks${query}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Could not load tracks");
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
      setBanner(`No tracks found for ${genre}.`, "error");
    } else {
      setBanner("");
    }
  } catch (error) {
    setBanner(`Failed to load tracks: ${error.message}`, "error");
    showStatus(error.message, "error");
  }
}

async function bootFromPath() {
  const { genre: urlSlug, filter } = parsePath(window.location.pathname);
  if (!urlSlug) {
    showGenreView();
    loadGenres();
    return;
  }

  try {
    await ensureKnownGenres();
  } catch (error) {
    showGenreView();
    setBanner(`Failed to load genres: ${error.message}`, "error");
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

backLink.addEventListener("click", (event) => {
  event.preventDefault();
  if (currentFilter) {
    navigateToGenreHub();
  } else if (currentGenre) {
    navigateHome();
  } else {
    navigateHome();
  }
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
  const { genre: urlSlug, filter } = parsed;

  if (!urlSlug) {
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
    const response = await fetch("/api/tracks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        track: trackInput.value.trim(),
        reference_url: urlInput.value.trim(),
      }),
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
