from flask import Flask, render_template, request, jsonify
from memory_manager import (
    save_selection_to_context,
    update_active_context,
    get_active_context_string,
    split_text_into_chunks
)
from llm_client import call_llm
from tests.evaluator import evaluate_response

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_prompt = data.get("prompt", "")
    config = data.get("config", {"mode": "simulate"})
    run_eval = config.get("evaluate", False)
    
    # Pre-prompt phase: Get active context
    active_context = get_active_context_string()
    
    # Call the LLM using our wrapper
    response_text = call_llm(user_prompt, active_context_string=active_context, config=config)
    
    # Split response into chunks so frontend can render them with indexes
    chunks = split_text_into_chunks(response_text)
    
    eval_metrics = None
    if run_eval:
        eval_metrics = evaluate_response(user_prompt, response_text, active_context, config)
    
    return jsonify({
        "response": response_text,
        "chunks": chunks,
        "active_context_used": active_context,
        "user_prompt": user_prompt,
        "evaluation": eval_metrics
    })

@app.route("/save_selection", methods=["POST"])
def save_selection():
    data = request.json
    selected_indexes = data.get("indexes", [])
    llm_response = data.get("response_text", "")
    user_prompt = data.get("user_prompt", "")
    
    block_id = save_selection_to_context(selected_indexes, llm_response, user_prompt)
    if block_id:
        return jsonify({"status": "success", "block_id": block_id})
    return jsonify({"status": "error", "message": "No chunks selected or valid."})

if __name__ == "__main__":
    app.run(debug=True, port=5005)
