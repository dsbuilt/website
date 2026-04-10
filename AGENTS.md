# AGENTS.md

This file provides repository-wide guidance for AI coding agents and contributors.

## Repository overview
- This is a static website project.
- Primary entry point: `index.html`.
- Client-side behavior lives in `js/main.js`.
- Images are stored under `images/`.
- Image optimization helper script: `scripts/optimize-project-images.sh`.

## Working conventions
- Keep changes focused and minimal for the requested task.
- Prefer small, readable vanilla HTML/CSS/JS updates over adding new dependencies.
- Preserve existing file/folder structure and naming conventions.
- Do not bulk-reformat unrelated files.

## Validation checklist
After making changes, run the checks that are relevant:
1. Open `index.html` in a browser (or static server) and verify there are no obvious console errors.
2. If JavaScript was changed, quickly smoke-test key interactions.
3. If images were added/updated, ensure paths resolve correctly and file sizes are reasonable.

## Commit guidance
- Use clear commit messages that describe user-visible impact.
- Include only files related to the task in each commit.

## Safety notes
- Never commit secrets, API keys, or credentials.
- Avoid destructive commands unless explicitly requested.
