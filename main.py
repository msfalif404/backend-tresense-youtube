from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api import youtube_metadata, auth, youtube_autocomment
from core.config import verify_token

app = FastAPI(
    title="YouTube Metadata API",
    description="API untuk mengambil metadata video YouTube setelah login dengan Google OAuth",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(youtube_metadata.router, prefix="/youtube", tags=["YouTube Metadata"])
app.include_router(youtube_autocomment.router, prefix="/youtube", tags=["YouTube AutoComment"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the YouTube Metadata API. Visit /youtube to start."}

@app.get("/protected", tags=["Auth"])
def protected_route(user=Depends(verify_token)):
    return {
        "message": "Access granted. You are authenticated!",
        "user": user
    }
