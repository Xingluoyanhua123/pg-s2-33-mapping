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
  const [courses, setCourses] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [command, setCommand] = useState("");
  const [message, setMessage] = useState("Ready.");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [conversationMode, setConversationMode] = useState(false);
  const [history, setHistory] = useState([
    { role: "assistant", text: "Hello. I am ready to help with course credit mapping." }
  ]);

  const recognitionRef = useRef(null);
  const conversationRef = useRef(false);
  const sessionId = useMemo(() => getSessionId(), []);

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
      speechSynthesis?.cancel();
    };
  }, []);

  function addHistory(role, text) {
    setHistory((items) => [...items, { role, text }]);
  }

  function speak(text, continueListening = false) {
    if (!("speechSynthesis" in window)) {
      if (continueListening && conversationRef.current) {
        setTimeout(startListening, 400);
      }
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-AU";
    utterance.rate = 0.98;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => {
      setSpeaking(false);
      if (continueListening && conversationRef.current) {
        setTimeout(startListening, 500);
      }
    };
    utterance.onerror = () => {
      setSpeaking(false);
      if (continueListening && conversationRef.current) {
        setTimeout(startListening, 500);
      }
    };

    window.speechSynthesis.speak(utterance);
  }

  async function runCommand(text = command, fromVoice = false) {
    const clean = text.trim();
    if (!clean) return;

    setCommand(clean);
    addHistory("user", clean);
    setMessage("Thinking...");

    try {
      const result = await sendVoiceCommand(clean, sessionId);
      setMessage(result.message);
      addHistory("assistant", result.message);
      await refresh();
      speak(result.message, fromVoice && conversationRef.current && result.should_continue);
    } catch (error) {
      const response = `Sorry, I could not reach the backend. ${error.message}`;
      setMessage(response);
      addHistory("assistant", response);
      speak(response, fromVoice && conversationRef.current);
    }
  }

  function startListening() {
    if (listening || speaking) return;

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
      setListening(false);
      const transcript = event.results[0][0].transcript.trim();
      setCommand(transcript);
      await runCommand(transcript, true);
    };

    recognition.onerror = (event) => {
      setListening(false);
      if (event.error === "no-speech" && conversationRef.current) {
        setMessage("No speech detected. Listening again...");
        setTimeout(startListening, 700);
        return;
      }
      if (event.error !== "aborted") {
        setMessage(`Speech recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
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
    setConversationMode(false);
    recognitionRef.current?.abort();
    window.speechSynthesis?.cancel();
    setListening(false);
    setSpeaking(false);
    setMessage("Conversation stopped.");
  }

  async function handleAdd(courseId) {
    const mapping = await createMapping(courseId);
    const response = `Mapping ready: ${mapping.source_course_code} to ${mapping.target_course_code}.`;
    setMessage(response);
    await refresh();
    speak(response);
  }

  async function handleDelete(mappingId) {
    await deleteMapping(mappingId);
    setMessage("Mapping deleted.");
    await refresh();
    speak("Mapping deleted.");
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">PG-S2-33 · Voice Prototype v2</p>
          <h1>Voice Course Credit Mapping</h1>
          <p className="subtitle">Speak naturally, confirm a mapping, and hear the result.</p>
        </div>
        <div className="status-pill">{conversationMode ? "Conversation ON" : "Conversation OFF"}</div>
      </header>

      <main className="grid">
        <section className="panel voice-panel">
          <div className="panel-heading">
            <div>
              <h2>Voice Assistant</h2>
              <p>Try “Map Database Systems”, then answer “Yes”.</p>
            </div>
            <strong>{speaking ? "🔊 Speaking" : listening ? "🎙 Listening" : "● Ready"}</strong>
          </div>

          <div className="conversation-buttons">
            {!conversationMode ? (
              <button className="primary-button" onClick={startConversation}>🎙 Start Conversation</button>
            ) : (
              <button className="stop-button" onClick={stopConversation}>■ Stop Conversation</button>
            )}
            <button className="secondary-button" onClick={startListening} disabled={listening || speaking}>Speak Once</button>
          </div>

          <div className="command-row">
            <input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Type a command, e.g. Map MATH101"
              onKeyDown={(e) => e.key === "Enter" && runCommand()}
            />
            <button className="primary-button" onClick={() => runCommand()}>Send</button>
          </div>

          <div className="message-box">{message}</div>
        </section>

        <section className="panel conversation-panel">
          <h2>Conversation</h2>
          <div className="chat-history">
            {history.map((item, index) => (
              <div key={index} className={`chat-message ${item.role === "user" ? "user-message" : "assistant-message"}`}>
                <strong>{item.role === "user" ? "You" : "Assistant"}</strong>
                <p>{item.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div><h2>Available Courses</h2><p>Prototype data.</p></div>
            <span className="count">{courses.length}</span>
          </div>
          <div className="course-list">
            {courses.map((course) => (
              <article className="course-card" key={course.id}>
                <div className="course-topline"><strong>{course.code}</strong><span>{course.units} units</span></div>
                <h3>{course.name}</h3>
                <p>{course.suggested_target_code} · {course.suggested_target_name}</p>
                <button className="primary-button" onClick={() => handleAdd(course.id)}>Add Mapping</button>
              </article>
            ))}
          </div>
        </section>

        <section className="panel mappings-panel">
          <div className="panel-heading">
            <div><h2>Current Mappings</h2><p>Created through button, text, or voice.</p></div>
            <span className="count">{mappings.length}</span>
          </div>
          {mappings.length === 0 ? (
            <div className="empty-state">No mappings yet.</div>
          ) : (
            <div className="mapping-table-wrap">
              <table>
                <thead><tr><th>Source</th><th>Target</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {mappings.map((m) => (
                    <tr key={m.id}>
                      <td><strong>{m.source_course_code}</strong><div>{m.source_course_name}</div></td>
                      <td><strong>{m.target_course_code}</strong><div>{m.target_course_name}</div></td>
                      <td><span className="decision">{m.decision}</span></td>
                      <td><button className="delete-button" onClick={() => handleDelete(m.id)}>Delete</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="panel architecture-panel">
          <h2>Voice Flow</h2>
          <div className="architecture-flow">
            <span>🎙 Microphone</span><b>→</b><span>Speech-to-Text</span><b>→</b><span>React</span><b>→</b>
            <span>FastAPI</span><b>→</b><span>Service</span><b>→</b><span>Repository</span><b>→</b><span>🔊 TTS</span>
          </div>
        </section>
      </main>
    </div>
  );
}
