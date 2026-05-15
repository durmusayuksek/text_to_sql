import type { FormEvent } from "react";
import type { ModuleConfig } from "../types/api";

interface QuestionPanelProps {
  module: ModuleConfig;
  question: string;
  error: string | null;
  isSubmitting: boolean;
  onQuestionChange: (question: string) => void;
  onSubmit: () => void;
}

export function QuestionPanel({
  module,
  question,
  error,
  isSubmitting,
  onQuestionChange,
  onSubmit,
}: QuestionPanelProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      aria-labelledby="question-panel-heading"
    >
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-slate-500">Selected module</p>
        <h2 id="question-panel-heading" className="text-2xl font-semibold text-slate-950">
          {module.label}
        </h2>
      </div>

      <form className="mt-5" onSubmit={handleSubmit}>
        <label htmlFor="question" className="text-sm font-medium text-slate-700">
          Natural-language question
        </label>
        <textarea
          id="question"
          className="mt-2 min-h-36 w-full resize-y rounded-lg border border-slate-300 bg-white px-4 py-3 text-base leading-7 text-slate-950 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900"
          placeholder="Example: Which sailings are forecast to exceed capacity targets next month?"
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
        />

        {error ? (
          <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            className="inline-flex min-h-11 w-full items-center justify-center rounded-md bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-auto"
            type="submit"
            disabled={isSubmitting || question.trim().length === 0}
          >
            {isSubmitting ? "Generating answer..." : "Submit question"}
          </button>
          <p className="text-sm text-slate-500">
            Mocked API behavior is active for this version.
          </p>
        </div>
      </form>
    </section>
  );
}
