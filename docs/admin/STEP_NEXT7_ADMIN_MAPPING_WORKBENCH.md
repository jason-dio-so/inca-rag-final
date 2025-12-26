# STEP NEXT-7: Admin Mapping Workbench

## 목적 (Purpose)

UNMAPPED/AMBIGUOUS 상태의 coverage mapping을 수동으로 해결하고, 해결 결과를 DB에 반영하여 향후 동일/유사 질의에서 자동으로 해결되도록 한다.

**핵심**: 신정원(통일담보명/통일코드)이 절대 기준(canonical)이며, 모든 매핑은 이를 위반하면 안 된다.

## Constitutional Requirements (헌법 원칙)

### 1. Canonical Coverage Rule (절대)
- **coverage_code는 반드시 신정원 통일코드에 정합해야 한다**
- Admin이 승인하는 매핑도 "신정원 통일코드 → alias/name" 방향으로만 확정
- 존재하지 않는 코드 승인 시 거부 (400 error)

### 2. Fact-only / No Inference
- Admin UI는 후보/근거/상태를 보여주고 "판단/추천" 문구를 생성하지 않는다
- 자동 승인 금지 (운영자 승인만 DB 반영)

### 3. Deterministic & Auditable
- 승인/반영은 재현 가능한 규칙/로그가 남아야 한다
- 누가, 언제, 무엇을, 왜(근거 ref) 승인했는지 감사 로그 필수

### 4. Frontend/Backend 분리
- Frontend는 표시/선택/승인 요청만
- Backend에서 검증(신정원 코드 존재, 중복/충돌 체크) 후 커밋

### 5. Safe Defaults
- 충돌/불명확 시 "거부/보류"가 기본
- 자동 overwrite 금지

---

## Architecture

### Data Flow

```
User Query → Compare API → UNMAPPED/AMBIGUOUS detected
                           ↓
                    mapping_event_queue (OPEN)
                           ↓
                    Admin UI (선택/승인)
                           ↓
                    Backend Validation (canonical code 존재 확인)
                           ↓
                    DB Reflection (coverage_code_alias / coverage_name_map)
                           ↓
                    Audit Log (admin_audit_log)
```

### Database Schema

#### 1. `mapping_event_queue` (이벤트 큐)
- **Purpose**: UNMAPPED/AMBIGUOUS 이벤트 저장
- **Key Fields**:
  - `insurer`: 보험사
  - `query_text`: 원 질의
  - `raw_coverage_title`: 문서 원문 담보명
  - `detected_status`: UNMAPPED | AMBIGUOUS
  - `candidate_coverage_codes`: 후보 신정원 코드 (jsonb)
  - `state`: OPEN | APPROVED | REJECTED | SNOOZED
  - `resolved_coverage_code`: 승인된 신정원 코드
  - `resolution_type`: ALIAS | NAME_MAP | MANUAL_NOTE
- **Deduplication**: Only one OPEN event per (insurer, raw_coverage_title, detected_status)

#### 2. `coverage_code_alias` (별칭 테이블)
- **Purpose**: 질의 별칭 → 신정원 코드 매핑
- **Key Fields**:
  - `insurer`: 보험사
  - `alias_text`: 별칭 텍스트
  - `coverage_code`: 신정원 통일코드
  - `created_by`: 승인자
- **UNIQUE**: (insurer, alias_text)

#### 3. `coverage_name_map` (담보명 매핑 테이블)
- **Purpose**: 문서 원문 담보명 → 신정원 코드 매핑
- **Key Fields**:
  - `insurer`: 보험사
  - `raw_name`: 문서 원문 담보명
  - `coverage_title_normalized`: 표시용 정규화 담보명
  - `coverage_code`: 신정원 통일코드
  - `created_by`: 승인자
- **UNIQUE**: (insurer, raw_name)

#### 4. `admin_audit_log` (감사 로그)
- **Purpose**: 모든 Admin 액션 감사 로그
- **Key Fields**:
  - `actor`: 승인자
  - `action`: APPROVE | REJECT | SNOOZE | UPSERT_ALIAS | UPSERT_NAME_MAP
  - `target_type`: EVENT | ALIAS | NAME_MAP
  - `target_id`: 대상 ID
  - `before` / `after`: 변경 전/후 상태 (jsonb)
  - `evidence_ref_ids`: 근거 참조 (jsonb)

---

## Backend API

### Endpoints

#### 1. `GET /admin/mapping/events`
**Purpose**: 이벤트 큐 조회 (페이지네이션)

