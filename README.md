# Short Jack's Release Finder

Spotify playlist sync tool with a terminal menu, MySQL storage, and optional YouTube-to-AIFF downloads.

This guide is written for a **fresh Mac** with nothing installed yet. Follow the steps in order.

---

## Quick start (copy-paste)

After you have the project folder on your Mac, run these commands in **Terminal**:

```bash
# 1. System tools (skip if already installed)
brew install python mysql git ffmpeg node
brew services start mysql

# 2. Go to the project
cd /path/to/spotify-playground

# 3. Database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS spotify_playground CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root spotify_playground < schema.sql

# 4. Environment file
cp .env.example .env

# 5. Python packages (required — do this once)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then edit `spotify_playlist/config.py` with your Spotify credentials (see [Spotify setup](#spotify-setup) below).

Start the app:

```bash
cd /path/to/spotify-playground
source .venv/bin/activate
./run_sync.sh
```

`./run_sync.sh` loads `.env` automatically and uses the virtual environment. You do **not** need to run `pip install` again unless you pull new dependencies.

---

## What you need

### Required (core app)

| Component | Purpose | Install |
|-----------|---------|---------|
| **Homebrew** | Easy macOS installs | [brew.sh](https://brew.sh) |
| **Python 3.10+** | Main app | `brew install python` |
| **MySQL 8** | Database | `brew install mysql` |
| **Python packages** | Spotify, MySQL, UI, etc. | `pip install -r requirements.txt` (inside `.venv`) |

### Optional (only for specific features)

| Component | Purpose | Install |
|-----------|---------|---------|
| **Git** | Clone the repo | `brew install git` |
| **ffmpeg** | Menu option 3 — download YouTube as AIFF | `brew install ffmpeg` |
| **Node.js** | More reliable YouTube downloads | `brew install node` |
| **PHP 8+** | Alternative web UI instead of Flask | `brew install php` |

### Python packages (`requirements.txt`)

All of these are installed with one command: `pip install -r requirements.txt`

| Package | Used for |
|---------|----------|
| `spotipy` | Spotify API |
| `pymysql` | MySQL database |
| `tqdm` | Progress bars |
| `flask` | New-tracks web UI (`run_new_tracks_todo.py`) |
| `mutagen` | WAV/AIFF metadata tagging |
| `Pillow` | Cover art in audio files |
| `yt-dlp` | YouTube downloads (menu option 3) |

---

## Step-by-step setup

### 1. Install Homebrew and system tools

Open **Terminal** and install Homebrew if you do not have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions (Homebrew may ask you to add it to your `PATH`).

Install the tools you need:

```bash
brew install python mysql git ffmpeg node
brew services start mysql
```

Verify:

```bash
python3 --version   # 3.10 or higher
mysql --version
ffmpeg -version     # only needed for YouTube downloads
node --version      # recommended for YouTube downloads
```

### 2. Get the project

Clone or copy the project folder, then go into it:

```bash
cd /path/to/spotify-playground
```

### 3. Set up the database

Create the database and load the schema:

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS spotify_playground CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root spotify_playground < schema.sql
```

If your MySQL `root` user has a password, add `-p` to both commands.

Check that it worked:

```bash
mysql -u root spotify_playground -e "SHOW TABLES;"
```

