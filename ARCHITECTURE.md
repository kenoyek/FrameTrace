# Architecture

```mermaid
flowchart LR
  Mobile[Expo native client] -->|confirmed multipart upload| API[FastAPI]
  API -->|private temporary clip| Volume[Local private volume]
  API -->|job metadata| DB[(PostgreSQL)]
  API -->|job ID only| Redis[Redis queue]
  Redis --> Worker[Celery worker]
  Worker --> Volume
  Worker --> FFmpeg[FFprobe / FFmpeg bounded decoding]
  FFmpeg --> Hash[Timestamped dHash samples]
  Hash --> Verify[Constant-offset temporal verification]
  DB --> Verify
  Verify --> DB
  Mobile -->|bearer job capability + polling| API
```

Current services implement a small controlled reference catalog, not source discovery
across the internet. Client uploads are never reference catalog entries. Operators ingest
rights-cleared media through a local CLI. The data model records provenance without claiming
that a supplied publisher is a verified creator or rights holder.

The API process and worker are separate in Compose. SQLite plus FastAPI BackgroundTasks
is an explicit development fallback. Retained artifacts: dependencies, database, catalog
fingerprints. Processes to restart: database, queue, API and worker. No process-survival assumption.

Future boundaries: R2 StorageProvider replacing the volume; Supabase JWT authentication
and per-user RLS; audio/transcript/OCR/embedding evidence retrieval; pgvector candidate
search; isolated decoder containers. See providers.py for typed future model boundaries.
No provider silently returns invented evidence when unconfigured.