**Query Parameters**:
- `state`: EventState (OPEN | APPROVED | REJECTED | SNOOZED)
- `insurer`: 보험사 필터
- `page`: 페이지 번호 (1-indexed)
- `page_size`: 페이지 크기 (default: 50)

**Response**:
```json
{
  "events": [
    {
      "id": "uuid",
      "created_at": "2025-12-26T...",
      "insurer": "SAMSUNG",
      "raw_coverage_title": "일반암 진단비",
      "detected_status": "UNMAPPED",
      "state": "OPEN",
      "candidate_count": 1
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

#### 2. `GET /admin/mapping/events/{event_id}`
**Purpose**: 이벤트 상세 조회 (후보 + 근거 포함)

**Response**:
```json
{
  "id": "uuid",
  "insurer": "SAMSUNG",
  "query_text": "일반암진단비",
  "raw_coverage_title": "일반암 진단비",
  "detected_status": "UNMAPPED",
  "candidate_coverage_codes": ["CA_DIAG_GENERAL"],
  "evidence_ref_ids": null,
  "state": "OPEN"
}
```

#### 3. `POST /admin/mapping/approve`
**Purpose**: 이벤트 승인 및 DB 반영

**Request**:
```json
{
  "event_id": "uuid",
  "coverage_code": "CA_DIAG_GENERAL",
  "resolution_type": "NAME_MAP",
  "note": "Canonical code confirmed",
  "actor": "admin"
}
```

**Response**:
```json
{
  "success": true,
  "event_id": "uuid",
  "resolved_coverage_code": "CA_DIAG_GENERAL",
  "resolution_type": "NAME_MAP",
  "audit_log_id": "uuid",
  "message": "Event approved and NAME_MAP mapping created"
}
```

**Validation**:
- coverage_code 존재 확인 (coverage_standard 테이블)
- 충돌 확인 (동일 alias/raw_name이 다른 코드로 이미 매핑돼 있으면 400)
- 트랜잭션: 모두 성공 or 모두 실패

**Error Codes**:
- `400`: Validation error (invalid code, conflict)
- `404`: Event not found or not in OPEN state

#### 4. `POST /admin/mapping/reject`
**Purpose**: 이벤트 거부

**Request**:
```json
{
  "event_id": "uuid",
  "note": "Invalid mapping",
  "actor": "admin"
}
```

#### 5. `POST /admin/mapping/snooze`
**Purpose**: 이벤트 보류

**Request**:
```json
{
  "event_id": "uuid",
  "note": "Need more information",
  "actor": "admin"
}
```

---

## Frontend UI

### Page: `/admin/mapping`

#### Layout
- **Left Panel**: Event Queue (리스트)
- **Right Panel**: Event Detail (선택 시)

#### Queue Panel
- OPEN 이벤트 우선 표시
- 필터: state (OPEN/ALL)
- 정렬: created_at DESC
- 페이지네이션

#### Detail Panel
- **Event Info**:
  - Query text
  - Insurer
  - Raw coverage title
  - Detected status (UNMAPPED/AMBIGUOUS)
- **Candidate Codes** (신정원 통일코드):
  - Radio button 선택
  - 수동 입력 가능 (fallback)
- **Resolution Type**:
  - NAME_MAP: 담보명 매핑
  - ALIAS: 별칭 등록
  - MANUAL_NOTE: 수동 메모
- **Note**: Optional 텍스트
- **Actions**:
  - Approve (승인)
  - Reject (거부)
  - Snooze (보류)

#### UI 문구 규칙
- ❌ "더 좋다/추천" 금지
- ✅ 상태는 코드 그대로 표시 (UNMAPPED/AMBIGUOUS/OPEN/APPROVED 등)

---

## Validation Logic (Backend)

### 1. Canonical Code Validation
```python
async def _validate_canonical_coverage_code(conn, coverage_code: str):
    """
    Validate that coverage_code exists in canonical source (신정원 통일코드).
    Raises ValidationError if code does not exist.
    """
    exists = await conn.fetchval(
        "SELECT EXISTS(SELECT 1 FROM coverage_standard WHERE coverage_code = $1)",
        coverage_code
    )
    if not exists:
        raise ValidationError(
            f"Coverage code '{coverage_code}' does not exist in canonical source. "
            f"Constitutional violation: Canonical Coverage Rule."
        )
```

### 2. Conflict Detection
```python
async def _check_alias_conflict(conn, insurer, alias_text, coverage_code):
    """
    Check if alias already exists with different coverage_code.
    Returns conflicting code if exists, None otherwise.
    """
    existing = await conn.fetchrow(
        "SELECT coverage_code FROM coverage_code_alias WHERE insurer = $1 AND alias_text = $2",
        insurer, alias_text
    )
    if existing and existing["coverage_code"] != coverage_code:
        return existing["coverage_code"]  # Conflict!
    return None
