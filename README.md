# Short Jack's Release Finder

Spotify playlist sync tool with a terminal menu, MySQL or text-file storage, and optional YouTube-to-AIFF downloads.

This guide walks through setup on a **fresh MacBook** (no developer tools pre-installed).

---

## What you need

| Component | Required for | Install via |
|-----------|--------------|-------------|
| **Homebrew** | Easy installs on macOS | [brew.sh](https://brew.sh) |
| **Python 3.10+** | Main app | `brew install python` |
| **MySQL 8** | Database (MySQL mode only) | `brew install mysql` |
| **Git** | Clone the repo (optional) | `brew install git` |
| **ffmpeg** | YouTube → AIFF downloads (menu option 9) | `brew install ffmpeg` |
| **Node.js** | Reliable YouTube downloads with yt-dlp | `brew install node` |
| **PHP 8+** | PHP web UI only (optional alternative to Flask) | `brew install php` |

Python packages (installed with `pip`):

- `spotipy` — Spotify API
- `pymysql` — MySQL (only when `STORAGE_BACKEND=mysql`)
- `tqdm` — progress bars
- `flask` — new-tracks web UI
- `mutagen` — WAV/AIFF metadata tagging
- `yt-dlp` — YouTube downloads
- `numbers-parser` — import from Apple Numbers (optional)

---

## 1. Install Homebrew and system tools

Open **Terminal** and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions (Homebrew may ask you to add it to your `PATH`).

Then install the tools:

```bash
brew install python mysql git ffmpeg node
```

Start MySQL and enable it on login:

```bash
brew services start mysql
```

Verify:

```bash
python3 --version   # should be 3.10 or higher
mysql --version
ffmpeg -version
node --version
```

---

## 2. Get the project

Clone or copy the project folder to your Mac, then go into it:

```bash
cd /path/to/spotify-playground
```

---

## Storage: MySQL or text file

The app supports two storage backends, selected with `STORAGE_BACKEND` in `.env`:

| Mode | Value | Requires MySQL? |
|------|-------|-----------------|
| **MySQL** (default) | `STORAGE_BACKEND=mysql` | Yes |
| **Text file** | `STORAGE_BACKEND=txt` | No |

### MySQL (default)

Follow step 3 below to create the database.

### Text file (simpler setup)

No MySQL needed. All data is stored in a single JSON text file (default: `data/store.txt`).

```bash
cp .env.example .env
# Edit .env and set:
# STORAGE_BACKEND=txt

mkdir -p data
cp data/store.txt.example data/store.txt
```

Optional: set a custom path with `STORAGE_FILE=/path/to/your/store.txt`.

The Flask new-tracks web UI (`run_new_tracks_todo.py`) works with text-file storage. The PHP web UI still requires MySQL.

---

## 3. Set up the database (MySQL mode only)

Skip this step if you use `STORAGE_BACKEND=txt`.

Create the database and load the schema:

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS spotify_playground CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root spotify_playground < schema.sql
```

If your MySQL `root` user has a password, add `-p` to both commands.

---

## 4. Configure environment variables

Copy the example env file and edit it if needed:

```bash
cp .env.example .env
```

Default values for MySQL mode:

```
STORAGE_BACKEND=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=spotify_playground
```

For text-file mode, only this is needed:

```
STORAGE_BACKEND=txt
```

**Important:** Python scripts read these from your shell environment. The `./run_sync.sh` script loads `.env` automatically. For manual runs:

```bash
set -a
source .env
set +a
```

You can add those three lines to your `~/.zshrc` if you always work from this project, or run them each time you open a new Terminal tab.

The PHP web UI loads `.env` automatically.

---

## 5. Create a Python virtual environment

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

You should see `(.venv)` at the start of your prompt when the virtual environment is active.

---

## 6. Configure Spotify API credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app (or use an existing one)
3. Open **Settings** and add this **Redirect URI**:

   ```
   http://127.0.0.1:8888/
   ```

4. Copy your **Client ID** and **Client Secret**
5. Edit `spotify_playlist/config.py` and replace:

   ```python
   CLIENT_ID = 'your-client-id'
   CLIENT_SECRET = 'your-client-secret'
   REDIRECT_URI = 'http://127.0.0.1:8888/'
   ```

Optional settings in the same file:

- `YOUTUBE_DOWNLOAD_DIR` — folder for AIFF downloads (menu option 9)
- `WAV_METADATA_DIR` — folder with WAV/AIFF files for metadata tagging (menu option 8)
- `CHECK_ARTIST_RELEASES` — sync new releases from followed artists

---

## 7. Run the app

Load env vars (if not already in your shell), activate the venv, then start:

```bash
set -a && source .env && set +a
source .venv/bin/activate
./run_sync.sh
```

Or without the shell script:

```bash
python3 playlist_sync.py
```

On first run, your browser opens for Spotify login. After that, credentials are cached in `.spotipy_cache`.

### Other commands

| Command | Purpose |
|---------|---------|
| `./run_sync.sh` | Interactive menu (recommended) |
| Menu option **10** | Install Python packages and optional system tools (ffmpeg, Node, MySQL) |
| `python3 playlist_sync.py --export` | Export new tracks with saved settings |
| `python3 run_new_tracks_todo.py` | Web UI for managing new tracks (Flask, port 5050) |
| `python3 import_new_numbers.py` | Import tracks from `new.numbers` (Apple Numbers) |

### PHP web UI (optional)

If you prefer PHP over Flask for the new-tracks UI:

```bash
brew install php   # if not installed yet
php -S 127.0.0.1:8080 -t public
```

Open http://127.0.0.1:8080/

---

## 8. Optional: YouTube downloads

For menu option **9 — Download YouTube naar AIFF** you need:

- `ffmpeg` (installed above)
- `node` (recommended; yt-dlp uses it for YouTube extraction)
- `yt-dlp` (installed via `requirements.txt`)

Create a URL list if you want batch downloads from a file:

```bash
cp youtube_urls.txt.example youtube_urls.txt
# edit youtube_urls.txt — one URL per line
```

Set `YOUTUBE_DOWNLOAD_DIR` in `spotify_playlist/config.py` to your preferred download folder.

---

## Troubleshooting

### "Virtual environment not found"

Create it (step 4):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### "spotipy / pymysql / mutagen not found"

Activate the venv and reinstall:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Kan geen verbinding maken met de database"

- Check MySQL is running: `brew services list`
- Start it: `brew services start mysql`
- Verify `.env` values and that you ran `source .env` before Python
- Test: `mysql -u root spotify_playground -e "SHOW TABLES;"`

### "Invalid redirect URI" (Spotify)

The redirect URI in `config.py` must **exactly** match one listed in your Spotify app settings, including the trailing slash:

```
http://127.0.0.1:8888/
```

### Port 8888 already in use

Either close the app using that port, or change `REDIRECT_URI` in `config.py` (e.g. to `http://127.0.0.1:8889/`) and update Spotify Dashboard to match.

### "ffmpeg is niet geïnstalleerd"

```bash
brew install ffmpeg
```

### YouTube download fails

Install Node.js for more reliable extraction:

```bash
brew install node
```

---

## Quick setup checklist

- [ ] Homebrew, Python, MySQL, ffmpeg, Node installed
- [ ] Storage mode chosen (`mysql` or `txt`)
- [ ] MySQL running and schema imported *(MySQL mode only)*
- [ ] `data/store.txt` created *(text-file mode only)*
- [ ] `.env` copied and configured
- [ ] `.venv` created; `pip install -r requirements.txt` done
- [ ] Spotify Client ID/Secret and redirect URI set in `config.py`
- [ ] `source .env` before running Python
- [ ] `./run_sync.sh` starts and Spotify login works
