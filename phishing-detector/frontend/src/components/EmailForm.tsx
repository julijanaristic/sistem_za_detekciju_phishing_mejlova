import { useState } from "react";
import { classifyEmail } from "../services/api";
import type { EmailClassifyResponse } from "../types/classifier";

interface EmailFormProps{
    onResult: (result: EmailClassifyResponse) => void;
    onLoading: (loading: boolean) => void;
}

function EmailForm({
    onResult,
    onLoading,
}: EmailFormProps) {
    const [subject, setSubject] = useState("");
    const [body, setBody] = useState("");
    const [sender, setSender] = useState("");
    const [error, setError] = useState("");

    async function handleSubmit(
        event: React.FormEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        setError("");

        if (!subject.trim() && !body.trim()) {
            setError("Please enter an email subject or body.");
            return;
        }

        try {
            onLoading(true);

            const result = await classifyEmail({
                subject, 
                body,
                sender,
            });

            onResult(result);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Something went wrong",
            );
        } finally {
            onLoading(false);
        }
    }

    return (
        <form 
            onSubmit={handleSubmit}
            className="space-y-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div>
            <label
                htmlFor="subject"
                className="mb-2 block text-sm font-semibold text-slate-700">
                Email subject
            </label>

            <input
                id="subject"
                type="text"
                value={subject}
                onChange={(event) =>
                    setSubject(event.target.value)
                }
                placeholder="Urgent: Verify your account"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"/>
        </div>

        <div>
            <label
                htmlFor="sender"
                className="mb-2 block text-sm font-semibold text-slate-700">
                Email sender
            </label>

            <input
                id="sender"
                type="text"
                value={sender}
                onChange={(event) =>
                    setSender(event.target.value)
                }
                placeholder="Sender"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"/>
        </div>

        <div>
            <label
                htmlFor="body"
                className="mb-2 block text-sm font-semibold text-slate-700">
                Email body
            </label>

            <textarea
                id="body"
                value={body}
                onChange={(event) =>
                    setBody(event.target.value)
                }
                placeholder="Paste the email content here..."
                rows={12}
                className="w-full resize-y rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"/>
        </div>

        {error && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
            </div>
        )}

        <button
                type="submit"
                className="w-full rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700">
                Analyze email
        </button>
    </form>
    )
}

export default EmailForm;