import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_client import call_llm

LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
EVAL_LOG_FILE = os.path.join(LOGS_DIR, 'evaluation.jsonl')

def evaluate_response(user_prompt, bot_response, active_context, config):
    """
    Evaluates the LLM response for hallucination and confidence using LLM-as-a-judge.
    Also calculates token usage and saves logs to tests/logs/evaluation.jsonl.
    """
    if config.get("mode") == "simulate":
        eval_data = {
            "hallucination_score": 0.0,
            "confidence_score": 1.0,
            "reasoning": "Simulated response is always perfect.",
            "tokens": 0
        }
    else:
        eval_prompt = f"""
You are an expert evaluator assessing an AI's response for Hallucination and Confidence.

[CONTEXT PROVIDED TO AI]
{active_context if active_context else "None"}

[USER QUESTION]
{user_prompt}

[AI RESPONSE]
{bot_response}

Evaluate the AI response based on the context. If the AI stated facts not found in the context (when context was provided), that is a hallucination. If the AI sounds unsure, confidence is low.
Output ONLY valid JSON with no markdown formatting or backticks. Format:
{{
  "hallucination_score": 0.0,
  "confidence_score": 1.0,
  "reasoning": "short explanation"
}}
"""
        raw_eval = call_llm(eval_prompt, active_context_string="", config=config)
        
        try:
            import re
            clean_eval = re.sub(r'```json\n|\n```|```', '', raw_eval.strip())
            eval_data = json.loads(clean_eval)
        except Exception as e:
            eval_data = {
                "hallucination_score": -1.0,
                "confidence_score": -1.0,
                "reasoning": f"Failed to parse eval JSON: {str(e)}\nRaw: {raw_eval}"
            }

    # Token counting using tiktoken
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        prompt_tokens = len(enc.encode(user_prompt + str(active_context or "")))
        completion_tokens = len(enc.encode(bot_response))
        total_tokens = prompt_tokens + completion_tokens
    except ImportError:
        total_tokens = (len(user_prompt) + len(str(active_context or "")) + len(bot_response)) // 4

    eval_data["tokens"] = total_tokens
    eval_data["timestamp"] = int(time.time())
    
    # Save log
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    with open(EVAL_LOG_FILE, 'a') as f:
        log_entry = {
            "user_prompt": user_prompt,
            "bot_response": bot_response,
            "evaluation": eval_data
        }
        f.write(json.dumps(log_entry) + '\n')
        
    return eval_data
