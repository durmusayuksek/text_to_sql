import type { AskResponse } from "../types/api";

interface AnswerPanelProps {
  answer: AskResponse | null;
  error: string | null;
  isLoading: boolean;
}

export function AnswerPanel({ answer, error, isLoading }: AnswerPanelProps) {
  if (isLoading) {
    return (
      <section
        className="rounded-[1.25rem] border border-white/80 border-t-[3px] border-t-[rgb(var(--brand-teal-rgb))] bg-white/90 p-5 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur sm:p-6"
        aria-live="polite"
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[rgb(var(--brand-teal-rgb))]">
              Response
            </p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950">
              Analyzing your question...
            </h2>
          </div>
          <div className="h-3 w-3 rounded-full bg-[rgb(var(--brand-teal-rgb))] shadow-[0_0_0_6px_rgba(var(--brand-teal-rgb),0.12)]" />
        </div>
        <div className="mt-6 space-y-3">
          <SkeletonBar className="w-full" />
          <SkeletonBar className="w-11/12" />
          <SkeletonBar className="w-4/5" />
          <SkeletonBar className="w-10/12" />
          <SkeletonBar className="w-7/12" />
        </div>
        <p className="mt-5 text-sm leading-6 text-slate-500">
          The backend is planning, generating SQL, validating it, and preparing the answer.
        </p>
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="rounded-[1.25rem] border border-rose-200 bg-white/90 p-5 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur sm:p-6"
        aria-labelledby="answer-error-heading"
      >
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-rose-700">
          Error
        </p>
        <h2 id="answer-error-heading" className="mt-1 text-xl font-semibold text-slate-950">
          The answer could not be generated
        </h2>
        <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {error}
        </p>
      </section>
    );
  }

  if (!answer) {
    return (
      <section className="rounded-[1.25rem] border border-dashed border-slate-300 bg-white/70 p-5 text-sm leading-6 text-slate-500 shadow-sm backdrop-blur sm:p-6">
        <div className="flex min-h-64 flex-col justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
              Response
            </p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950">
              Ready for a question
            </h2>
            <p className="mt-4 max-w-md">
              The business answer, key findings, assumptions, limitations, and debug details
              will appear here after you submit.
            </p>
          </div>
          <div className="mt-8 grid gap-2">
            <div className="h-2 w-3/4 rounded-full bg-slate-200" />
            <div className="h-2 w-1/2 rounded-full bg-slate-200" />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      className="rounded-[1.25rem] border border-white/80 border-t-[3px] border-t-[rgb(var(--brand-teal-rgb))] bg-white/90 p-5 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur sm:p-6"
      aria-labelledby="answer-panel-heading"
    >
      <div className="flex flex-col gap-1.5">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-[rgb(var(--brand-teal-rgb))]">
          Response
        </p>
        <h2 id="answer-panel-heading" className="text-xl font-semibold text-slate-950">
          Business answer
        </h2>
      </div>

      <p className="mt-5 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4 text-base leading-7 text-slate-800">
        {answer.answer}
      </p>

      {answer.key_findings.length > 0 ? (
        <div className="mt-5 rounded-2xl border border-[rgba(var(--brand-teal-rgb),0.16)] bg-[rgba(var(--brand-teal-rgb),0.06)] p-4">
          <p className="text-xs font-bold uppercase tracking-[0.12em] text-[rgb(var(--brand-teal-rgb))]">
            Key findings
          </p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-800">
            {answer.key_findings.map((finding) => (
              <li key={finding} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[rgb(var(--brand-teal-rgb))]" />
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {answer.assumptions.length > 0 ? (
        <InfoList title="Assumptions" items={answer.assumptions} />
      ) : null}

      {answer.limitations.length > 0 ? (
        <InfoList title="Limitations" items={answer.limitations} />
      ) : null}

      <details className="mt-5 rounded-2xl border border-slate-200 bg-white/80 p-4">
        <summary className="cursor-pointer text-xs font-bold uppercase tracking-[0.12em] text-slate-500 transition hover:text-slate-800">
          Debug
        </summary>
        <div className="mt-4 space-y-4">
          {answer.generated_sql_queries.map((query) => (
            <div key={query.query_id} className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
              <p className="text-sm font-semibold text-slate-900">{query.query_id}</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">{query.purpose}</p>
              <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-100">
                <code>{query.sql}</code>
              </pre>
            </div>
          ))}

          {answer.query_results ? (
            <div className="space-y-3">
              {answer.query_results.map((result) => (
                <div key={result.query_id} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
                    Rows for {result.query_id}
                  </p>
                  {result.warnings.length > 0 ? (
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-700">
                      {result.warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  ) : null}
                  <div className="mt-3 space-y-2">
                    {result.rows.map((row, index) => (
                      <div
                        key={`${result.query_id}-row-${index}`}
                        className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
                      >
                        {Object.entries(row)
                          .map(([key, value]) => `${key}: ${String(value)}`)
                          .join(" | ")}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm leading-6 text-slate-500">
              Raw rows are hidden. Enable backend debug query results to include them.
            </p>
          )}
        </div>
      </details>

      <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-200 pt-4 text-xs font-semibold text-slate-600">
        <span className="rounded-full bg-slate-100 px-3 py-1">
          Agent mode: {answer.query_agent_mode}
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1">
          Confidence: {answer.confidence}
        </span>
      </div>
    </section>
  );
}

interface InfoListProps {
  title: string;
  items: string[];
}

function InfoList({ title, items }: InfoListProps) {
  return (
    <div className="mt-4 rounded-2xl border border-slate-200 bg-white/80 p-4">
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
        {title}
      </p>
      <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-700">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

interface SkeletonBarProps {
  className: string;
}

function SkeletonBar({ className }: SkeletonBarProps) {
  return <div className={`skeleton-shimmer h-4 rounded-full ${className}`} />;
}
