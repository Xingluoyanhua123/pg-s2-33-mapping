const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const getCourses = () => request("/api/courses");
export const getMappings = () => request("/api/mappings");

export function createMapping(sourceCourseId) {
  return request("/api/mappings", {
    method: "POST",
    body: JSON.stringify({ source_course_id: sourceCourseId })
  });
}

export function deleteMapping(mappingId) {
  return request(`/api/mappings/${mappingId}`, { method: "DELETE" });
}

export function sendVoiceCommand(text, sessionId) {
  return request("/api/voice-command", {
    method: "POST",
    body: JSON.stringify({ text, session_id: sessionId })
  });
}
