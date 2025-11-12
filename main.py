from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from database import db, create_document, get_documents
from datetime import datetime

app = FastAPI(title="Event Designer API", version="1.0.0")

# CORS setup - allow all by default; in production, restrict to specific origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    message: str = Field(..., min_length=5, max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    social: Optional[str] = Field(None, max_length=200)


class FeedbackOut(BaseModel):
    id: str
    name: str
    message: str
    rating: Optional[int] = None
    created_at: Optional[datetime] = None


@app.get("/test")
async def test_connection():
    # Verify database connectivity if available
    try:
        if db is not None:
            # ping by listing collections
            _ = db.list_collection_names()
            db_status = "connected"
        else:
            db_status = "not_configured"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status}


@app.post("/feedback", response_model=dict)
async def create_feedback(feedback: FeedbackIn):
    try:
        inserted_id = create_document("testimonial", feedback)
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/testimonials", response_model=List[FeedbackOut])
async def list_testimonials(limit: int = 5):
    try:
        docs = get_documents("testimonial", {}, limit)
        # Sort newest first by created_at if available
        docs.sort(key=lambda d: d.get("created_at"), reverse=True)
        results: List[FeedbackOut] = []
        for d in docs:
            results.append(
                FeedbackOut(
                    id=str(d.get("_id")),
                    name=d.get("name", ""),
                    message=d.get("message", ""),
                    rating=d.get("rating"),
                    created_at=d.get("created_at"),
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
