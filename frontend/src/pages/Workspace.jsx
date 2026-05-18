import {
  Bot,
  CheckCircle2,
  FileSearch,
  FileText,
  FileUp,
  Loader2,
  MessageSquareText,
  SendHorizontal,
  User,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  formatApiError,
  getDocuments,
  getHealth,
  sendChatMessage,
  uploadDocuments,
} from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

const TABS = [
  {
    id: "documents",
    label: "Documents",
    description: "Upload and index files",
    icon: FileText,
  },
  {
    id: "chat",
    label: "Chat",
    description: "Ask questions with sources",
    icon: MessageSquareText,
  },
];

const VALID_TAB_IDS = new Set(TABS.map((tab) => tab.id));

export default function Workspace({ initialTab = "documents" }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get("tab");
  const defaultTab = VALID_TAB_IDS.has(initialTab) ? initialTab : "documents";
  const resolvedTab = VALID_TAB_IDS.has(tabFromUrl) ? tabFromUrl : defaultTab;

  const [activeTab, setActiveTab] = useState(resolvedTab);
  const [documents, setDocuments] = useState([]);
  const [documentError, setDocumentError] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [chatError, setChatError] = useState("");
  const [backendStatus, setBackendStatus] = useState("loading");
  const [backendMessage, setBackendMessage] = useState("Checking backend...");

  const hasFiles = selectedFiles.length > 0;
  const uploadTone = useMemo(() => {
    if (uploadStatus === "complete") return "text-moss";
    if (uploadStatus === "failed") return "text-coral";
    return "text-ink/60";
  }, [uploadStatus]);

  useEffect(() => {
    setActiveTab(resolvedTab);
  }, [resolvedTab]);

  useEffect(() => {
    async function loadDocuments() {
      try {
        const data = await getDocuments();
        setDocuments(data.documents ?? []);
        setDocumentError("");
      } catch {
        setDocumentError("Could not load uploaded documents.");
      }
    }

    loadDocuments();
  }, []);

  useEffect(() => {
    async function checkBackend() {
      try {
        const data = await getHealth();
        setBackendStatus("ok");
        setBackendMessage(
          `${data.app_name ?? "Backend"} is online${data.environment ? ` (${data.environment})` : ""}.`,
        );
      } catch (error) {
        setBackendStatus("down");
        setBackendMessage(
          formatApiError(
            error,
            "Backend is not reachable right now. Start FastAPI on port 8000 and refresh the page.",
          ),
        );
      }
    }

    checkBackend();
  }, []);

  function handleTabChange(nextTab) {
    setActiveTab(nextTab);
    setSearchParams({ tab: nextTab });
  }

  function handleFileChange(event) {
    setSelectedFiles(Array.from(event.target.files ?? []));
    setUploadMessage("");
    setUploadStatus("idle");
  }

  function toggleDocument(documentId) {
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!hasFiles || uploadStatus === "uploading") return;

    const form = event.currentTarget;
    setUploadStatus("uploading");
    setUploadMessage("Uploading and indexing documents...");
    try {
      const data = await uploadDocuments(selectedFiles);
      setDocuments((current) => [...(data.documents ?? []), ...current]);
      setDocumentError("");
      setSelectedFiles([]);
      form?.reset();
      setUploadStatus("complete");
      setUploadMessage("Documents indexed and ready for chat.");
    } catch (error) {
      setUploadStatus("failed");
      setUploadMessage(
        formatApiError(
          error,
          "Upload could not reach the backend. Check that FastAPI is running and VITE_API_BASE_URL is correct.",
        ),
      );
    }
  }

  async function handleChatSubmit(event) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || isSending) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: cleanQuestion,
    };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatError("");
    setIsSending(true);

    try {
      const data = await sendChatMessage({
        question: cleanQuestion,
        documentIds: selectedDocumentIds,
        sessionId,
      });
      setSessionId(data.session_id);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.answer,
          sources: data.sources ?? [],
        },
      ]);
    } catch (sendError) {
      setChatError(
        formatApiError(
          sendError,
          "Chat failed. Make sure the backend, Ollama, and indexed documents are available.",
        ),
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Document Chat" title="Documents and chat in one place">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={[
              "rounded-md px-3 py-2 text-xs font-medium",
              backendStatus === "ok"
                ? "bg-moss/10 text-moss"
                : backendStatus === "down"
                  ? "bg-coral/10 text-coral"
                  : "bg-ink/[0.06] text-ink/65",
            ].join(" ")}
          >
            {backendMessage}
          </span>
          {sessionId ? (
            <span className="rounded-md bg-ink/[0.06] px-3 py-2 text-xs font-medium text-ink/65">
              Session {sessionId.slice(0, 8)}
            </span>
          ) : null}
        </div>
      </PageHeader>

      <section className="flex min-h-0 flex-1 p-5 sm:p-8">
        <div className="flex min-h-0 w-full flex-col rounded-2xl border border-ink/10 bg-white shadow-panel">
          <div className="border-b border-ink/10 px-4 py-4 sm:px-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-sm font-semibold text-ink/80">Document Chat tabs</p>
                <p className="mt-1 text-sm text-ink/55">
                  Move between document indexing and chat without leaving the page.
                </p>
              </div>

              <div className="inline-flex rounded-full bg-ink/[0.04] p-1">
                {TABS.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      type="button"
                      aria-selected={isActive}
                      onClick={() => handleTabChange(tab.id)}
                      className={[
                        "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition",
                        isActive
                          ? "bg-moss text-white shadow-sm"
                          : "text-ink/60 hover:text-ink",
                      ].join(" ")}
                    >
                      <Icon aria-hidden="true" className="size-4" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
            {activeTab === "documents" ? (
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
                <form
                  className="flex min-h-[28rem] flex-col items-center justify-center rounded-xl border border-dashed border-ink/20 bg-paper/50 p-8 text-center"
                  onSubmit={handleUpload}
                >
                  <FileUp aria-hidden="true" className="size-8 text-moss" />
                  <h2 className="mt-4 text-lg font-semibold">Add PDF or TXT files</h2>
                  <p className="mt-2 max-w-sm text-sm leading-6 text-ink/65">
                    Files are saved locally, parsed, chunked, embedded, and indexed in ChromaDB.
                  </p>

                  <label className="mt-6 inline-flex cursor-pointer items-center gap-2 rounded-md border border-ink/15 bg-white px-4 py-2 text-sm font-medium transition hover:border-moss/50">
                    <FileText aria-hidden="true" className="size-4 text-moss" />
                    Choose files
                    <input
                      className="sr-only"
                      type="file"
                      accept=".pdf,.txt"
                      multiple
                      onChange={handleFileChange}
                    />
                  </label>

                  {hasFiles ? (
                    <div className="mt-4 w-full max-w-md rounded-md bg-ink/[0.03] p-3 text-left text-sm text-ink/70">
                      {selectedFiles.map((file) => (
                        <p key={`${file.name}-${file.size}`} className="truncate">
                          {file.name}
                        </p>
                      ))}
                    </div>
                  ) : null}

                  <button
                    className="mt-5 inline-flex items-center gap-2 rounded-md bg-moss px-4 py-2 text-sm font-semibold text-white transition hover:bg-moss/90 disabled:cursor-not-allowed disabled:bg-ink/25"
                    type="submit"
                    disabled={!hasFiles || uploadStatus === "uploading"}
                  >
                    {uploadStatus === "uploading" ? (
                      <Loader2 aria-hidden="true" className="size-4 animate-spin" />
                    ) : (
                      <FileUp aria-hidden="true" className="size-4" />
                    )}
                    Upload and index
                  </button>

                  {uploadMessage ? (
                    <p className={`mt-4 flex items-center gap-2 text-sm ${uploadTone}`}>
                      {uploadStatus === "complete" ? <CheckCircle2 className="size-4" /> : null}
                      {uploadStatus === "failed" ? <XCircle className="size-4" /> : null}
                      {uploadMessage}
                    </p>
                  ) : null}
                </form>

                <aside className="rounded-xl border border-ink/10 bg-white p-5">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-base font-semibold">Indexed documents</h2>
                    <span className="rounded-full bg-ink/[0.06] px-2 py-1 text-xs font-medium text-ink/70">
                      {documents.length}
                    </span>
                  </div>

                  <div className="mt-4 space-y-3">
                    {documentError ? (
                      <p className="text-sm leading-6 text-coral">{documentError}</p>
                    ) : null}
                    {documents.length ? (
                      documents.map((document) => (
                        <article
                          key={document.document_id}
                          className="rounded-md border border-ink/10 p-3"
                        >
                          <p className="truncate text-sm font-medium">{document.file_name}</p>
                          <p className="mt-1 text-xs text-ink/55">
                            {document.chunk_count} chunks /{" "}
                            {document.character_count.toLocaleString()} chars
                          </p>
                        </article>
                      ))
                    ) : (
                      <p className="text-sm leading-6 text-ink/60">No documents indexed yet.</p>
                    )}
                  </div>
                </aside>
              </div>
            ) : (
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
                <div className="flex min-h-0 flex-col">
                  <div className="min-h-[28rem] flex-1 overflow-y-auto rounded-xl border border-ink/10 bg-white p-4">
                    {messages.length ? (
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
                              {message.sources?.length ? (
                                <div className="mt-3 space-y-2">
                                  {message.sources.map((source) => (
                                    <div
                                      key={`${source.document_id}-${source.chunk_index}`}
                                      className="rounded-md border border-ink/10 bg-white p-3"
                                    >
                                      <p className="text-xs font-semibold text-ink/70">
                                        {source.file_name}
                                        {source.page_number ? `, page ${source.page_number}` : ""}
                                      </p>
                                      <p className="mt-1 text-xs leading-5 text-ink/60">
                                        {source.excerpt}
                                      </p>
                                    </div>
                                  ))}
                                </div>
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
                    ) : (
                      <div className="flex min-h-80 items-center justify-center text-center">
                        <div className="max-w-sm">
                          <FileSearch aria-hidden="true" className="mx-auto size-8 text-moss" />
                          <h2 className="mt-4 text-lg font-semibold">Ready for grounded Q&A</h2>
                          <p className="mt-2 text-sm leading-6 text-ink/65">
                            Ask a question after uploading documents. Answers include returned
                            sources.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {chatError ? <p className="mt-3 text-sm text-coral">{chatError}</p> : null}

                  <form className="mt-4 flex gap-2" onSubmit={handleChatSubmit}>
                    <input
                      className="min-w-0 flex-1 rounded-md border border-ink/15 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-ink/40 focus:border-moss"
                      placeholder="Ask a question about your documents"
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

                <aside className="rounded-xl border border-ink/10 bg-white p-5">
                  <h2 className="text-base font-semibold">Document scope</h2>
                  <p className="mt-1 text-sm text-ink/60">
                    Select none to search every indexed document.
                  </p>

                  <div className="mt-4 space-y-2">
                    {documents.length ? (
                      documents.map((document) => (
                        <label
                          key={document.document_id}
                          className="flex cursor-pointer items-start gap-3 rounded-md border border-ink/10 p-3 text-sm transition hover:border-moss/40"
                        >
                          <input
                            className="mt-1 accent-moss"
                            type="checkbox"
                            checked={selectedDocumentIds.includes(document.document_id)}
                            onChange={() => toggleDocument(document.document_id)}
                          />
                          <span className="min-w-0">
                            <span className="block truncate font-medium">{document.file_name}</span>
                            <span className="mt-1 block text-xs text-ink/55">
                              {document.chunk_count} chunks
                            </span>
                          </span>
                        </label>
                      ))
                    ) : (
                      <p className="text-sm leading-6 text-ink/60">No indexed documents found.</p>
                    )}
                  </div>
                </aside>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
