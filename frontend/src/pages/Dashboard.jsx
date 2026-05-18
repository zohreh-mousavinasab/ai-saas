import { ArrowRight, Database, FileUp, MessageSquareText } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getChatSessions, getDocuments } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [documentsData, sessionsData] = await Promise.all([
          getDocuments(),
          getChatSessions(),
        ]);
        setDocuments(documentsData.documents ?? []);
        setSessions(sessionsData.sessions ?? []);
      } catch {
        setError("Backend data is unavailable right now.");
      }
    }

    loadDashboard();
  }, []);

  const stats = [
    { label: "Indexed documents", value: documents.length, icon: Database },
    { label: "Chat sessions", value: sessions.length, icon: MessageSquareText },
    { label: "Queued uploads", value: 0, icon: FileUp },
  ];

  return (
    <>
      <PageHeader eyebrow="Workspace" title="Document intelligence dashboard">
        {error ? <span className="text-sm text-coral">{error}</span> : null}
      </PageHeader>

      <section className="grid gap-4 p-5 sm:grid-cols-3 sm:p-8">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <article
              key={stat.label}
              className="rounded-lg border border-ink/10 bg-white p-4 shadow-panel"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-ink/60">{stat.label}</p>
                <Icon aria-hidden="true" className="size-4 text-moss" />
              </div>
              <p className="mt-3 text-3xl font-semibold">{stat.value.toLocaleString()}</p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-4 px-5 pb-8 sm:grid-cols-2 sm:px-8">
        <Link
          to="/workspace?tab=documents"
          className="group rounded-lg border border-ink/10 bg-white p-5 shadow-panel transition hover:border-moss/40"
        >
          <FileUp aria-hidden="true" className="size-5 text-moss" />
          <h2 className="mt-4 text-lg font-semibold">Add documents</h2>
          <p className="mt-2 text-sm leading-6 text-ink/65">
            Upload PDFs or text files and index them into the local vector store.
          </p>
          <ArrowRight
            aria-hidden="true"
            className="mt-4 size-4 transition group-hover:translate-x-1"
          />
        </Link>

        <Link
          to="/workspace?tab=chat"
          className="group rounded-lg border border-ink/10 bg-white p-5 shadow-panel transition hover:border-moss/40"
        >
          <MessageSquareText aria-hidden="true" className="size-5 text-moss" />
          <h2 className="mt-4 text-lg font-semibold">Ask a question</h2>
          <p className="mt-2 text-sm leading-6 text-ink/65">
            Query indexed documents with local RAG answers and source citations.
          </p>
          <ArrowRight
            aria-hidden="true"
            className="mt-4 size-4 transition group-hover:translate-x-1"
          />
        </Link>
      </section>
    </>
  );
}
