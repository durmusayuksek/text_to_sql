import type { FormEvent } from "react";

interface QuestionPanelProps {
  question: string;
  error: string | null;
  isSubmitting: boolean;
  onQuestionChange: (question: string) => void;
  onSubmit: () => void;
}

export function QuestionPanel({
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
      className="rounded-[1.25rem] border border-white/80 border-t-[3px] border-t-[rgb(var(--brand-teal-rgb))] bg-white/90 p-5 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur sm:p-6"
      aria-labelledby="question-panel-heading"
    >
      <div className="flex flex-col gap-1.5">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-[rgb(var(--brand-teal-rgb))]">
          Question
        </p>
        <h2 id="question-panel-heading" className="text-2xl font-semibold text-slate-950">
          Ask a business question
        </h2>
        <p className="text-sm leading-6 text-slate-500">
          Use route, market, date, pax, and revenue wording naturally.
        </p>
      </div>

      <form className="mt-6" onSubmit={handleSubmit}>
        <label htmlFor="question" className="text-sm font-semibold text-slate-700">
          Natural-language question
        </label>
        <textarea
          id="question"
          className="mt-2 min-h-40 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3.5 text-base leading-7 text-slate-950 shadow-inner outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-[rgb(var(--brand-teal-rgb))] focus:bg-white focus:ring-4 focus:ring-[rgba(var(--brand-teal-rgb),0.12)] disabled:cursor-not-allowed disabled:opacity-70"
          placeholder="Example: Tell me the number of pax on HEL-STO for departure month April 2026."
          value={question}
          disabled={isSubmitting}
          onChange={(event) => onQuestionChange(event.target.value)}
        />

        {error ? (
          <div className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            className="inline-flex min-h-12 w-full items-center justify-center rounded-2xl bg-[rgb(var(--brand-teal-rgb))] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-[rgba(var(--brand-teal-rgb),0.18)] transition hover:-translate-y-0.5 hover:bg-[rgb(var(--brand-teal-hover-rgb))] hover:shadow-xl hover:shadow-[rgba(var(--brand-teal-rgb),0.24)] active:translate-y-0 active:bg-[rgb(var(--brand-teal-rgb))] disabled:translate-y-0 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none sm:w-auto"
            type="submit"
            disabled={isSubmitting || question.trim().length === 0}
          >
            {isSubmitting ? (
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-white" />
                Generating answer...
              </span>
            ) : (
              "Submit question"
            )}
          </button>
          <p className="text-sm leading-6 text-slate-500">
            The backend validates SQL before running it.
          </p>
        </div>
      </form>
    </section>
  );
}
