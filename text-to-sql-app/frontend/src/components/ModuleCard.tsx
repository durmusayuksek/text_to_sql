import type { ModuleConfig, ModuleId } from "../types/api";

interface ModuleCardProps {
  module: ModuleConfig;
  selected: boolean;
  onSelect: (moduleId: ModuleId) => void;
}

type Accent = "amber" | "indigo" | "teal";

const accentClasses: Record<Accent, string> = {
  amber: "border-amber-300 bg-amber-50 text-amber-700",
  indigo: "border-indigo-300 bg-indigo-50 text-indigo-700",
  teal: "border-teal-300 bg-teal-50 text-teal-700",
};

const accentByModuleId: Record<ModuleId, keyof typeof accentClasses> = {
  pax_forecast: "teal",
  qa: "amber",
  special_cruise_profit: "indigo",
};

export function ModuleCard({ module, selected, onSelect }: ModuleCardProps) {
  return (
    <button
      className={`flex h-full min-h-48 flex-col rounded-lg border bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 ${
        selected ? "border-slate-900 ring-2 ring-slate-900" : "border-slate-200"
      }`}
      type="button"
      aria-pressed={selected}
      onClick={() => onSelect(module.module_id)}
    >
      <span
        className={`w-fit rounded-full border px-3 py-1 text-xs font-semibold ${accentClasses[accentByModuleId[module.module_id]]}`}
      >
        {module.data_path}
      </span>
      <span className="mt-4 text-lg font-semibold leading-6 text-slate-950">
        {module.label}
      </span>
      <span className="mt-3 text-sm leading-6 text-slate-600">{module.description}</span>
      <span className="mt-auto pt-5 text-sm font-medium text-slate-900">
        {selected ? "Selected" : "Select module"}
      </span>
    </button>
  );
}
