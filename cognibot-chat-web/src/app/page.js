'use client';
import { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { Send, Settings, Check, X, BookmarkPlus, Loader2, Sparkles, Trash2, Database } from 'lucide-react';

const API_BASE = "http://127.0.0.1:5005";

const Message = ({ msg, onSnippetSaved }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [selectedText, setSelectedText] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    if (msg.role !== 'bot') return;

    const handleMouseUp = (e) => {
      const selection = window.getSelection();
      const text = selection.toString().trim();

      if (text && contentRef.current && contentRef.current.contains(selection.anchorNode)) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        setSelectedText(text);
        setTooltipPos({
          x: rect.left + rect.width / 2,
          y: rect.top - 10
        });
        setShowTooltip(true);
      } else if (!e.target.closest('.selection-tooltip')) {
        setShowTooltip(false);
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    return () => document.removeEventListener('mouseup', handleMouseUp);
  }, [msg.role]);

  const handleSaveSelection = async () => {
    if (!selectedText) return;
    setIsSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/core/context/save_selection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_text: selectedText,
          user_prompt: msg.userPrompt
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        onSnippetSaved({ text: selectedText, chunk_id: data.chunk_id, block_id: data.block_id });
        setShowTooltip(false);
        window.getSelection().removeAllRanges();
      } else {
        alert("Failed to save selection.");
      }
    } catch (err) {
      console.error(err);
      alert("Error contacting server.");
    } finally {
      setIsSaving(false);
    }
  };

  if (msg.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }} className="animate-fade-in">
        <div style={{ background: 'var(--accent-color)', padding: '12px 16px', borderRadius: '16px 16px 0 16px', maxWidth: '80%' }}>
          {msg.content}
        </div>
      </div>
    );
  }

  const rawMarkup = DOMPurify.sanitize(marked.parse(msg.responseText || ""));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', marginBottom: '32px', maxWidth: '85%' }} className="animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        <Sparkles size={16} color="var(--accent-color)" />
        <span style={{ fontWeight: 500 }}>Cognibot</span>
      </div>

      <div style={{ position: 'relative' }}>
        <div 
          ref={contentRef}
          className="markdown-body"
          style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '0 16px 16px 16px', border: '1px solid var(--border-color)' }}
          dangerouslySetInnerHTML={{ __html: rawMarkup }}
        />

        {showTooltip && (
          <div 
            className="selection-tooltip"
            style={{
              position: 'fixed', left: tooltipPos.x, top: tooltipPos.y,
              transform: 'translate(-50%, -100%)', background: 'var(--accent-color)',
              color: 'white', padding: '6px 12px', borderRadius: '8px',
              display: 'flex', alignItems: 'center', gap: '6px',
              cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              zIndex: 1000, fontSize: '0.85rem', fontWeight: 500
            }}
            onClick={handleSaveSelection}
          >
            {isSaving ? <Loader2 size={14} className="animate-spin" /> : <BookmarkPlus size={14} />}
            {isSaving ? "Saving..." : "Save Selection"}
          </div>
        )}
      </div>
    </div>
  );
};

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [allSavedSnippets, setAllSavedSnippets] = useState([]);
  
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const prompt = input.trim();
    
    setMessages(prev => [...prev, { role: 'user', content: prompt }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, config: { evaluate: false } })
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, {
        role: 'bot',
        responseText: data.response,
        userPrompt: data.user_prompt || prompt,
        activeContext: data.active_context_used,
        evaluation: data.evaluation
      }]);
    } catch (e) {
      alert("Error connecting to backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSnippet = async (chunkId, blockId, index) => {
    try {
      await fetch(`http://127.0.0.1:5007/api/blocks/${blockId}/chunks/${chunkId}`, { method: 'DELETE' });
      setAllSavedSnippets(prev => prev.filter((_, i) => i !== index));
    } catch (e) {
      console.error(e);
      alert("Failed to delete snippet.");
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      
      {/* LEFT SIDEBAR: Memory Context */}
      <aside style={{ width: '320px', borderRight: '1px solid var(--border-color)', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Database size={20} color="var(--accent-color)" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Memory Context</h2>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          {allSavedSnippets.length === 0 ? (
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center', marginTop: '40px' }}>
              <p>No context saved yet.</p>
              <p style={{ marginTop: '8px', opacity: 0.7 }}>Highlight text in the chat to save snippets here.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {allSavedSnippets.map((s, i) => (
                <div key={i} className="animate-fade-in" style={{ background: 'var(--bg-tertiary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.85rem', fontStyle: 'italic', marginBottom: '8px', color: 'var(--text-primary)' }}>
                    "{s.text}"
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button 
                      onClick={() => handleDeleteSnippet(s.chunk_id, s.block_id, i)}
                      style={{ background: 'none', border: 'none', color: 'var(--danger-color)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', opacity: 0.8 }}
                    >
                      <Trash2 size={14} /> Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* RIGHT MAIN: Chat Interface */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
        <header style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)' }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Cognitive Chatbot</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Chat with context-aware AI</p>
          </div>
        </header>

        <main style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {messages.length === 0 && (
            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              <Sparkles size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
              <h2 style={{ fontWeight: 500, marginBottom: '8px' }}>Start a conversation</h2>
              <p style={{ fontSize: '0.9rem' }}>Highlight any part of my response to save it to your contextual memory.</p>
            </div>
          )}

          {messages.map((msg, i) => <Message key={i} msg={msg} onSnippetSaved={(s) => setAllSavedSnippets(prev => [...prev, s])} />)}
          
          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--text-secondary)' }}>
              <Loader2 size={18} className="animate-spin" />
              <span style={{ fontSize: '0.9rem' }}>Thinking...</span>
            </div>
          )}
          <div ref={bottomRef} />
        </main>

        <footer style={{ padding: '24px', borderTop: '1px solid var(--border-color)', background: 'var(--bg-primary)' }}>
          <div style={{ display: 'flex', gap: '12px', position: 'relative' }}>
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question..."
              style={{ 
                flex: 1, padding: '16px 20px', borderRadius: '12px', 
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', 
                color: 'white', fontSize: '1rem', outline: 'none'
              }}
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              style={{ 
                background: 'var(--accent-color)', color: 'white', border: 'none', 
                borderRadius: '12px', padding: '0 24px', cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
                opacity: input.trim() && !isLoading ? 1 : 0.5,
                display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.2s'
              }}
            >
              <Send size={20} />
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
