from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from core.context import get_active_context_string
from core.memory import save_selection_to_context
from core.chunking import split_text_into_chunks
from integrations.chatbot.llm_client import call_llm
from tests.evaluator import evaluate_response

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

class ChatRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None

@router.post("/chat")
async def chat(data: ChatRequest):
    user_prompt = data.prompt
    config = data.config or {"mode": "simulate"}
    run_eval = config.get("evaluate", False)
    
    active_context = get_active_context_string()
    response_text = call_llm(user_prompt, active_context_string=active_context, config=config)
    chunks = split_text_into_chunks(response_text)
    
    eval_metrics = None
    if run_eval:
        eval_metrics = evaluate_response(user_prompt, response_text, active_context, config)
        
    return {
        "response": response_text,
        "chunks": chunks,
        "active_context_used": active_context,
        "user_prompt": user_prompt,
        "evaluation": eval_metrics
    }

class SaveSelectionRequest(BaseModel):
    indexes: List[int]
    response_text: str
    user_prompt: str

@router.post("/save_selection")
async def save_selection(data: SaveSelectionRequest):
    block_id = save_selection_to_context(data.indexes, data.response_text, data.user_prompt)
    return {"status": "success", "block_id": block_id}
