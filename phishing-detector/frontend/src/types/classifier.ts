export interface EmailClassifyRequest {
    subject: string;
    body: string;
    sender: string;
}

export interface SuspiciousToken {
    token: string;
    weight: number;
}

export interface UrlFinding {
    url: string;
    is_suspicious: boolean;
    reason: string;
}

export interface EmailClassifyResponse {
    label: "phishing" | "legitimate";
    phishing_probability: number;
    suspicious_tokens: SuspiciousToken[];
    url_findings: UrlFinding[];
    model_version: string;
}