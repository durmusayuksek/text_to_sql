export interface HealthResponse {
  appName: string;
  status: "ok";
  environment: string;
}

export type ModuleId = string;

export interface TableDefinition {
  name: string;
  description: string;
  columns: string[];
}

export interface ModuleConfig {
  module_id: ModuleId;
  label: string;
  description: string;
  data_path: string;
  table_name: string;
  table_definitions: TableDefinition[];
  example_questions: string[];
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
