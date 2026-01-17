# PDF2MD

PDFをMarkdownに変換するWebアプリケーション。[Docling](https://github.com/docling-project/docling)を使用して、学術論文などの複雑なレイアウトを持つドキュメントを処理できます。

## Features

- **画像抽出** - PDF内の図表も自動的に抽出・保存
- **キャッシュ機能** - 同一PDFの再変換をスキップ（タイトル/ハッシュベース）
- **ダークモード** - 目に優しい表示切替
- **ダウンロード** - Markdown + 画像をzipでダウンロード
- **直接URL共有** - 変換結果のURLをブックマーク・共有可能

## Quick Start

### Docker (推奨)

```bash
docker compose up
# Open http://localhost:8000
```

### Local

```bash
uv sync
uv run uvicorn app.main:app --reload
# Open http://localhost:8000
```

## Usage

1. `http://localhost:8000` にアクセス
2. PDFファイルをドラッグ&ドロップまたは選択
3. 「変換開始」をクリック
4. 変換完了後、自動的にビューワーページへ遷移

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/convert` | PDF変換を開始 |
| GET | `/api/status/{task_id}` | 変換状態を確認 |
| GET | `/api/markdown/{task_id}` | Markdownを取得 |
| GET | `/api/download/{task_id}` | zipダウンロード |
| GET | `/api/images/{task_id}/{filename}` | 画像を取得 |

## License

MIT
