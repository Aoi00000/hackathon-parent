# 追加実装メモ

## ローカルDB差分反映
既存DBに対しては以下を1回実行してください。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  mysql -uhackathon_user -phackathon_password hackathon \
  < hackathon-backend/migrations/003_add_advanced_marketplace.sql
```

既存データを消してよい場合は、ボリュームを消してから `001_init.sql` を実行してください。

## AI設定
AI Studio APIキー方式で HTTP 429 RESOURCE_EXHAUSTED / prepayment credits depleted が出る場合、コードの問題ではなく、AI Studio側の利用枠またはプリペイド残高不足です。
研修資料に合わせてVertex AIを使う場合は `.env` を以下のように変更してください。

```env
AI_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
VERTEX_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-1.5-flash-002
```

ローカルでは以下も必要です。

```bash
gcloud auth application-default login
```

その後、バックエンドを再起動してください。
