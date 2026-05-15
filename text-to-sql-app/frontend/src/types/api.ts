export interface HealthResponse {
  appName: string;
  status: "ok";
  environment: string;
}

export type ModuleId = "pax_forecast" | "special_cruise_profit" | "qa";

export interface ModuleConfig {
  id: ModuleId;
  title: string;
  description: string;
  dataFocus: string;
  accent: "teal" | "indigo" | "amber";
}

export interface AskRequest {
  moduleId: ModuleId;
  question: string;
}

export interface AskResponse {
  moduleId: ModuleId;
  question: string;
  summary: string;
  details: string[];
  generatedAt: string;
}
