import type { EmailClassifyResponse } from "../types/classifier";

interface ResultCardProps {
    result: EmailClassifyResponse;
}

function ResultCard({ result }: ResultCardProps) {
    const isPhishing = result.label === "phishing";

    const probability = (
        result.phishing_probability * 100
    ).toFixed(2);

    return (
        <div
            className={`rounded-2xl p-6 shadow-sm ring-1 ${
                isPhishing
                ? "bg-red-50 ring-red-200"
                : "bg-emerald-50 ring-emerald-200"}`}>
        <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold">
            Analysis result
            </h2>

            <span
                className={`rounded-full px-4 py-2 text-sm font-bold uppercase ${
                    isPhishing
                    ? "bg-red-600 text-white"
                    : "bg-emerald-600 text-white"}`}>
                {result.label}
            </span>
        </div>

        <div className="mb-6">
            <p className="text-sm text-slate-600">
                Phishing probability
            </p>

            <p className="text-4xl font-bold text-slate-900">
                {probability}%
            </p>
        </div>

        <div className="mb-6">
            <p className="mb-2 text-sm font-semibold text-slate-700">
                Model
            </p>

            <code className="rounded bg-white px-3 py-1 text-sm">
                {result.model_version}
            </code>
        </div>

        <div>
            <p className="mb-3 text-sm font-semibold text-slate-700">
                Suspicious tokens
            </p>

            {result.suspicious_tokens.length === 0 ? (
                <p className="text-sm text-slate-500">
                    No suspicious tokens detected.
                </p>
            ) : (
                <div className="space-y-2">
                    {result.suspicious_tokens.map(
                        (item, index) => (
                            <div
                                key={`${item.token}-${index}`}
                                className="flex items-center justify-between rounded-lg bg-white px-4 py-2">
                                <span className="font-medium">
                                    {item.token}
                                </span>

                                <span className="text-sm text-slate-500">
                                    {item.weight.toFixed(4)}
                                </span>
                            </div>
                        ),
                    )}
                </div>
            )}
        </div>
    </div>
    );
}

export default ResultCard;