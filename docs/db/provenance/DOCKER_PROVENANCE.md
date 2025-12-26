# Docker Provenance Report

**Generated**: 2025-12-26
**Purpose**: Container/Volume/Environment provenance audit (READ-ONLY)
**Target**: `inca_pg_step14` container + `inca-rag-final_postgres_step14_data` volume

---

## Container: inca_pg_step14

### Basic Info
- **Container ID**: `dc1e967f5fcb73e6f8e739777aca63b9b78f50d650f7bfc08a45bf01b6a3f2b3`
- **Image**: `postgres:17-alpine` (sha256:ff4ccc02b97e)
- **Name**: `/inca_pg_step14`
- **Status**: **Running** (Up 5 hours as of 2025-12-26 08:39 UTC)
- **Health**: **healthy** (pg_isready check every 10s)

### Lifecycle Timestamps
- **Created**: `2025-12-25T06:24:38.121449628Z` (2025-12-25 15:24 KST)
- **StartedAt**: `2025-12-26T03:48:02.361841959Z` (2025-12-26 12:48 KST)
- **FinishedAt** (previous run): `2025-12-25T15:49:42.834257418Z` (2025-12-26 00:49 KST)

**Interpretation**:
- Container created: 2025-12-25 15:24 KST
- Last restart: 2025-12-26 12:48 KST (12시간 전)
- Restart policy: `unless-stopped`

### Environment Variables

**Postgres Configuration**:
- `POSTGRES_DB=inca_rag_final`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=******` (masked for security)
- `PGDATA=/var/lib/postgresql/data`

**Legacy Variables**: ❌ Not present
- No `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` env vars
- Container only uses standard `POSTGRES_*` variables

**Conclusion**: Container uses PostgreSQL official env vars (not apps/api/.env contract)

### Port Mapping
- **Container**: `5432/tcp`
- **Host**: `0.0.0.0:5433->5432/tcp` + `[::]:5433->5432/tcp`

**Conclusion**: Exposed on host port **5433** (IPv4 + IPv6)

### Volume Mount

**Mount**:
- **Type**: volume
- **Name**: `inca-rag-final_postgres_step14_data`
- **Source**: `/var/lib/docker/volumes/inca-rag-final_postgres_step14_data/_data`
- **Destination**: `/var/lib/postgresql/data` (inside container)
- **Mode**: `rw` (read-write)

### Network
- **Network**: `inca-rag-final_inca_network`
- **Aliases**: `inca_pg_step14`, `postgres`
- **Internal IP**: `172.19.0.2/16`
- **Gateway**: `172.19.0.1`

### Docker Compose Metadata

**Labels**:
- `com.docker.compose.project`: `inca-rag-final`
- `com.docker.compose.service`: `postgres`
- `com.docker.compose.config_files`: `/Users/cheollee/inca-RAG-final/docker-compose.step14.yml`
- `com.docker.compose.version`: `2.40.3`

**Conclusion**: Container managed by Docker Compose (step14 configuration)

---

## Volume: inca-rag-final_postgres_step14_data

### Basic Info
- **Name**: `inca-rag-final_postgres_step14_data`
- **Driver**: `local`
- **Mountpoint**: `/var/lib/docker/volumes/inca-rag-final_postgres_step14_data/_data`
- **CreatedAt**: `2025-12-24T23:21:53Z` (2025-12-25 08:21 KST)

### Labels
- `com.docker.compose.project`: `inca-rag-final`
- `com.docker.compose.volume`: `postgres_step14_data`
- `com.docker.compose.version`: `2.40.3`

**Interpretation**:
- Volume created: **2025-12-25 08:21 KST** (12월 25일 오전)
- Volume is ~1.5 days old as of 2025-12-26 09:00 KST

---

## Timeline Reconstruction

### 2025-12-24 23:21 UTC (2025-12-25 08:21 KST)
- ✅ Volume `inca-rag-final_postgres_step14_data` created

### 2025-12-25 06:24 UTC (2025-12-25 15:24 KST)
- ✅ Container `inca_pg_step14` created (first time)
- 🔗 Mounted to volume created ~7 hours earlier

### 2025-12-25 15:49 UTC (2025-12-26 00:49 KST)
- ⏸ Container stopped (FinishedAt timestamp)

### 2025-12-26 03:48 UTC (2025-12-26 12:48 KST)
- ▶ Container restarted
- 🟢 Currently running (healthy)

---

## Provenance Implications

### Volume Age vs DB Data Age
From previous DB audit:
- `proposal_coverage_universe.created_at`: `2025-12-24 23:21:58.65662`
- Volume created: `2025-12-24T23:21:53Z`

**Time Delta**: **~5 seconds**

**Conclusion**:
- DB rows inserted **immediately after volume creation** (within 5 seconds)
- Suggests **automated seed/migration** ran during initial container setup
- NOT manual insertion (timing too precise)

### Container Lifecycle vs Data Persistence
- Container has been **stopped and restarted** (2025-12-26 00:49 → 12:48)
- Volume persists across container restarts (standard Docker behavior)
- DB data from 2025-12-24 23:21 still present (volume not recreated)

### Docker Compose Configuration
- Compose file: `docker-compose.step14.yml`
- Compose project: `inca-rag-final`
- Service name: `postgres`

**Next Step**: Check `docker-compose.step14.yml` for init scripts or volume mounts

---

## Evidence Catalog

### Container Metadata
- ID: `dc1e967f5fcb73e6f8e739777aca63b9b78f50d650f7bfc08a45bf01b6a3f2b3`
- Image SHA: `sha256:ff4ccc02b97e0ebb6b328ef9ff92522f95586f83be6801896b615088defc8ad2`
- Created: `2025-12-25T06:24:38Z`
- RestartCount: 0 (no crashes, manual restart only)

### Volume Metadata
- Created: `2025-12-24T23:21:53Z`
- Mountpoint: `/var/lib/docker/volumes/inca-rag-final_postgres_step14_data/_data`

### Environment Contract
- ✅ Uses `POSTGRES_*` env vars (standard PostgreSQL)
- ❌ Does NOT use `DB_*` env vars (apps/api/.env contract)
- ⚠️ Mismatch with apps/api/.env.example SSOT

---

## SSOT Compliance Check

### DB Contract (CLAUDE.md § DB Contract)
**Expected**:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` env vars
- apps/api/.env.example = SSOT

