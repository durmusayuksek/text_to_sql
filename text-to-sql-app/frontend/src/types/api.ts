export interface HealthResponse {
  appName: string;
  status: "ok";
  environment: string;
}

export type ModuleId = string;

export interface TableDefinition {
  table_name: string;
  data_path: string;
  description: string;
  columns: ColumnDefinition[];
}

export interface ColumnDefinition {
  name: string;
  type: string;
  description: string;
  examples: string[];
  business_terms: string[];
}

export interface RelationshipDefinition {
  left_table: string;
  left_column: string;
  right_table: string;
  right_column: string;
  relationship_type: string;
  description: string;
}

export interface ModuleConfig {
  module_id: ModuleId;
  label: string;
  description: string;
  tables: TableDefinition[];
  relationships: RelationshipDefinition[];
  example_questions: string[];
  example_sql: string[];
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
