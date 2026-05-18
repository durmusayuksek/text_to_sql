import { useState } from "react";
import { askQuestion } from "./api/client";
import { AnswerPanel } from "./components/AnswerPanel";
import { HealthStatus } from "./components/HealthStatus";
import { QuestionPanel } from "./components/QuestionPanel";
import tallinkSiljaLogo from "./assets/tallink-silja-line-logo.png";
import type { AskResponse } from "./types/api";

type SubmitState = "idle" | "loading" | "success" | "error";

export function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(var(--brand-teal-rgb),0.12),_transparent_34rem),linear-gradient(135deg,_#f8fafc_0%,_#eef2ff_48%,_#f8fafc_100%)] text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="overflow-hidden rounded-[1.25rem] border border-white/80 bg-white/85 shadow-[0_18px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="h-1 bg-[rgb(var(--brand-teal-rgb))]" />
          <div className="px-5 py-5 sm:px-6 lg:px-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <img
                  src={tallinkSiljaLogo}
                  alt="Tallink Silja Line logo"
                  className="h-12 w-12 rounded-2xl border border-slate-200 bg-white object-contain p-2 shadow-sm sm:h-14 sm:w-14"
                />
                <div>
                  <p className="text-base font-semibold text-slate-950">
                    Tallink Silja Line
                  </p>
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-[rgb(var(--brand-teal-rgb))]">
                    Sales Analytics Q&A
                  </p>
                </div>
              </div>
              <h1 className="mt-2 max-w-3xl text-3xl font-semibold tracking-normal text-slate-950 sm:text-4xl">
                Ask the sales data and get a business answer.
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                Tallink Silja Line sales questions are planned, translated to SQL,
                validated, and answered from the active catalog.
              </p>
            </div>
            <HealthStatus />
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <StatCard label="Catalog" value="Private" detail="Local metadata" />
            <StatCard label="Engine" value="DuckDB" detail="Validated SQL" />
            <StatCard label="Flow" value="Q&A" detail="Single answer view" />
          </div>
          </div>
        </header>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
          <QuestionPanel
            question={question}
            error={error}
            isSubmitting={submitState === "loading"}
            onQuestionChange={setQuestion}
            onSubmit={handleSubmit}
          />
          <AnswerPanel
            answer={answer}
            error={submitState === "error" ? error : null}
            isLoading={submitState === "loading"}
          />
        </section>
      </div>
    </main>
  );
}

function waitForMinimumLoadingState(): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, 700));
}

export default App;

interface StatCardProps {
  label: string;
  value: string;
  detail: string;
}

function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200/80 border-l-[3px] border-l-[rgb(var(--brand-teal-rgb))] bg-white/75 px-4 py-3 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[rgb(var(--brand-teal-rgb))]">
        {label}
      </p>
      <p className="mt-1 text-xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{detail}</p>
    </div>
  );
}
