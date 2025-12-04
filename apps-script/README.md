# Google Apps Script Code

This folder contains source code for Google Apps Script projects.

## Purpose

This is a lab for experimenting with Google Apps Script automation, focused on integrating Google Workspace services (Sheets, Drive, Gmail, etc.) with custom workflows.

## Folder Structure

- **`sheets/`** — Scripts for working with Google Sheets (reading, writing, formatting, etc.)
- **`gmail/`** — (Future) Scripts for Gmail automation (filtering, auto-replies, etc.)
- **`drive/`** — (Future) Scripts for Google Drive operations (organizing files, cleanup, etc.)
- **`utils/`** — (Future) Shared helper functions and utilities

## Workflow

1. **Edit in GitHub**: Maintain your `.gs` files in this repository for version control.
2. **Copy into script.google.com**: Open the [Apps Script editor](https://script.google.com) and create a new project or open an existing one.
3. **Paste the code**: Copy the content of your `.gs` files and paste it into the editor.
4. **Run and test**: Execute functions from the editor's toolbar, check logs via `View > Logs` or `Ctrl+Enter`.
5. **Configure triggers**: Set up time-based or event-based triggers as needed via `Triggers` in the left sidebar.

## Tips

- Each `.gs` file can contain multiple functions.
- Use `Logger.log()` for debugging output visible in the Apps Script editor.
- For production scripts, consider setting up error notifications and proper permissions.
- Store sensitive IDs (spreadsheet IDs, folder IDs, etc.) as script properties instead of hardcoding them.

## Getting Started

Check out the examples in `sheets/` to see simple patterns for common operations.
