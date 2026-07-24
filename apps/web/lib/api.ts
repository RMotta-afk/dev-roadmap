import { AnalyzeResponse, AgentProgressEvent, AnalyzeResult } from "@cv-analyzer/shared-types";

export async function submitAnalysis(formData: FormData): Promise<AnalyzeResponse> {
  const res = await fetch("/api/analyze", {
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
  onEvent: (event: AgentProgressEvent) => void,
  onError?: () => void
): { close: () => void } {
  const url = `/api/analyze/${id}/events`;
  const es = new EventSource(url, { withCredentials: true });
  let received = false;

  es.onmessage = (e) => {
    received = true;
    try {
      const data = JSON.parse(e.data) as AgentProgressEvent;
      onEvent(data);
    } catch {
      // ignore malformed events
    }
  };

  es.onerror = () => {
    // Connection error or stream closed. Only report an error if we haven't
    // received any data yet; otherwise the stream likely closed normally.
    es.close();
    if (!received && onError) {
      onError();
    }
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
