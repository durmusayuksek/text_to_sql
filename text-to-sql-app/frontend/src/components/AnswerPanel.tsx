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
        Your answer will appear here after submitting a question.
      </section>
    );
  }

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      aria-labelledby="answer-panel-heading"
    >
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-slate-500">Response</p>
        <h2 id="answer-panel-heading" className="text-xl font-semibold text-slate-950">
          Business answer
        </h2>
      </div>

      <p className="mt-5 text-base leading-7 text-slate-800">{answer.answer}</p>

      {answer.key_findings.length > 0 ? (
        <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Key findings
          </p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-800">
            {answer.key_findings.map((finding) => (
              <li key={finding}>{finding}</li>
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

      <details className="mt-5 rounded-md border border-slate-200 bg-white p-4">
        <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-500">
          Debug
        </summary>
        <div className="mt-4 space-y-4">
          {answer.generated_sql_queries.map((query) => (
            <div key={query.query_id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">{query.query_id}</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">{query.purpose}</p>
              <pre className="mt-3 overflow-x-auto text-sm leading-6 text-slate-800">
                <code>{query.sql}</code>
              </pre>
            </div>
          ))}

          {answer.query_results ? (
            <div className="space-y-3">
              {answer.query_results.map((result) => (
                <div key={result.query_id} className="rounded-md border border-slate-200 bg-white p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
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
                        className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
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

      <div className="mt-5 border-t border-slate-200 pt-4 text-xs text-slate-500">
        Agent mode: {answer.query_agent_mode}. Confidence: {answer.confidence}.
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
    <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
