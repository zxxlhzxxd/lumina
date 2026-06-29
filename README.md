# Lumina

Offline-first worship PowerPoint generation for churches.

[中文说明](README.zh-CN.md)

Lumina helps worship service teams turn recurring Sunday service structures into consistent, ready-to-present PowerPoint decks. It combines reusable service templates, local Bible and hymn/liturgy libraries, media attachments, and a PPTX export engine so weekly slide preparation can move from repetitive manual layout work to focused content editing.

## What Lumina Does

- Create worship projects from reusable service templates.
- Generate responsive readings and sermon scripture slides from Bible references.
- Manage hymn and liturgy libraries, including built-in and user-created entries.
- Edit service sections such as covers, scripture, hymns, liturgy text, announcements, and media pages.
- Customize section-level style: background color/image, typography, alignment, margins, and responsive-reading labels.
- Attach project media, including images and audio.
- Export standard `.pptx` files with embedded media.
- Add editable PowerPoint audio objects with click-to-play or auto-play behavior.
- Store projects and templates locally in portable container files.

Lumina is designed as a local desktop application. There is no account system, cloud sync, or online collaboration requirement.

## Architecture

Lumina is split into a local backend service and an Electron desktop frontend:

```text
lumina/
  backend/    Python FastAPI service, domain models, stores, and PPTX generation
  frontend/   Electron + React + TypeScript desktop UI
```

The Electron main process starts the backend as a local subprocess, reads the selected loopback port from stdout, and passes the API base URL to the renderer through IPC. The backend only binds to `127.0.0.1` by default.

## Requirements

- Python 3.11+
- Node.js 22 is recommended for the frontend
- npm
- PowerPoint, Keynote, WPS, or another PPTX-compatible application for presenting exported files

## Getting Started

### 1. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Import the local Bible database:

```bash
python -m app.data.import_bible
```

This creates `backend/app/data/bible.sqlite`. The SQLite database is generated local data and should not be committed.

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Start the Desktop App

From `frontend/`:

```bash
npm run dev
```

This starts Vite and Electron together. Electron starts the Python backend automatically from `backend/`.

## Running Services Separately

For backend-only development:

```bash
cd backend
source .venv/bin/activate
python -m app.main
```

The backend prints the selected port as:

```text
LUMINA_PORT=<port>
```

Useful environment variables:

- `LUMINA_HOST`: backend host, defaults to `127.0.0.1`
- `LUMINA_PORT`: backend port, defaults to `0` for an OS-selected free port
- `LUMINA_DATA_DIR`: local user data directory, defaults to `~/.lumina`
- `LUMINA_BIBLE_DB`: override path for `bible.sqlite`
- `LUMINA_LIBRARY_DB`: override path for the hymn/liturgy library database

For frontend renderer development without Electron:

```bash
cd frontend
npm run dev:vite
```

## Build

Frontend production build:

```bash
cd frontend
npm run build
```

`npm run build` runs TypeScript checking with `tsc --noEmit` and then builds the Vite renderer bundle.

Backend executable build:

```bash
cd backend
python -m pip install -r requirements-build.txt
python -m app.data.import_bible
python -m PyInstaller --noconfirm --clean lumina-backend.spec
```

Electron installers expect the backend build at `backend/dist/lumina-backend`.

macOS arm64 installer:

```bash
cd frontend
npm run dist:mac
```

Windows x64 installer:

```bash
cd frontend
npm run dist:win
```

GitHub releases are created by pushing a version tag:

```bash
git tag v0.0.1
git push origin v0.0.1
```

The release workflow builds macOS arm64 and Windows x64 installers, uploads them to a draft GitHub Release, and GitHub automatically provides source-code archives for the tag. macOS and Windows signing is optional: configure repository Actions secrets before pushing a tag to enable signing.

macOS signing/notarization secrets:

- `APPLE_CERTIFICATE_BASE64`
- `APPLE_CERTIFICATE_PASSWORD`
- `APPLE_ID`
- `APPLE_APP_SPECIFIC_PASSWORD`
- `APPLE_TEAM_ID`

Windows signing secrets:

- `WIN_CSC_LINK`
- `WIN_CSC_KEY_PASSWORD`

## Tests

Backend tests:

```bash
cd backend
pytest
```

Frontend verification:

```bash
cd frontend
npm run build
```

There is currently no dedicated frontend test runner.

## Debugging

### Backend

- Run `python -m app.main` directly to see FastAPI and startup logs.
- Set `LUMINA_PORT=8000` when you want a stable local API URL.
- Inspect generated user data under `~/.lumina` unless `LUMINA_DATA_DIR` is overridden.
- Exported default PPTX files are written under `~/.lumina/exports` when no explicit path is provided.

Example:

```bash
cd backend
source .venv/bin/activate
LUMINA_PORT=8000 python -m app.main
```

### Electron and Renderer

- `npm run dev` prints backend subprocess output with a `[backend]` prefix.
- In development mode, the renderer runs at `http://127.0.0.1:5173`.
- Use the Electron developer tools for renderer errors and network/API inspection.
- If backend startup fails, verify that `backend/.venv` exists and dependencies are installed.

### PPTX Export

- PPTX generation lives in `backend/app/pptx/`.
- Media files are copied into each project working directory under `media/`.
- Audio export uses embedded PowerPoint media parts and OOXML timing so exported audio can be selected and edited in PowerPoint.

## Data and Storage

Runtime user data defaults to:

```text
~/.lumina/
  projects/
  templates/
  exports/
  library.db
```

Project and template containers bundle referenced media so they can be moved between machines.

## Documentation

- [Requirements](REQUIREMENTS.md)
- [中文说明](README.zh-CN.md)

## License

See [LICENSE](LICENSE).
