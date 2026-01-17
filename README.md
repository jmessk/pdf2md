# PDF2MD

A web application that converts PDFs to Markdown. It uses [Docling](https://github.com/docling-project/docling) to handle documents with complex layouts such as academic papers.

## Features

- **Image extraction** - Automatically extracts and saves figures and images contained in PDFs.
- **Caching** - Skips re-conversion for the same PDF (title/hash-based).
- **Dark mode** - Toggle for an eye-friendly display.
- **Download** - Download the Markdown and images as a zip file.
- **Direct URL sharing** - Conversion results are accessible via a URL that can be bookmarked or shared.

## Getting Started

```bash
docker compose up
```

## Usage

1. Go to app URL (default: `http://localhost:8000`)
2. Drag & drop a PDF file or select one via the file picker
3. Click "Start Conversion"
4. After conversion completes, you will be redirected automatically to the viewer page

## API

| Method | Endpoint                           | Description             |
| ------ | ---------------------------------- | ----------------------- |
| POST   | `/api/convert`                     | Start PDF conversion    |
| GET    | `/api/status/{task_id}`            | Check conversion status |
| GET    | `/api/markdown/{task_id}`          | Retrieve the Markdown   |
| GET    | `/api/download/{task_id}`          | Download zip archive    |
| GET    | `/api/images/{task_id}/{filename}` | Serve extracted images  |
