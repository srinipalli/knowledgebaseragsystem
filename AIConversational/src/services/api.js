const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");

export async function askQuestion(question) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question })
    });
  } catch (error) {
    throw new Error(`Cannot reach API at ${API_BASE_URL}. Make sure LLMAPI is running.`);
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to fetch answer from API.");
  }

  return response.json();
}
