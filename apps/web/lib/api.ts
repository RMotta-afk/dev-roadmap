import { AnalyzeResponse, AgentProgressEvent, AnalyzeResult } from "@cv-analyzer/shared-types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export async function submitAnalysis(formData: FormData): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Analysis submission failed: ${res.status} ${text}`);
  }

  return res.json();
}

export function subscribeToAnalysis(
  id: string,
  onEvent: (event: AgentProgressEvent) => void
): { close: () => void } {
  const url = `${API_BASE_URL}/analyze/${id}/events`;
  const es = new EventSource(url, { withCredentials: true });

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data) as AgentProgressEvent;
      onEvent(data);
    } catch {
      // ignore malformed events
    }
  };

  es.onerror = () => {
    // Connection error or stream closed
    es.close();
  };

  return {
    close: () => es.close(),
  };
}

export function isFinalEvent(event: AgentProgressEvent): event is AgentProgressEvent & { payload: AnalyzeResult } {
  return (
    event.status === "completed" &&
    event.payload !== undefined &&
    typeof event.payload === "object" &&
    event.payload !== null &&
    "level_resume" in event.payload &&
    "compatibility_score" in event.payload &&
    "personalized_roadmap" in event.payload
  );
}
