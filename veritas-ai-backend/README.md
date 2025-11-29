# Veritas AI Backend

FastAPI backend for misinformation verification demo project.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

Make sure PostgreSQL is running and create a database:

```sql
CREATE DATABASE veritas_ai;
```

Update the `POSTGRES_URL` in `config.py` or set it as an environment variable:

```bash
export POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/veritas_ai"
```

### 3. Initialize Database

The database tables will be automatically created on first run. Alternatively, you can use Alembic for migrations:

```bash
alembic init db/migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Endpoints

### Verification Endpoints

- `POST /api/v1/verify/text` - Verify plain text
- `POST /api/v1/verify/image` - Verify image file
- `POST /api/v1/verify/video` - Verify video file
- `POST /api/v1/verify/article` - Verify article (URL or HTML)

### Results Endpoints

- `GET /api/v1/result/{verification_id}` - Get verification results

### Streaming Endpoints

- `GET /api/v1/stream/{verification_id}` - Stream verification progress via SSE

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── models/               # SQLAlchemy database models
│   ├── verification.py
│   └── claim.py
├── routers/              # API route handlers
│   ├── verify.py
│   ├── results.py
│   └── stream.py
├── services/             # Business logic services
│   ├── database.py
│   ├── storage.py
│   └── pipeline.py
├── storage/              # Local file storage
│   └── verifications/   # Verification data storage
└── db/                   # Database migrations
    └── migrations/
```

## Storage

All verification inputs and outputs are stored locally in `storage/verifications/{verification_id}/`:

- `input/` - Original input files
- `outputs/text_analysis.json` - Text analysis results (if text analysis performed)
- `outputs/image_analysis.json` - Image analysis results (if image analysis performed)
- `outputs/video_analysis.json` - Video analysis results (if video analysis performed)
- `outputs/fusion_results.json` - Cross-modal fusion results (when fusion completes)
- `outputs/results.json` - Legacy results file (for backward compatibility)

## Development

The pipeline is currently a mock implementation that simulates processing stages. Each stage sleeps for 1 second to demonstrate the async flow and SSE streaming.

