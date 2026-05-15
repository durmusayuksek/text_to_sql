import type { ModuleConfig } from "../types/api";

export const moduleConfigs: ModuleConfig[] = [
  {
    id: "pax_forecast",
    title: "Pax Forecast",
    description: "Ask forecasting questions about demand, occupancy, and passenger volume trends.",
    dataFocus: "Forecasting",
    accent: "teal",
  },
  {
    id: "special_cruise_profit",
    title: "Special Cruise / Entertainment Profit Calculation",
    description: "Explore revenue, cost, margin, and profitability scenarios for special cruise events.",
    dataFocus: "Profit analysis",
    accent: "indigo",
  },
  {
    id: "qa",
    title: "Questions / Answers",
    description: "Use a general analytical workspace for direct questions over prepared datasets.",
    dataFocus: "Operations Q&A",
    accent: "amber",
  },
];
