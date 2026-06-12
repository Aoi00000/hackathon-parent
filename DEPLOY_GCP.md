# GCPデプロイ手順メモ

## 1. 必要APIを有効化

```bash
gcloud services enable run.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```

## 2. Cloud SQLを作成

研修資料ではMySQL 8.0、us-central1、低スペック構成の例が示されています。ハッカソンでは費用を抑えるため、必要最小限の構成にします。

```bash
gcloud sql instances create hackathon-mysql \
  --database-version=MYSQL_8_0 \
  --region=us-central1 \
  --tier=db-f1-micro \
  --storage-size=10GB
```

## 3. DBとユーザーを作成

```bash
gcloud sql connect hackathon-mysql --user=root
```

MySQLコンソールで以下を実行します。

```sql
CREATE DATABASE hackathon CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'hackathon_user' IDENTIFIED BY '任意の強いパスワード';
GRANT ALL ON hackathon.* TO 'hackathon_user';
FLUSH PRIVILEGES;
```

その後、`hackathon-backend/migrations/001_init.sql` を実行します。

## 4. Secret Managerに秘密情報を保存

```bash
echo -n "DBパスワード" | gcloud secrets create MYSQL_PASSWORD --data-file=-
echo -n "長いランダム文字列" | gcloud secrets create JWT_SECRET --data-file=-
echo -n "Gemini APIキー" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

## 5. Cloud Runにバックエンドをデプロイ

```bash
cd hackathon-backend

gcloud run deploy hackathon-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances PROJECT_ID:us-central1:hackathon-mysql \
  --set-env-vars MYSQL_USER=hackathon_user,MYSQL_HOST=/cloudsql/PROJECT_ID:us-central1:hackathon-mysql,MYSQL_DATABASE=hackathon,GEMINI_MODEL=gemini-2.5-flash,FRONTEND_ORIGIN=https://your-frontend-cloud-run-url \
  --set-secrets MYSQL_PASSWORD=MYSQL_PASSWORD:latest,JWT_SECRET=JWT_SECRET:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest
```

`PROJECT_ID` と `FRONTEND_ORIGIN` は自分の値に置き換えてください。

## 6. Cloud Runにフロントエンドをデプロイ

フロントエンドはViteの仕様上、API URLをビルド時に埋め込みます。バックエンドのCloud Run URLが分かった後、以下のようにDocker build時の引数として渡します。

```bash
cd hackathon-frontend

gcloud builds submit \
  --tag gcr.io/PROJECT_ID/hackathon-frontend \
  --substitutions=_VITE_API_BASE_URL=https://your-backend-cloud-run-url
```

上のコマンドだけではDockerfileのbuild-argを渡せない場合があります。その場合は、Cloud Build設定ファイルを追加するか、ローカルで以下のようにビルドしてからpushしてください。

```bash
docker build \
  --build-arg VITE_API_BASE_URL=https://your-backend-cloud-run-url \
  -t gcr.io/PROJECT_ID/hackathon-frontend .

docker push gcr.io/PROJECT_ID/hackathon-frontend
```

その後、Cloud Runへデプロイします。

```bash
gcloud run deploy hackathon-frontend \
  --image gcr.io/PROJECT_ID/hackathon-frontend \
  --region us-central1 \
  --allow-unauthenticated
```

## 7. CORS設定を更新

フロントエンドのCloud Run URLが分かったら、バックエンドの `FRONTEND_ORIGIN` をそのURLに更新し、新しいリビジョンをデプロイします。

## 8. 動作確認

- `GET /healthz` が `{"status":"ok"}` を返すこと
- フロントエンドから新規登録できること
- AI説明生成が返ること
- 商品を出品、一覧表示、購入できること
