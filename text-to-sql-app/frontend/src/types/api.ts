export interface HealthResponse {
  appName: string;
  status: "ok";
  environment: string;
}

export interface AskRequest {
  question: string;
}

export interface AskResponse {
  answer: string;
  sql: string;
  explanation: string;
  data: Array<Record<string, string | number | boolean | null>>;
  query_agent_mode: "mock" | "openai";
}
