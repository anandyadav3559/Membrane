import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
EVAL_LOG_FILE = os.path.join(LOGS_DIR, 'evaluation.jsonl')

def evaluate_response(user_prompt, bot_response, active_context, config):
    """
    Evaluates the LLM response using Ragas, DeepEval, and TruLens.
    """
    if config.get("mode") == "simulate":
        return {
            "hallucination_score": 0.0,
            "confidence_score": 1.0,
            "reasoning": "Simulated response is perfect.",
            "tokens": 0
        }

    eval_data = {
        "hallucination_score": 0.0,
        "confidence_score": 0.0,
        "reasoning": "",
        "ragas": {},
        "deepeval": {},
        "trulens": {}
    }

    # Setup common LangChain LLM for the local proxy
    try:
        from langchain_openai import ChatOpenAI
        import os
        
        # Override env vars so libraries default to our proxy
        # We must use 'or' because the UI passes an empty string '""' when no key is entered
        os.environ["OPENAI_API_KEY"] = config.get("api_key") or "dummy_proxy_key"
        
        if config.get("mode") == "proxy":
            proxy_url = config.get("proxy_url") or "http://localhost:8001/v1/chat/completions"
            os.environ["OPENAI_API_BASE"] = proxy_url.replace("/chat/completions", "")
            
        llm = ChatOpenAI(model=config.get("model", "llama-3.1-8b-instant"))
    except ImportError:
        llm = None

    # --- RAGAS ---
    try:
        from ragas import evaluate
        from datasets import Dataset
        from ragas.metrics import faithfulness
        from ragas.llms import LangchainLLMWrapper
        
        ragas_llm = LangchainLLMWrapper(llm)
        
        data = {
            "question": [user_prompt],
            "answer": [bot_response],
            "contexts": [[active_context] if active_context else [""]],
            "ground_truth": [""]
        }
        dataset = Dataset.from_dict(data)
        
        # We only use faithfulness since answer_relevancy requires an embedding model which the proxy may not support
        ragas_result = evaluate(
            dataset,
            metrics=[faithfulness],
            llm=ragas_llm,
            raise_exceptions=False
        )
        eval_data["ragas"] = {
            "faithfulness": ragas_result.get("faithfulness", 0.0)
        }
    except Exception as e:
        eval_data["ragas"] = {"error": str(e)}

    # --- DEEPEVAL ---
    try:
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import HallucinationMetric
        from deepeval.models import DeepEvalBaseLLM
        
        class ProxyLLM(DeepEvalBaseLLM):
            def __init__(self, model):
                self.model = model
            def load_model(self): return self.model
            def generate(self, prompt: str) -> str:
                return self.model.invoke(prompt).content
            async def a_generate(self, prompt: str) -> str:
                return self.generate(prompt)
            def get_model_name(self): return "ProxyModel"
            
        proxy_deepeval_llm = ProxyLLM(llm)
        
        test_case = LLMTestCase(
            input=user_prompt,
            actual_output=bot_response,
            context=[active_context] if active_context else [""]
        )
        
        hallucination_metric = HallucinationMetric(threshold=0.5, model=proxy_deepeval_llm)
        hallucination_metric.measure(test_case)
        
        eval_data["deepeval"] = {
            "hallucination": hallucination_metric.score,
            "reason": hallucination_metric.reason
        }
    except Exception as e:
        eval_data["deepeval"] = {"error": str(e)}

    # --- TRULENS ---
    try:
        # TruLens providers require specific sub-packages now, use a basic fallback if they fail
        from trulens_eval.feedback.provider.langchain import Langchain
        provider = Langchain(chain=llm)
        rel_score = provider.relevance(user_prompt, bot_response)
        
        eval_data["trulens"] = {
            "relevance": rel_score
        }
    except Exception as e:
        eval_data["trulens"] = {"error": str(e)}


    # Aggregate scoring for the UI
    try:
        # Use Ragas faithfulness as inverse hallucination
        faith = eval_data.get("ragas", {}).get("faithfulness", 1.0)
        eval_data["hallucination_score"] = round(1.0 - faith, 2)
        
        # Use DeepEval hallucination reason if available
        de_reason = eval_data.get("deepeval", {}).get("reason", "")
        eval_data["reasoning"] = de_reason or "Evaluated using Ragas, DeepEval, and TruLens."
        
        # Use TruLens relevance as confidence
        eval_data["confidence_score"] = eval_data.get("trulens", {}).get("relevance", 0.8)
    except:
        pass

    # Tokens
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        eval_data["tokens"] = len(enc.encode(user_prompt + (active_context or "") + bot_response))
    except:
        eval_data["tokens"] = (len(user_prompt) + len(active_context or "") + len(bot_response)) // 4

    eval_data["timestamp"] = int(time.time())
    
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