```

### 3. Approval Transaction
```python
async def approve_event(request: ApproveEventRequest):
    async with conn.transaction():
        # 1. Load event (OPEN only)
        # 2. Validate canonical code
        # 3. Check conflicts
        # 4. Upsert to alias/name_map table
        # 5. Update event state
        # 6. Create audit log
        # All or nothing
```

---

## Testing

### Backend Tests (`tests/test_admin_mapping_approve.py`)

1. **test_approve_event_success**:
   - OPEN 이벤트 승인 → NAME_MAP 생성 + event APPROVED + audit log 생성

2. **test_approve_event_invalid_code**:
   - coverage_code가 존재하지 않으면 400 (Constitutional violation)

3. **test_approve_event_conflict**:
   - alias가 다른 코드로 이미 존재 → 승인 실패 (409)

4. **test_audit_log_created**:
   - 승인 시 audit log에 before/after 남음

5. **test_reject_event**:
   - 거부 시 state REJECTED + audit log

6. **test_snooze_event**:
   - 보류 시 state SNOOZED + audit log

7. **test_deduplication**:
   - 동일 입력으로 중복 이벤트 생성되지 않음

### Frontend Tests (최소)
- `/admin/mapping` 렌더 스모크 1개 (빌드 깨짐 방지)
- Queue → Detail → Approve API 호출까지 최소 동작 확인

---

## Integration with Compare Flow

### Event Creation Trigger
- `/compare` endpoint에서 UNMAPPED/AMBIGUOUS 감지 시
- `src/admin_mapping/integration.py::maybe_create_unmapped_event_from_compare()` 호출

```python
from src.admin_mapping.integration import maybe_create_unmapped_event_from_compare

# In compare endpoint
if coverage_a and coverage_a.get("mapping_status") in ["UNMAPPED", "AMBIGUOUS"]:
    await maybe_create_unmapped_event_from_compare(
        db_pool=db_pool,
        insurer=coverage_a["insurer"],
        query=request.query,
        coverage_data=coverage_a,
    )
```

---

## Deployment Checklist

- [ ] Run migration: `migrations/step_next7_admin_mapping_workbench.sql`
- [ ] Register router in FastAPI app
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Verify `/admin/mapping` page loads
- [ ] Create test UNMAPPED event manually
- [ ] Approve event and verify DB reflection

---

## DoD (Definition of Done)

- [x] OPEN UNMAPPED/AMBIGUOUS 이벤트가 큐에 쌓인다 (중복 방지)
- [x] Admin UI에서 이벤트를 선택하고 coverage_code를 지정해 승인하면
      coverage_code_alias 또는 coverage_name_map에 반영된다
- [x] 승인/거부/보류 모든 액션이 admin_audit_log에 남는다
- [x] 충돌/중복/존재하지 않는 코드 등은 보수적으로 실패한다 (자동 overwrite 금지)
- [x] 최소 백엔드 테스트 통과 + 프론트 빌드 깨짐 없음
- [ ] 문서/STATUS 업데이트 + main 커밋/푸시 완료

---

## 금지 사항 (Constitutional Violations)

1. ❌ 신정원 코드가 아닌 임의 코드 승인
2. ❌ 자동 승인 (운영자 승인 필수)
3. ❌ 충돌 무시 (safe defaults 위반)
4. ❌ Audit log 누락
5. ❌ "추천/더 좋다" UI 문구 생성

---

## Future Enhancements

1. **인증 시스템**: X-Admin-Actor 헤더 → OAuth/JWT 인증
2. **AMBIGUOUS 후보 자동 생성**: Excel 매핑에서 여러 후보 감지
3. **Evidence 패널 통합**: CompareViewModelRenderer의 EvidenceAccordion 재사용
4. **Bulk Actions**: 여러 이벤트 일괄 승인/거부
5. **Admin Dashboard**: 승인율, 처리 속도 통계

---

## References

- Constitutional: `/Users/cheollee/inca-RAG-final/CLAUDE.md`
- Migration: `/Users/cheollee/inca-RAG-final/migrations/step_next7_admin_mapping_workbench.sql`
- Backend: `/Users/cheollee/inca-RAG-final/src/admin_mapping/`
- Frontend: `/Users/cheollee/inca-RAG-final/apps/web/src/pages/admin/mapping.tsx`
- Tests: `/Users/cheollee/inca-RAG-final/tests/test_admin_mapping_approve.py`
