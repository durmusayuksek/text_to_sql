import type { ModuleConfig, ModuleId } from "../types/api";
import { ModuleCard } from "./ModuleCard";

interface ModuleSelectorProps {
  modules: ModuleConfig[];
  selectedModuleId: ModuleId;
  onSelect: (moduleId: ModuleId) => void;
}

export function ModuleSelector({
  modules,
  selectedModuleId,
  onSelect,
}: ModuleSelectorProps) {
  return (
    <section aria-labelledby="module-selector-heading">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 id="module-selector-heading" className="text-xl font-semibold text-slate-950">
            Select a module
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Choose the business area that should interpret the question.
          </p>
        </div>
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        {modules.map((module) => (
          <ModuleCard
            key={module.id}
            module={module}
            selected={module.id === selectedModuleId}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}
