export interface HealthResponse {
  appName: string;
  status: "ok";
  environment: string;
}

export interface AskRequest {
  question: string;
}

export interface GeneratedSqlQuery {
  query_id: string;
  purpose: string;
  sql: string;
}

export interface QueryResult {
  query_id: string;
  purpose: string;
  sql: string;
  rows: Array<Record<string, string | number | boolean | null>>;
}

export interface AskResponse {
  answer: string;
  key_findings: string[];
  assumptions: string[];
  limitations: string[];
  confidence: "high" | "medium" | "low";
  generated_sql_queries: GeneratedSqlQuery[];
  query_results: QueryResult[] | null;
  query_agent_mode: "mock" | "openai";
}
