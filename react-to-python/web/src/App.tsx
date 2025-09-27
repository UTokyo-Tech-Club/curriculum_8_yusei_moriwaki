import React, { useState, useEffect } from 'react';

type Chat = {
  id: number;
  question: string;
  answer: string;
  created_at: string;
};

function App() {
  const [question, setQuestion] = useState<string>("");
  const [chats, setChats] = useState<Chat[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await fetch("http://localhost:8000/chats");
        if (!response.ok) {
          throw new Error(`GET /chats failed: ${response.status}`);
        }
        const data = await response.json();
        setChats(data);
      } catch (err: any) {
        setError(err.message);
      }
    };
    fetchChats();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!question.trim()) {
      setError("Please enter a question");
      return;
    }
    if (question.length > 100) {
      setError("Question must be less than 100 characters");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) {
        throw new Error(`POST /chat failed: ${response.status}`);
      }
      const data = await response.json();
      setChats([...chats, data]);
      setQuestion("");
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div style={{
      maxWidth: "600px",
      margin: "2rem auto",
      padding: "1rem",
      backgroundColor: "#fff",
      borderRadius: "8px",
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
    }}>
      <h1 style={{ textAlign: "center" }}>Chat with GPT-4o</h1>

      <form onSubmit={handleSubmit} style={{ display: "flex", marginBottom: "1rem" }}>
        <input 
          type="text" 
          value={question} 
          onChange={(e) => setQuestion(e.target.value)} 
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Ask anything..."
          style={{
            flex: 1,
            padding: "0.75rem 1rem",
            border: "1px solid #ccc",
            borderRadius: "25px",
            marginRight: "0.5rem",
            fontSize: "1rem",
            outline: "none"
          }}
        />
        <button 
          type="submit"
          style={{
            padding: "0.75rem 1.5rem",
            border: "none",
            backgroundColor: "#2563eb",
            color: "white",
            borderRadius: "25px",
            cursor: "pointer",
            fontSize: "1rem",
            fontWeight: "500"
          }}
        >
          Submit
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div>
        {chats.map((chat) => (
          <div key={chat.id} style={{ marginBottom: "1rem" }}>
            <div style={{
              backgroundColor: "#2563eb",
              color: "white",
              padding: "0.75rem 1rem",
              borderRadius: "20px",
              maxWidth: "80%",
              marginLeft: "auto",
              marginBottom: "0.5rem"
            }}>
              <strong>You:</strong> {chat.question}
            </div>
            <div style={{
              backgroundColor: "#f1f1f1",
              padding: "0.75rem 1rem",
              borderRadius: "20px",
              maxWidth: "80%",
              marginRight: "auto"
            }}>
              <strong>GPT:</strong> {chat.answer}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;