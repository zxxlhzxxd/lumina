# Repository Guidelines

## Project Structure & Module Organization

Lumina is an offline-first worship PowerPoint generator with a Python backend and an Electron React frontend.

- `backend/app/` contains the FastAPI app, domain models, services, seed data, and PPTX generation code.
- `backend/app/api/v1/` holds versioned API routers.
- `backend/app/domain/` defines Pydantic models and enums shared by services.
- `backend/app/services/` contains persistence, generation, styling, and library logic.
- `backend/tests/` contains pytest tests for parser, generation, container, styling, and store behavior.
- `frontend/src/` contains the React + TypeScript renderer, components, API client, styles, and preview layout logic.
- `frontend/electron/` contains Electron main/preload process code.

## Development Approach & Architecture

Treat every change as part of a maintainable product rather than a one-off implementation. Before coding, identify responsibilities, stable boundaries, likely variation points, and how the change fits the existing architecture.

- Decompose features into cohesive modules with clear interfaces and a single primary responsibility.
- Keep domain logic independent from transport, UI, persistence, and framework details. Prefer dependency injection and dependency inversion where they make components easier to replace or test.
- Reuse and extend existing services, domain models, components, and utilities instead of duplicating behavior or embedding feature-specific shortcuts.
- Apply suitable design patterns when they clarify ownership, isolate changing behavior, or provide explicit extension points. Favor composition over inheritance and avoid abstractions that merely add indirection without defining a meaningful boundary.
- Design APIs and data models with future variants and integrations in mind. Avoid hard-coded branches, tightly coupled modules, hidden side effects, and assumptions that make the next iteration require a rewrite.
- Separate policy from mechanism: configurable business rules and presentation choices should not be buried in low-level implementation code.
- Keep modules independently testable and add focused coverage around contracts, extension points, and failure cases.
- Do not write disposable code solely to make the current case pass. If a short-term compromise is unavoidable, isolate it, document the constraint, and leave a clear migration path.

## Build, Test, and Development Commands

Backend setup and local run:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.data.import_bible
python -m app.main
```

`python -m app.data.import_bible` creates local `backend/app/data/bible.sqlite`; do not commit generated SQLite data. Use `LUMINA_PORT` and `LUMINA_HOST` to pin the dev server if needed.

Frontend setup and local run:

```bash
cd frontend
npm install
npm run dev
npm run build
```

`npm run dev` starts Vite and Electron together. `npm run build` runs TypeScript checking with `tsc --noEmit` and builds the renderer.

## Coding Style & Naming Conventions

Python uses 4-space indentation, type hints, Pydantic models, and snake_case for modules, functions, and fields. Keep backend business logic in services rather than API handlers.

TypeScript uses strict mode, React function components, PascalCase component files such as `SectionEditor.tsx`, and camelCase helpers such as `styleResolve.ts`. Prefer existing Ant Design components and icons.

No repository-wide formatter is configured, so preserve the surrounding style and keep comments sparse and useful.

## Testing Guidelines

Run backend tests with:

```bash
cd backend
pytest
```

Name tests `test_*.py` and keep fixtures in `backend/tests/conftest.py`. Add focused tests for changes to parsing, generation, project/template containers, style resolution, and library stores. The frontend currently has no test runner; use `npm run build` as the minimum verification for TypeScript changes.

## Commit & Pull Request Guidelines

History follows Conventional Commit-style subjects, for example `feat: add project list page` and `fix: make style edits visible`. Use concise `feat:`, `fix:`, `test:`, or `docs:` prefixes.

Pull requests should describe the user-facing change, list verification commands run, link related issues or requirements, and include screenshots or short recordings for UI changes.
