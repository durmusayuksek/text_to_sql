import type { AskRequest, AskResponse, HealthResponse } from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealthStatus(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Backend health check failed");
  }

  return response.json();
}

const mockedAnswers: Record<AskRequest["moduleId"], Omit<AskResponse, "question" | "generatedAt">> = {
  pax_forecast: {
    moduleId: "pax_forecast",
    summary:
      "Passenger demand is expected to remain above the baseline, with the strongest lift coming from weekend departures and shoulder-season bookings.",
    details: [
      "Forecast confidence is strongest for near-term sailings where booking pace is already visible.",
      "Capacity planning should prioritize high-demand departure windows before adding broad inventory changes.",
      "A useful next query would compare actual pickup against forecast by route and departure month.",
    ],
  },
  special_cruise_profit: {
    moduleId: "special_cruise_profit",
    summary:
      "The mocked profit view suggests a positive contribution margin if entertainment costs stay within the planned budget band.",
    details: [
      "Revenue sensitivity is mostly driven by ticket mix, onboard spend, and premium package attachment.",
      "Cost pressure should be monitored around staffing, artist fees, and venue setup.",
      "A useful next query would model break-even attendance under conservative spend assumptions.",
    ],
  },
  qa: {
    moduleId: "qa",
    summary:
      "The current answer indicates a clear operational signal, but the final interpretation will depend on the selected dataset and validated SQL path.",
    details: [
      "The mocked workflow is ready for module-specific routing without connecting to an LLM yet.",
      "Future responses should include the validated SQL, source tables, and confidence notes.",
      "A useful next query would ask for a ranked comparison with a specific date range.",
    ],
  },
};

export async function askQuestion(request: AskRequest): Promise<AskResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 900));

  if (request.question.toLowerCase().includes("error")) {
    throw new Error("Mocked request failed. Try a different question.");
  }

  return {
    ...mockedAnswers[request.moduleId],
    question: request.question,
    generatedAt: new Date().toISOString(),
  };
}
