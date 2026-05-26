from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from core.context import get_active_context_string
from core.memory import save_selection_to_context, clear_active_context

router = APIRouter()

@router.get("/api/core/context/active")
async def api_get_active_context():
    context_str = get_active_context_string()
    return {"active_context_string": context_str}

@router.post("/api/core/context/clear_active")
async def api_clear_active_context():
    clear_active_context()
    return {"status": "success"}


class SaveSelectionRequest(BaseModel):
    selected_text: str
    user_prompt: str

@router.post("/api/core/context/save_selection")
async def api_save_selection(data: SaveSelectionRequest):
    block_id, chunk_id = save_selection_to_context(data.selected_text, data.user_prompt)
    if not block_id:
        return {"status": "error", "message": "Failed to save selection"}
    return {"status": "success", "block_id": block_id, "chunk_id": chunk_id}

from typing import Optional, Dict, Any
from integrations.llm_client import call_llm
from tests.evaluator import evaluate_response

class ChatRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None

@router.post("/chat")
async def chat(data: ChatRequest):
    user_prompt = data.prompt
    config = data.config or {}
    run_eval = config.get("evaluate", False)
    
    active_context = get_active_context_string()
    response_text = call_llm(user_prompt, active_context_string=active_context, config=config)
    
    eval_metrics = None
    if run_eval:
        eval_metrics = evaluate_response(user_prompt, response_text, active_context, config)
        
    return {
        "response": response_text,
        "active_context_used": active_context,
        "user_prompt": user_prompt,
        "evaluation": eval_metrics
    }

@router.post("/save_selection")
async def chat_save_selection(data: SaveSelectionRequest):
    return await api_save_selection(data)