You should see tables like `new_tracks`, `destination_config`, and `source_playlists`.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Default values (usually fine for local development):

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=spotify_playground
```

**Note:** `./run_sync.sh` loads `.env` for you. If you run Python scripts directly (without the shell script), load env vars first:

```bash
set -a && source .env && set +a
```

The PHP web UI also loads `.env` automatically.

### 5. Install Python packages

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

You should see `(.venv)` at the start of your prompt. Activate the venv in every new Terminal tab before running the app:

```bash
source .venv/bin/activate
```

### Spotify setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app (or use an existing one)
3. Open **Settings** and add this **Redirect URI**:

   ```
   http://127.0.0.1:8888/
   ```

4. Copy your **Client ID** and **Client Secret**
5. Edit `spotify_playlist/config.py` and set:

   ```python
   CLIENT_ID = 'your-client-id'
   CLIENT_SECRET = 'your-client-secret'
   REDIRECT_URI = 'http://127.0.0.1:8888/'
   ```

Optional settings in the same file:

| Setting | Purpose |
|---------|---------|
| `YOUTUBE_DOWNLOAD_DIR` | Folder for AIFF downloads (menu option 3) |
| `WAV_METADATA_DIR` | Folder for Spotify metadata batch tagging |
| `SPOTIFY_COVER_ART_DIR` | Folder for embedding Spotify cover art |
| `YOUTUBE_URLS_FILE` | Text file with YouTube URLs (one per line) |
| `CHECK_ARTIST_RELEASES` | Sync new releases from followed artists |

---

## Run the app

```bash
cd /path/to/spotify-playground
source .venv/bin/activate
./run_sync.sh
```

Or without the shell script:

```bash
set -a && source .env && set +a
source .venv/bin/activate
python3 playlist_sync.py
```

On first run, your browser opens for Spotify login. After that, credentials are cached in `.spotipy_cache`.

### Main menu

| Option | What it does |
|--------|--------------|
| **1** | Sync source playlists into your destination playlist and fetch new artist releases |
| **2** | Import new tracks since a date into the database (includes Spotify energy scores) |
| **3** | Download tracks from the database as AIFF (YouTube URLs; energy written to file metadata) |
| **4** | Configure source, destination, and tracking playlists |
| **0** | Exit |

**Suggested first-time flow:** option **4** (set playlists) → option **1** (sync) → option **2** (import tracks) → option **3** (download AIFF files).

### Other commands

| Command | Purpose |
|---------|---------|
| `./run_sync.sh` | Interactive menu (recommended) |
| `python3 playlist_sync.py --export` | Export new tracks with saved settings |
| `python3 run_new_tracks_todo.py` | Web UI for managing new tracks (Flask, http://127.0.0.1:5050) |

### PHP web UI (optional)

If you prefer PHP over Flask for the new-tracks UI:

```bash
brew install php   # if not installed yet
php -S 127.0.0.1:8080 -t public
```

Open http://127.0.0.1:8080/

---

## YouTube → AIFF downloads (menu option 3)

Requires:

- `ffmpeg` — `brew install ffmpeg`
- `node` — recommended for reliable YouTube extraction
- `yt-dlp` — installed via `requirements.txt`

Set `YOUTUBE_DOWNLOAD_DIR` in `spotify_playlist/config.py` to your download folder.

Tracks downloaded from the app database get **genre**, **release year**, and **energy** (from the database) embedded in the AIFF metadata. Energy comes from Spotify when you import tracks (menu option 2).

For batch downloads from a text file instead of the database:

```bash
cp youtube_urls.txt.example youtube_urls.txt
# edit youtube_urls.txt — one URL per line
```

---

## Troubleshooting

### "Virtual environment not found" or missing Python packages

Create the venv and install everything:

```bash
cd /path/to/spotify-playground
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Always activate the venv before running the app: `source .venv/bin/activate`

### "spotipy / pymysql / mutagen / flask not found"

You are probably not using the virtual environment. Run:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Cannot connect to the database"

- Check MySQL is running: `brew services list`
- Start it: `brew services start mysql`
- Verify `.env` values match your MySQL setup
- Test: `mysql -u root spotify_playground -e "SHOW TABLES;"`

### "Invalid redirect URI" (Spotify)

The redirect URI in `config.py` must **exactly** match one listed in your Spotify app settings, including the trailing slash:

```
http://127.0.0.1:8888/
```

### Port 8888 already in use

Close the app using that port, or change `REDIRECT_URI` in `config.py` (e.g. to `http://127.0.0.1:8889/`) and update the Spotify Dashboard to match.

### "ffmpeg is not installed"

```bash
brew install ffmpeg
```

### YouTube download fails

Install Node.js for more reliable extraction:

```bash
brew install node
```

---

## Setup checklist

- [ ] Homebrew installed
- [ ] Python 3.10+ and MySQL installed; MySQL running
- [ ] Project folder on your Mac
- [ ] Database created and `schema.sql` imported
- [ ] `.env` copied from `.env.example`
- [ ] `.venv` created and `pip install -r requirements.txt` completed
- [ ] Spotify Client ID, Secret, and redirect URI set in `config.py`
- [ ] `./run_sync.sh` starts and Spotify login works
- [ ] *(Optional)* ffmpeg and Node installed for YouTube downloads
