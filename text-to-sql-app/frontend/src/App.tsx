import { useEffect, useMemo, useState } from "react";
import { askQuestion, getModules } from "./api/client";
import { AnswerPanel } from "./components/AnswerPanel";
import { ModuleSelector } from "./components/ModuleSelector";
import { QuestionPanel } from "./components/QuestionPanel";
import type { AskResponse, ModuleConfig, ModuleId } from "./types/api";

type SubmitState = "idle" | "loading" | "success" | "error";
type ModuleLoadState = "idle" | "loading" | "success" | "error";

export function App() {
  const [modules, setModules] = useState<ModuleConfig[]>([]);
  const [selectedModuleId, setSelectedModuleId] = useState<ModuleId>("pax_forecast");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [moduleLoadState, setModuleLoadState] = useState<ModuleLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [moduleError, setModuleError] = useState<string | null>(null);

  const selectedModule = useMemo(
    () => modules.find((module) => module.module_id === selectedModuleId) ?? modules[0] ?? null,
    [modules, selectedModuleId],
  );

  useEffect(() => {
    let isMounted = true;

    async function loadModules() {
      setModuleLoadState("loading");
      setModuleError(null);

      try {
        const loadedModules = await getModules();

        if (isMounted) {
          setModules(loadedModules);
          setSelectedModuleId(loadedModules[0]?.module_id ?? "pax_forecast");
          setModuleLoadState("success");
        }
      } catch (caughtError) {
        const message =
          caughtError instanceof Error ? caughtError.message : "Unable to load modules.";

        if (isMounted) {
          setModuleError(message);
          setModuleLoadState("error");
        }
      }
    }

    void loadModules();

    return () => {
      isMounted = false;
    };
  }, []);

  function handleModuleSelect(moduleId: ModuleId) {
    setSelectedModuleId(moduleId);
    setError(null);
    setAnswer(null);
  }

  async function handleSubmit() {
    if (!selectedModule) {
      setError("Select a module before submitting.");
      setSubmitState("error");
      return;
    }

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setError("Enter a question before submitting.");
      setSubmitState("error");
      return;
    }

    setSubmitState("loading");
    setError(null);

    try {
      const [response] = await Promise.all([
        askQuestion({
          module_id: selectedModule.module_id,
          question: trimmedQuestion,
        }),
        waitForMinimumLoadingState(),
      ]);

      setAnswer(response);
      setSubmitState("success");
    } catch (caughtError) {
      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "Something went wrong while generating the answer.";

      setError(message);
      setAnswer(null);
      setSubmitState("error");
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-10 lg:px-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
                Text-to-SQL workspace
              </p>
              <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-normal text-slate-950 sm:text-5xl">
                Ask business questions across operational modules.
              </h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
                Select a module, enter a natural-language question, and review a
                mocked business-style answer. SQL generation and LLM routing are
                intentionally not connected yet.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
              <div className="min-w-20">
                <p className="text-2xl font-semibold text-slate-950">{modules.length || 3}</p>
                <p className="text-xs font-medium text-slate-500">Modules</p>
              </div>
              <div className="min-w-20">
                <p className="text-2xl font-semibold text-slate-950">0</p>
                <p className="text-xs font-medium text-slate-500">SQL calls</p>
              </div>
              <div className="min-w-20">
                <p className="text-2xl font-semibold text-slate-950">Mock</p>
                <p className="text-xs font-medium text-slate-500">Mode</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto grid w-full max-w-7xl gap-6 px-6 py-8 lg:px-8">
        {moduleError ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {moduleError}
          </div>
        ) : null}

        {moduleLoadState === "loading" ? (
          <div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-500 shadow-sm">
            Loading modules from backend...
          </div>
        ) : null}

        <ModuleSelector
          modules={modules}
          selectedModuleId={selectedModule?.module_id ?? selectedModuleId}
          onSelect={handleModuleSelect}
        />

        {selectedModule ? (
          <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(340px,0.8fr)]">
            <QuestionPanel
              module={selectedModule}
              question={question}
              error={error}
              isSubmitting={submitState === "loading"}
              onQuestionChange={setQuestion}
              onSubmit={handleSubmit}
            />
            <AnswerPanel answer={answer} isLoading={submitState === "loading"} />
          </section>
        ) : null}
      </div>
    </main>
  );
}

function waitForMinimumLoadingState(): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, 700));
}

export default App;
