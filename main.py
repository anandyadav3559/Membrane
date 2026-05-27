from fastapi import FastAPI
from integrations.web.router import router as web_router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Membrane Runtime Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(web_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5005, reload=True)
