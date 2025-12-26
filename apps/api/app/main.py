"""
inca-RAG-final STEP 5 FastAPI Application

Contract-driven implementation enforcing operational constitution.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import products, compare, evidence, view_model, compile
from .admin_mapping import router as admin_mapping_router
from .db import close_async_pool

app = FastAPI(
    title="inca-RAG-final STEP 5 API",
    version="0.1.0",
    description="""
STEP 5 API Contract Implementation

운영 헌법:
- Compare/Retrieval 축: chunk.is_synthetic=false 강제 (synthetic evidence 금지)
- Amount Bridge 축: include_synthetic 옵션으로 synthetic 허용 (축 분리)
- coverage_standard 자동 INSERT/UPDATE 금지 (해당 API 없음)
- premium mode 정렬은 premium 필터 없으면 400
""",
)

# CORS middleware (STEP 33-α: Allow preflight for /compare)
# Controlled via CORS_ORIGINS env (defaults to localhost:3000 for dev)
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Includes OPTIONS for preflight
    allow_headers=["*"],  # Includes Content-Type
)

# Register routers
app.include_router(products.router)
app.include_router(compare.router)
app.include_router(evidence.router)
app.include_router(view_model.router)
app.include_router(compile.router)
app.include_router(admin_mapping_router)  # STEP NEXT-7: Admin Mapping Workbench


@app.get("/")
async def root():
    """Health check / API info"""
    return {
        "service": "inca-RAG-final STEP 5 API",
        "version": "0.1.0",
        "status": "operational",
        "contract": "openapi/step5_openapi.yaml",
        "constitution": [
            "Compare axis: is_synthetic=false mandatory",
            "Amount Bridge axis: synthetic allowed (option)",
            "Premium mode requires premium filter",
            "coverage_standard auto-INSERT forbidden",
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup async database pool on shutdown"""
    await close_async_pool()
