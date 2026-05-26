from fastapi import FastAPI
from integrations.chatbot.router import router as chatbot_router
import os

app = FastAPI(title="Cognitive Chatbot Runtime Engine")

app.include_router(chatbot_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5005, reload=True)
