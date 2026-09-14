import { useEffect, useMemo, useRef, useState } from "react";
import {
  createMapping,
  deleteMapping,
  getCourses,
  getMappings,
  sendVoiceCommand
} from "./api";

function getSessionId() {
  const saved = localStorage.getItem("voiceMappingSessionId");
  if (saved) return saved;

  const id = crypto.randomUUID
    ? crypto.randomUUID()
    : `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  localStorage.setItem("voiceMappingSessionId", id);
  return id;
}

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const historyRef = useRef(null);
  const inputRef = useRef(null);
  const launcherRef = useRef(null);
  const busyRef = useRef(false);
  const retryRef = useRef(null);
  const soundRef = useRef({ muted: false, volume: 1 });
  const [courses, setCourses] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [command, setCommand] = useState("");
  const [message, setMessage] = useState("Ready.");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [conversationMode, setConversationMode] = useState(false);
  const [isMuted, setIsMuted] = useState(() => {
  return localStorage.getItem("voiceMuted") === "true";
});

const [voiceVolume, setVoiceVolume] = useState(() => {
  const saved = localStorage.getItem("voiceVolume");
  const parsed = saved === null ? 1 : Number(saved);

  return Number.isFinite(parsed) && parsed >= 0 && parsed <= 1
    ? parsed
    : 1;
});
  const [history, setHistory] = useState([
    { role: "assistant", text: "Hello. I am ready to help with course credit mapping." }
  ]);

  soundRef.current = { muted: isMuted, volume: voiceVolume };
  useEffect(() => {
    if (chatOpen) {
      inputRef.current?.focus();
      if (historyRef.current) historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [chatOpen]);
  useEffect(() => {
    if (historyRef.current) historyRef.current.scrollTop = historyRef.current.scrollHeight;
  }, [history, busy]);
  const recognitionRef = useRef(null);
  const conversationRef = useRef(false);
  const sessionId = useMemo(() => getSessionId(), []);

  useEffect(() => {
  localStorage.setItem("voiceMuted", String(isMuted));
  localStorage.setItem("voiceVolume", String(voiceVolume));
}, [isMuted, voiceVolume]);

  async function refresh() {
    try {
      const [courseData, mappingData] = await Promise.all([getCourses(), getMappings()]);
      setCourses(courseData);
      setMappings(mappingData);
    } catch (error) {
      setMessage(`Backend error: ${error.message}`);
    }
  }

  useEffect(() => {
    refresh();
    return () => {
      conversationRef.current = false;
      recognitionRef.current?.abort();
      clearTimeout(retryRef.current);
      window.speechSynthesis?.cancel();
    };
  }, []);

  function addHistory(role, text) {
    setHistory((items) => [...items, { role, text }]);
  }

function speak(text, continueListening = false) {
  if (!("speechSynthesis" in window) || soundRef.current.muted) {
    setSpeaking(false);

    if (continueListening && conversationRef.current) {
      scheduleListening(400);
    }

    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-AU";
  utterance.rate = 0.98;
  utterance.volume = soundRef.current.volume;

  utterance.onstart = () => setSpeaking(true);

  utterance.onend = () => {
    setSpeaking(false);

    if (continueListening && conversationRef.current) {
      scheduleListening(500);
    }
  };

  utterance.onerror = () => {
    setSpeaking(false);

    if (continueListening && conversationRef.current) {
      scheduleListening(500);
    }
  };

  window.speechSynthesis.speak(utterance);
}

  async function runCommand(text = command, fromVoice = false) {
    const clean = text.trim();
    if (!clean || busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setCommand("");
    addHistory("user", clean);
    setMessage("Thinking...");

    try {
      const result = await sendVoiceCommand(clean, sessionId);
      setMessage(result.message);
      addHistory("assistant", result.message);
      await refresh();
      if (!fromVoice || conversationRef.current) speak(result.message, fromVoice && conversationRef.current && result.should_continue);
    } catch (error) {
      const response = `Sorry, I could not reach the backend. ${error.message}`;
      setMessage(response);
      addHistory("assistant", response);
      if (!fromVoice || conversationRef.current) speak(response, fromVoice && conversationRef.current);
    } finally { busyRef.current = false; setBusy(false); }
  }

  function scheduleListening(delay) {
    clearTimeout(retryRef.current);
    retryRef.current = setTimeout(() => {
      if (conversationRef.current) startListening();
    }, delay);
  }

  function startListening() {
    if (busyRef.current || recognitionRef.current || window.speechSynthesis?.speaking) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessage("Speech Recognition is not supported. Please use Chrome or Edge.");
      conversationRef.current = false;
      setConversationMode(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-AU";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
      setMessage("Listening...");
    };

    recognition.onresult = async (event) => {
      recognitionRef.current = null;
      setListening(false);
      const transcript = event.results[0][0].transcript.trim();
      setCommand(transcript);
      await runCommand(transcript, true);
    };

    recognition.onerror = (event) => {
      setListening(false);
      if (event.error === "no-speech" && conversationRef.current) {
        setMessage("No speech detected. Listening again...");
        scheduleListening(700);
        return;
      }
      if (event.error !== "aborted") {
        setMessage(`Speech recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => { if (recognitionRef.current === recognition) recognitionRef.current = null; setListening(false); };
    recognitionRef.current = recognition;
    try { recognition.start(); } catch (error) { recognitionRef.current = null; setListening(false); setMessage(error.message); }
  }

  function toggleMute() {
    setIsMuted((current) => {
      const next = !current;

      if (next) {
        window.speechSynthesis?.cancel();
        setSpeaking(false);
      }

      return next;
    });
  }

  function startConversation() {
    conversationRef.current = true;
    setConversationMode(true);
    const intro = "Conversation mode started. Tell me which course you want to map.";
    setMessage(intro);
    addHistory("assistant", intro);
    speak(intro, true);
  }

  function stopConversation() {
    conversationRef.current = false;
    clearTimeout(retryRef.current);
    setConversationMode(false);
    recognitionRef.current?.abort();
    recognitionRef.current = null;
    window.speechSynthesis?.cancel();
    setListening(false);
    setSpeaking(false);
    setMessage("Conversation stopped.");
  }

  async function handleAdd(courseId) {
    try {
      const mapping = await createMapping(courseId);
      setMessage(`Mapping ready: ${mapping.source_course_code} to ${mapping.target_course_code}.`);
      await refresh();
    } catch (error) { setMessage(error.message); }
  }

  async function handleDelete(mappingId) {
    try { await deleteMapping(mappingId); await refresh(); setMessage("Mapping deleted."); }
    catch (error) { setMessage(error.message); }
  }

  function closeChat() {
    stopConversation();
    setChatOpen(false);
    launcherRef.current?.focus();
  }

  const visibleCourses = courses.filter(course =>
    `${course.code} ${course.name}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page">
      <nav className="topbar"><span className="brand"><span className="brand-mark">✦</span> Course Mapping</span><span className="prototype-tag">PG-S2-33 · Prototype</span></nav>
      <header className="hero">
        <div><p className="eyebrow">YOUR COURSE WORKSPACE</p><h1>Explore your courses.<br /><span>Plan your next step.</span></h1>
          <p className="subtitle">Browse course information and review potential credit mappings.<br />Need a hand? Ask the assistant in the bottom-right corner.</p></div>
        <div className="overview"><strong>{courses.length}</strong><span>available courses</span><hr /><strong>{mappings.length}</strong><span>current mappings</span></div>
      </header>
      <main className="grid">
        <section className="panel courses-panel">
          <div className="panel-heading"><div><h2>Available Courses</h2><p>Explore the course catalogue.</p></div><span className="count">{visibleCourses.length}</span></div>
          <label className="search-label">Search courses<input className="course-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by course name or code…" /></label>
          <div className="course-list">
            {visibleCourses.map(course => (
              <article className="course-card" key={course.id}>
                <div className="course-topline"><strong>{course.code}</strong><span>{course.units} units</span></div>
                <h3>{course.name}</h3>
                <p className="target-label">Suggested target</p>
                <p>{course.suggested_target_code === "PENDING" ? "Awaiting university review" : `${course.suggested_target_code} · ${course.suggested_target_name}`}</p>
                <div className="course-actions"><button className="secondary-button" onClick={() => { setCommand(`What are the main learning outcomes of ${course.code}?`); setChatOpen(true); inputRef.current?.focus(); }}>Ask assistant ↗</button>
                  <button className="primary-button" disabled={course.suggested_target_code === "PENDING"} onClick={() => handleAdd(course.id)}>{course.suggested_target_code === "PENDING" ? "Review pending" : "Add Mapping"}</button></div>
              </article>
            ))}
          </div>
          {visibleCourses.length === 0 && <p className="empty-state">{courses.length ? "No courses match your search." : "No courses loaded. Check that the backend is running."}</p>}
        </section>
        <section className="panel mappings-panel">
          <div className="panel-heading"><div><h2>Current Mappings</h2><p>Suggested mappings require university review.</p></div><span className="count">{mappings.length}</span></div>
          {mappings.length === 0 ? <div className="empty-state">Your mappings will appear here once added.</div> :
            <div className="mapping-table-wrap"><table><thead><tr><th>Source</th><th>Target</th><th>Status</th><th>Action</th></tr></thead><tbody>
              {mappings.map(m => <tr key={m.id}><td><strong>{m.source_course_code}</strong><div>{m.source_course_name}</div></td><td><strong>{m.target_course_code}</strong><div>{m.target_course_name}</div></td><td><span className="decision">{m.decision}</span></td><td><button className="delete-button" onClick={() => handleDelete(m.id)}>Delete</button></td></tr>)}
            </tbody></table></div>}
        </section>
      </main>
      <footer className="page-footer"><span>Course credit mapping · Student prototype</span><span role="status">{chatOpen ? "Assistant open" : message}</span></footer>
      <button ref={launcherRef} className="chat-launcher" aria-label={chatOpen ? "Close assistant" : "Open assistant"} aria-expanded={chatOpen} aria-controls="mapping-chat" onClick={() => chatOpen ? closeChat() : setChatOpen(true)}><span aria-hidden="true">{chatOpen ? "×" : "✦"}</span>{chatOpen ? "Close" : "Ask AI Helper"}</button>
      {chatOpen && <section id="mapping-chat" className="chat-widget" role="dialog" aria-modal="false" aria-labelledby="chat-title" onKeyDown={e => { if (e.key === "Escape") closeChat(); }}>
        <header className="chat-header"><span className="helper-icon" aria-hidden="true">✦</span><div><h2 id="chat-title">Adelaide Mapping AI Helper</h2><p>Course mapping support</p></div><button className="minimize" aria-label="Minimize assistant" onClick={closeChat}>−</button></header>
        <div ref={historyRef} className="chat-history" role="log" aria-label="Conversation" aria-live="polite">
          {history.map((item, index) => <div key={index} className={`chat-message ${item.role === "user" ? "user-message" : "assistant-message"}`}><span className="speaker-label">{item.role === "user" ? "You" : "Assistant"}</span><p>{item.text}</p></div>)}
          {busy && <div className="chat-message assistant-message typing">Thinking…</div>}
        </div>
        <div className="chat-controls">
          <div className="conversation-buttons"><button className="secondary-button" disabled={busy || listening || speaking} onClick={startListening}>🎙 Speak</button><button className={conversationMode ? "stop-button" : "secondary-button"} disabled={!conversationMode && busy} onClick={conversationMode ? stopConversation : startConversation}>{conversationMode ? "Stop conversation" : "Start conversation"}</button><button className="secondary-button" onClick={toggleMute} aria-pressed={isMuted}>{isMuted ? "Unmute" : "Mute"}</button></div>
          <label className="volume-control"><span>Volume</span><input type="range" min="0" max="100" step="5" value={Math.round(voiceVolume * 100)} disabled={isMuted} onChange={e => setVoiceVolume(Number(e.target.value) / 100)} /><span>{isMuted ? 0 : Math.round(voiceVolume * 100)}%</span></label>
          <p className="chat-status" role="status">{busy ? "Waiting for an answer…" : speaking ? "Speaking…" : listening ? "Listening…" : message === "Ready." ? "Type a question or use your microphone." : message}</p>
          <form className="command-row" onSubmit={e => { e.preventDefault(); runCommand(); }}><input ref={inputRef} aria-label="Message the assistant" value={command} onChange={e => setCommand(e.target.value)} placeholder="Ask about a course or mapping…" /><button aria-label="Send message" className="send-button" disabled={busy || !command.trim()} type="submit">➤</button></form>
        </div>
      </section>}
    </div>
  );
}