**Actual**:
- Container uses `POSTGRES_*` env vars
- No `DB_*` env vars in container environment

**Status**: ⚠️ **Partial compliance**
- Container naming (`inca_pg_step14`) matches convention
- Port (`5433`) matches DB Contract default
- But env vars don't follow apps/api/.env.example pattern

**Implication**:
- Container was **not** launched via apps/api/.env
- Likely launched via `docker-compose.step14.yml` with hardcoded env
- May need alignment with DB Contract SSOT

---

## Summary

| Aspect | Value | SSOT Status |
|--------|-------|-------------|
| Container Created | 2025-12-25 15:24 KST | ℹ️ Timeline |
| Volume Created | 2025-12-25 08:21 KST | ℹ️ Timeline |
| DB Data Inserted | 2025-12-24 23:21:58 UTC (within 5s of volume creation) | ⚠️ Automated seed suspected |
| Env Vars | `POSTGRES_*` (not `DB_*`) | ⚠️ Partial SSOT compliance |
| Port | 5433 | ✅ Matches DB Contract |
| Restart Policy | unless-stopped | ℹ️ Production-like |
| Health Check | pg_isready every 10s | ✅ Active monitoring |

**Key Finding**: DB data inserted **within 5 seconds** of volume creation suggests **automated init script/migration** during container first run.

---

**Next Investigation**:
1. Check `docker-compose.step14.yml` for:
   - Init scripts (`/docker-entrypoint-initdb.d/`)
   - Volume mounts for migrations
   - Linked services (API container)
2. Check repo for migration execution around 2025-12-24 23:21 UTC
