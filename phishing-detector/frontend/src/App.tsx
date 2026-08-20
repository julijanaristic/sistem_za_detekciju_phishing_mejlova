import { useState } from "react";
import type { EmailClassifyResponse } from "./types/classifier";
import EmailForm from "./components/EmailForm";
import ResultCard from "./components/ResultCard";
import GmailPanel from "./components/GmailPanel";

function App() {
    const [result, setResult] = useState<EmailClassifyResponse | null>(null);
    const [loading, setLoading] = useState(false);

    return (
        <main className="min-h-screen bg-slate-50">
            <div className="mx-auto max-w-7xl px-6 py-12">

                <div className="mb-10 text-center">
                    <h1 className="text-4xl font-bold tracking-tight text-slate-900">
                        Phishing Email Detector
                    </h1>

                    <p className="mt-3 text-slate-600">
                        Analyze emails manually or directly from your Gmail inbox.
                    </p>
                </div>

                <div className="grid items-start gap-8 lg:grid-cols-3">

                    <div className="min-w-0">
                        <EmailForm
                            onResult={setResult}
                            onLoading={setLoading}
                        />
                    </div>

                    <div className="min-w-0">
                        <GmailPanel
                            onResult={setResult}
                            onLoading={setLoading}
                        />
                    </div>

                    <div className="min-w-0">
                        {loading && (
                            <div className="rounded-2xl bg-white p-8 text-center shadow-sm ring-1 ring-slate-200">
                                <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

                                <p className="font-medium text-slate-600">
                                    Analyzing email...
                                </p>
                            </div>
                        )}

                        {!loading && result && (
                            <ResultCard result={result} />
                        )}

                        {!loading && !result && (
                            <div className="rounded-2xl bg-white p-8 text-center text-slate-500 shadow-sm ring-1 ring-slate-200">
                                <p>
                                    Submit an email or select an email
                                    from Gmail to see the classification
                                    result.
                                </p>
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </main>
    );
}

export default App;