# EnterpriseDoc AI – Developer & Operations Guide (v2.4)

## 1. Architecture & System Overview
The EnterpriseDoc AI platform uses a dual-engine Hybrid RAG (Retrieval-Augmented Generation) pipeline:
- **Dense Vector Search**: Powered by Google Gemini `text-embedding-004` (768-dimensional normalized embeddings) indexed inside persistent ChromaDB with cosine distance metric.
- **Sparse Keyword Search**: Implemented via BM25Okapi algorithm over tokenized document segments, capturing exact domain identifiers, product model numbers, and error codes.
- **Fusion Layer**: Reciprocal Rank Fusion (RRF) with constant k=60 combining vector similarity scores and keyword BM25 ranks.
- **Reranker**: Lexical-semantic cross-encoder re-scoring candidate passages based on exact phrase matches, query term frequency, and title proximity.
- **Relational Metadata Layer**: SQLite database managing user credentials, hashed passwords (bcrypt with cost factor 12), document SHA-256 signatures, and chunk mappings.

## 2. Account Access, Authentication, and Permissions

### User Roles and Permission Scopes
The platform defines two role levels:
1. **Admin Role**:
   - Upload new multi-format documents (`.pdf`, `.html`, `.md`, `.txt`).
   - Trigger index re-chunking and ChromaDB vector persistence.
   - Delete indexed documents and purge associated vector collections.
   - Run system evaluation benchmarks and access model telemetry.
2. **User Role**:
   - Query conversational documentation assistant.
   - Inspect grounded citation passages, source document names, and page numbers.
   - Browse document catalog in read-only mode.

### Account Provisioning and SSO
- New team members can register directly via the authentication endpoint or web UI.
- Default administrator credentials configured during initial seeding:
  - Username: `admin`
  - Password: `admin123`
- Single Sign-On (SSO) integration supports SAML 2.0 and OIDC identity providers (Okta, Azure Active Directory, Google Workspace).
- Sessions are governed by signed JWT tokens with 8-hour expiration. Refresh tokens expire after 14 days.
- **Account Lockout Policy**: Five consecutive incorrect password attempts trigger a 30-minute lockout. Unlocking immediately requires an administrator password reset or self-service email challenge.

## 3. Product Configuration and Environment Bindings

### Core Configuration Parameters
Configuration options are declared in the `.env` configuration file:
- `GEMINI_API_KEY`: Google Gemini API key used for generating text embeddings (`text-embedding-004`) and synthesis (`gemini-1.5-flash`).
- `BACKEND_HOST`: Network bind address for FastAPI (default: `127.0.0.1`).
- `BACKEND_PORT`: HTTP listening port for backend API (default: `8000`).
- `FRONTEND_PORT`: HTTP listening port for Streamlit UI (default: `8501`).
- `CHROMA_PERSIST_DIR`: Local storage directory for ChromaDB vector embeddings (default: `data/chroma_db`).
- `SQLITE_DB_PATH`: SQLite database file path (default: `data/enterprisedoc.db`).
- `CHUNK_SIZE`: Maximum text chunk length in characters (default: `700`).
- `CHUNK_OVERLAP`: Overlapping character boundary between adjacent chunks (default: `120`).

### Webhook Event Notifications
The platform emits outbound HTTPS POST webhook payloads on key document events:
- `document.indexed`: Dispatched upon successful document chunking and vector storage.
- `document.deleted`: Dispatched when a knowledge base entry is purged.
- `query.flagged`: Dispatched when contradiction detection or low-confidence (< 0.35) query occurs.
- Webhook payloads include SHA-256 HMAC signature headers (`X-EnterpriseDoc-Signature`) for replay prevention.

## 4. Usage Limits, Quotas, and Resource Constraints

### API Rate Limiting
- **Free / Evaluation Tier**: 60 requests per minute per IP address; maximum 1,000 queries per day.
- **Professional Tier**: 300 requests per minute per organization token; 50,000 queries per day.
- **Enterprise Dedicated Tier**: Up to 3,000 requests per minute; customized burst capacity.
- Exceeding quotas results in `HTTP 429 Too Many Requests` containing the `Retry-After: <seconds>` header.

### Document Ingestion Limits
- Maximum file size per upload: 25 MB for PDF, 10 MB for HTML, Markdown, and TXT.
- Maximum document page count: 500 pages per individual PDF document.
- Vector database capacity: Supports collections up to 250,000 chunks per index cluster before sharding.

## 5. Troubleshooting and Error Resolution Guide

### Error Code Reference Catalog
| HTTP Code | Error Name | Common Cause | Resolution |
|:---:|:---|:---|:---|
| **400** | Bad Request | Unsupported file format or corrupted document payload | Verify file extension matches `.pdf`, `.html`, `.md`, or `.txt` and is not 0 bytes. |
| **401** | Unauthorized | Missing or expired JWT bearer token; invalid credentials | Re-authenticate via `/api/v1/auth/token` or verify session state. |
| **403** | Forbidden | Standard user attempting admin-only operations (e.g. document deletion) | Check assigned user role; contact system administrator for elevated privileges. |
| **404** | Not Found | Requested document ID does not exist in SQLite database | Verify document list in dashboard before executing deletion or retrieval by ID. |
| **409** | Conflict | Duplicate file upload detected via identical SHA-256 hash | File has already been indexed; delete existing document if re-upload is required. |
| **429** | Too Many Requests | Exceeded requests-per-minute quota on backend or Gemini API | Implement exponential backoff retry; upgrade organization quota tier. |
| **500** | Internal Server Error | Vector database lock error or parser decoding failure | Check server logs in terminal; verify UTF-8 encoding of source documents. |
| **502 / 504** | Upstream Timeout | Gemini API connectivity issues or outbound internet latency | Confirm network internet connection; check Google Cloud API status page. |

### Diagnostic Health Checks
- Backend health endpoint: `GET http://localhost:8000/docs`
- Health probe API: `GET http://localhost:8000/api/v1/stats` returns total documents, chunk metrics, and database status.
- Resetting local state: If vector indices become corrupted, stop the backend, delete `data/chroma_db/`, and run `python scripts/seed_documents.py`.

## 6. Versioning, Deprecation Notices, and Conflict Handling

### API Version 1 vs Version 2 Differences
> **CRITICAL NOTICE (Version Conflict Policy)**:
> - **API v1 (Legacy)**: Used basic HTTP authentication (`Authorization: Basic <base64>`) and raw text responses without structured citation metadata. Legacy XML payload responses are deprecated as of March 2026.
> - **API v2 (Current)**: Strictly mandates Bearer JWT tokens (`Authorization: Bearer <jwt>`). All responses return structured JSON with confidence ratings, inline `[Source N]` citations, and verified evidence excerpts.
> - Any application attempting to transmit XML requests to v2 endpoints will receive `HTTP 415 Unsupported Media Type`.
