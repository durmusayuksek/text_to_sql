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
  data_focus: string;
  accent: "teal" | "indigo" | "amber";
}

export interface AskRequest {
  module_id: ModuleId;
  question: string;
}

export interface AskResponse {
  answer: string;
  sql: string;
  explanation: string;
  data: Array<Record<string, string | number | boolean | null>>;
  module_id: ModuleId;
}
