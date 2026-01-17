# PDF2MD - Project Specification

## Overview

DoclingでPDFをMarkdownに変換するWebアプリケーション。

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Frontend | Vanilla HTML/CSS/JS + marked.js |
| Storage | Local filesystem |
| Cache | SQLite |
| Task Queue | FastAPI BackgroundTasks |
| PDF Parser | Docling + pypdf |
| Package Manager | uv |

## Features

### PDF Upload (`/`)

- ドラッグ&ドロップまたはファイル選択に対応
- アップロード後、自動的にMarkdownへの変換を開始
- 変換完了後、表示ページ(`/view/{task_id}`)にリダイレクト

### Conversion

- PDFは常にMarkdownに変換される（フォーマット選択なし）
- 変換は非同期（バックグラウンド）で実行
- Doclingの画像抽出機能を有効化し、PDF内の画像も処理
- GPU無効（CPU強制）- CUDA互換性の問題のため

### Result Display (`/view/{task_id}`)

- 変換完了後、Markdownをブラウザ内でレンダリング表示（marked.js使用）
- 直接URLアクセス可能（ブックマーク・共有対応）
- フローティングボタン:
  - ダークモードトグル
  - Markdownダウンロード（zipファイル）

### Caching

- 変換結果はPDFのメタデータから取得したタイトルをキーとしてキャッシュ
- 同一タイトルのPDFが来た場合、キャッシュから結果を返却（変換をスキップ）
- pypdfでPDFメタデータからタイトルを高速に取得

### Storage

- 変換後のMarkdownと画像はローカルファイルシステムで管理
- 画像を含むため、単一ファイルではなくディレクトリ構造で保存

```
storage/output/
└── {task_id}/
    ├── output.md
    └── output_artifacts/
        └── image_xxx.png
```

## Pages

| Path | Description |
|------|-------------|
| `/` | アップロードページ |
| `/view/{task_id}` | ドキュメント表示ページ |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/convert` | PDF変換タスク開始（キャッシュヒット時は即座に返却） |
| GET | `/api/status/{task_id}` | タスク状態確認 |
| GET | `/api/markdown/{task_id}` | Markdownコンテンツ取得 |
| GET | `/api/download/{task_id}` | Markdown+画像のzipダウンロード |
| GET | `/api/images/{task_id}/{filename}` | 画像配信 |

## Running the Application

```bash
# Install dependencies
uv sync

# Start development server
uv run uvicorn app.main:app --reload

# Access at http://localhost:8000
```
