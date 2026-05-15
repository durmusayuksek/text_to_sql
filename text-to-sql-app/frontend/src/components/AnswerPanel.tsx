import type { AskResponse } from "../types/api";

interface AnswerPanelProps {
  answer: AskResponse | null;
  isLoading: boolean;
}

export function AnswerPanel({ answer, isLoading }: AnswerPanelProps) {
  if (isLoading) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="h-5 w-32 rounded bg-slate-200" />
        <div className="mt-5 space-y-3">
          <div className="h-4 w-full rounded bg-slate-100" />
          <div className="h-4 w-11/12 rounded bg-slate-100" />
          <div className="h-4 w-4/5 rounded bg-slate-100" />
        </div>
      </section>
    );
  }

  if (!answer) {
    return (
      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-5 text-sm leading-6 text-slate-500">
        Your mocked answer will appear here after submitting a question.
      </section>
    );
  }

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      aria-labelledby="answer-panel-heading"
    >
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-slate-500">Mocked response</p>
        <h2 id="answer-panel-heading" className="text-xl font-semibold text-slate-950">
          Business answer
        </h2>
      </div>

      <p className="mt-5 text-base leading-7 text-slate-800">{answer.answer}</p>

      <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Mocked SQL
        </p>
        <pre className="mt-3 overflow-x-auto text-sm leading-6 text-slate-800">
          <code>{answer.sql}</code>
        </pre>
      </div>

      <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Explanation
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{answer.explanation}</p>
      </div>

      <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Sample data
        </p>
        <div className="mt-3 space-y-2">
          {answer.data.map((row, index) => (
            <div
              key={`${answer.module_id}-${index}`}
              className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
            >
              {Object.entries(row)
                .map(([key, value]) => `${key}: ${String(value)}`)
                .join(" | ")}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-5 border-t border-slate-200 pt-4 text-xs text-slate-500">
        Response served by the mocked backend contract for {answer.module_id}.
      </div>
    </section>
  );
}
