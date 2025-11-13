import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Project as ProjectSchema, Message as MessageSchema

app = FastAPI(title="Aarav Tatiya Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str


SAMPLE_PROJECTS = [
    {
        "title": "Immersive Brand Microsite",
        "role": "Lead 3D & Frontend",
        "year": 2024,
        "description": "A lightweight WebGL brand experience with scroll-driven narrative and Spline-authored hero.",
        "tech": ["React", "Three.js", "Spline", "Framer Motion"],
        "images": [
            "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?q=80&w=1600&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1504639725590-34d0984388bd?q=80&w=1600&auto=format&fit=crop"
        ],
        "slug": "immersive-brand-microsite",
        "featured": True,
        "url": "https://example.com/project/immersive-brand-microsite"
    },
    {
        "title": "Realtime Product Configurator",
        "role": "3D Developer",
        "year": 2023,
        "description": "GPU-optimized configurator with LOD meshes, compressed textures, and AR preview.",
        "tech": ["React", "r3f", "GLTF", "WebGL"],
        "images": [
            "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1600&auto=format&fit=crop"
        ],
        "slug": "realtime-product-configurator",
        "featured": True,
        "url": "https://example.com/project/realtime-product-configurator"
    },
    {
        "title": "Data-Driven Portfolio Engine",
        "role": "Full-Stack Engineer",
        "year": 2022,
        "description": "Composable portfolio with CMS, structured data, and blazing-fast edge rendering.",
        "tech": ["Next.js", "MongoDB", "Edge Runtime"],
        "images": [
            "https://images.unsplash.com/photo-1516259762381-22954d7d3ad2?q=80&w=1600&auto=format&fit=crop"
        ],
        "slug": "data-driven-portfolio-engine",
        "featured": True,
        "url": "https://example.com/project/data-driven-portfolio-engine"
    }
]


@app.get("/")
def read_root():
    return {"message": "Aarav Tatiya Portfolio API running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


@app.get("/api/projects")
async def list_projects(limit: Optional[int] = None):
    # Try to read from database; if not available, fall back to sample data
    try:
        if db is not None:
            docs = get_documents("project", {}, limit=limit or 50)
            # If empty, seed with samples once for demo purposes
            if not docs:
                for p in SAMPLE_PROJECTS:
                    try:
                        _ = create_document("project", p)
                    except Exception:
                        pass
                docs = get_documents("project", {}, limit=limit or 50)
            # Map ObjectId to string id if present
            for d in docs:
                if "_id" in d:
                    d["id"] = str(d.pop("_id"))
            return {"projects": docs}
    except Exception:
        pass

    data = SAMPLE_PROJECTS[:limit] if limit else SAMPLE_PROJECTS
    return {"projects": data}


@app.get("/api/projects/{slug}")
async def get_project(slug: str):
    try:
        if db is not None:
            docs = get_documents("project", {"slug": slug}, limit=1)
            if docs:
                d = docs[0]
                if "_id" in d:
                    d["id"] = str(d.pop("_id"))
                return d
    except Exception:
        pass

    for p in SAMPLE_PROJECTS:
        if p["slug"] == slug:
            return p
    raise HTTPException(status_code=404, detail="Project not found")


@app.post("/api/contact")
async def submit_contact(payload: ContactRequest):
    # Validate with MessageSchema
    msg = MessageSchema(name=payload.name, email=payload.email, message=payload.message)
    try:
        if db is not None:
            _id = create_document("message", msg)
            return {"status": "ok", "id": _id}
    except Exception:
        pass
    # If DB not available, still return ok to keep UX smooth
    return {"status": "ok", "id": None}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
