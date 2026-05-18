import { Bot, Loader2, SendHorizontal, Sparkles, User } from "lucide-react";
import { useState } from "react";

import { formatApiError, sendModelChatMessage } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

export default function ModelChat() {
  const [messages, setMessages] = useState([
    {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "Ask me anything. I will answer with the Ollama model configured in the backend.",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || isSending) return;

    const nextMessages = [
      ...messages.map(({ role, content }) => ({ role, content })),
      { role: "user", content: cleanQuestion },
    ];

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: cleanQuestion,
      },
    ]);
    setQuestion("");
    setError("");
    setIsSending(true);

    try {
      const data = await sendModelChatMessage(nextMessages);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.answer,
          model: data.model,
        },
      ]);
    } catch (chatError) {
      setError(
        formatApiError(
          chatError,
          "Model chat failed. Make sure FastAPI and Ollama are running.",
        ),
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Model Chat" title="Chat with Ollama">
        <span className="rounded-md bg-ink/[0.06] px-3 py-2 text-xs font-medium text-ink/65">
          Direct model access
        </span>
      </PageHeader>

      <section className="grid min-h-0 flex-1 gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_18rem] sm:p-8">
        <div className="flex min-h-0 flex-col">
          <div className="min-h-96 flex-1 overflow-y-auto rounded-lg border border-ink/10 bg-white p-4 shadow-panel">
            <div className="space-y-4">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={[
                    "flex gap-3 rounded-lg p-3",
                    message.role === "user" ? "bg-ink/[0.04]" : "bg-moss/[0.08]",
                  ].join(" ")}
                >
                  <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-white text-moss">
                    {message.role === "user" ? (
                      <User aria-hidden="true" className="size-4" />
                    ) : (
                      <Bot aria-hidden="true" className="size-4" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                    {message.model ? (
                      <p className="mt-2 text-xs text-ink/50">Model: {message.model}</p>
                    ) : null}
                  </div>
                </article>
              ))}
              {isSending ? (
                <div className="inline-flex items-center gap-2 rounded-md bg-ink/[0.05] px-3 py-2 text-sm text-ink/60">
                  <Loader2 aria-hidden="true" className="size-4 animate-spin" />
                  Thinking
                </div>
              ) : null}
            </div>
          </div>

          {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}

          <form className="mt-4 flex gap-2" onSubmit={handleSubmit}>
            <input
              className="min-w-0 flex-1 rounded-md border border-ink/15 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-ink/40 focus:border-moss"
              placeholder="Ask the model anything"
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <button
              className="inline-flex size-12 shrink-0 items-center justify-center rounded-md bg-moss text-white transition hover:bg-moss/90 disabled:cursor-not-allowed disabled:bg-ink/25"
              type="submit"
              aria-label="Send message"
              disabled={!question.trim() || isSending}
            >
              {isSending ? (
                <Loader2 aria-hidden="true" className="size-5 animate-spin" />
              ) : (
                <SendHorizontal aria-hidden="true" className="size-5" />
              )}
            </button>
          </form>
        </div>

        <aside className="rounded-lg border border-ink/10 bg-white p-5 shadow-panel">
          <div className="flex items-center gap-2 text-moss">
            <Sparkles className="size-4" />
            <h2 className="text-base font-semibold text-ink">What this does</h2>
          </div>
          <p className="mt-3 text-sm leading-6 text-ink/65">
            This screen sends each message directly to the Ollama model configured in the backend
            settings. No document retrieval is used here.
          </p>
          <div className="mt-4 rounded-md bg-ink/[0.03] p-3 text-sm text-ink/70">
            <p className="font-medium">Backend model</p>
            <p className="mt-1 text-xs text-ink/55">Uses `settings.ollama_chat_model` and the Ollama base URL from backend config.</p>
          </div>
        </aside>
      </section>
    </>
  );
}
