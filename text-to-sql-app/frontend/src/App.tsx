import { HealthStatus } from "./components/HealthStatus";

export function App() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-16">
        <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
          Text to SQL
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-normal text-white sm:text-5xl">
          Clean project setup for a modular text-to-SQL workflow.
        </h1>
        <p className="mt-6 max-w-2xl text-base leading-7 text-slate-300">
          The frontend and backend are wired for local development. Business
          logic, agents, and SQL handling are intentionally left as placeholders.
        </p>
        <div className="mt-8">
          <HealthStatus />
        </div>
      </section>
    </main>
  );
}

export default App;

