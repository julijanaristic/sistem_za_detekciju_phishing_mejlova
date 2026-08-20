import { useEffect, useState } from "react";
import type { EmailClassifyResponse } from "../types/classifier";
import { analyzeGmailMessage, connectGmail, disconnectGmail, getGmailMessage, getGmailMessages, getGmailStatus, type GmailFullMessage, type GmailMessage } from "../services/api";

interface GmailPanelProps {
    onResult: (result: EmailClassifyResponse) => void;
    onLoading: (loading: boolean) => void;
}

function GmailPanel({
    onResult,
    onLoading,
}: GmailPanelProps) {
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState<GmailMessage[]>([]);
    const [selectedMessage, setSelectedMessage] = useState<GmailFullMessage | null>(null);
    const [loadingMessage, setLoadingMessage] = useState(false);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [error, setError] = useState("");

    async function checkGmail(){
        try {
            const isConnected = await getGmailStatus();

            setConnected(isConnected);

            if (isConnected) {
                await loadMessages();
            }
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to check Gmail connection",
            );
        }
    }

    async function loadMessages() {
        try {
            setLoadingMessages(true);
            setError("");
            setSelectedMessage(null);

            const result = await getGmailMessages(10);

            setMessages(result);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to load Gmail messages",
            );
        } finally {
            setLoadingMessages(false);
        }
    }

    async function handleOpenMessage(messageId: string) {
        try {
            setLoadingMessage(true);
            setError("");

            const message = await getGmailMessage(messageId);

            setSelectedMessage(message);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to load email",
            );
        } finally {
            setLoadingMessage(false);
        }
    }

    async function handleAnalyze(messageId: string) {
        try {
            setError("");
            onLoading(true);

            const result = await analyzeGmailMessage(messageId);

            onResult(result);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to analyze email",
            );
        } finally {
            onLoading(false);
        }
    }

    async function handleDisconnect() {
        try {
            setError("");

            await disconnectGmail();

            setConnected(false);
            setMessages([]);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to disconnect Gmail.",
            );
        }
    }

    useEffect(() => {
        const params = new URLSearchParams(
            window.location.search,
        );

        const gmailStatus = params.get("gmail");

        checkGmail();

        if (gmailStatus === "connected") {
            window.history.replaceState(
                {},
                document.title,
                window.location.pathname,
            );
        }
    }, []);

    if (!connected) {
        return (
            <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <div className="mb-6">
                    <h2 className="text-xl font-bold text-slate-900">
                        Connect your Gmail
                    </h2>

                    <p className="mt-2 text-sm text-slate-600">
                        Connect your Gmail account to analyze emails directly from your inbox.
                    </p>
                </div>

                {error && (
                    <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                        {error}
                    </div>
                )}

                <button
                    type="button"
                    onClick={connectGmail}
                    className="flex w-full items-center justify-center gap-3 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700">
                    Connect Gmail
                </button>
            </div>
        );
    }

    return (
        <div className="h-[650px] rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-900">
                        {selectedMessage
                            ? "Email"
                            : "Gmail inbox"}
                    </h2>

                    <p className="mt-1 text-sm text-emerald-600">
                        Gmail connected
                    </p>
                </div>

                <div className="flex gap-2">
                    {!selectedMessage && (
                        <button
                            type="button"
                            onClick={loadMessages}
                            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                            Refresh
                        </button>
                    )}

                    {selectedMessage && (
                        <button
                            type="button"
                            onClick={() =>
                                setSelectedMessage(null)
                            }
                            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                            Back
                        </button>
                    )}

                    <button
                        type="button"
                        onClick={handleDisconnect}
                        className="rounded-lg border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50">
                        Disconnect
                    </button>
                </div>
            </div>

            {error && (
                <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            {loadingMessage ? (
                <div className="flex h-[540px] items-center justify-center text-sm text-slate-500">
                    Loading email...
                </div>
            ) : selectedMessage ? (
                <div className="flex h-[540px] flex-col">
                    <div className="border-b border-slate-200 pb-4">
                        <h3 className="text-lg font-bold text-slate-900">
                            {selectedMessage.subject ||
                                "(No subject)"}
                        </h3>

                        <p className="mt-2 text-sm text-slate-600">
                            <span className="font-semibold">
                                From:
                            </span>{" "}
                            {selectedMessage.sender}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                            {selectedMessage.date}
                        </p>
                    </div>

                    <div className="mt-4 flex-1 overflow-y-auto rounded-lg bg-slate-50 p-4">
                        <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-700">
                            {selectedMessage.body}
                        </pre>
                    </div>

                    <button
                        type="button"
                        onClick={() =>
                            handleAnalyze(selectedMessage.id)
                        }
                        className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700">
                        Analyze this email
                    </button>
                </div>
                ) : loadingMessages ? (
                    <div className="flex h-[540px] items-center justify-center text-sm text-slate-500">
                        Loading emails...
                    </div>
                ) : messages.length === 0 ? (
                    <div className="flex h-[540px] items-center justify-center text-sm text-slate-500">
                        No emails found.
                    </div>
                ) : (
                <div className="h-[540px] space-y-3 overflow-y-auto pr-2">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            onClick={() =>
                                handleOpenMessage(
                                    message.id,
                                )
                            }
                            className="cursor-pointer rounded-xl border border-slate-200 p-4 transition hover:border-blue-300 hover:bg-slate-50">
                            <div className="flex items-start justify-between gap-4">
                                <div className="min-w-0">
                                    <h3 className="truncate font-semibold text-slate-900">
                                        {message.subject ||
                                            "(No subject)"}
                                    </h3>

                                    <p className="mt-1 truncate text-sm text-slate-600">
                                        {message.sender}
                                    </p>

                                    <p className="mt-2 line-clamp-2 text-sm text-slate-500">
                                        {message.snippet}
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={(event) => {
                                        event.stopPropagation();

                                        handleAnalyze(
                                            message.id,
                                        );
                                    }}
                                    className="shrink-0 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700">
                                    Analyze
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default GmailPanel;
            