import type { EmailClassifyRequest, EmailClassifyResponse } from "../types/classifier";

const API_BASE_URL = "http://localhost:8000/api/v1";

export async function classifyEmail(
    payload: EmailClassifyRequest,
): Promise<EmailClassifyResponse> {
    const response = await fetch(
        `${API_BASE_URL}/classify`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        },
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail || `Classification failed (${response.status})`,
        );
    }

    return response.json();
}

export function connectGmail(): void {
    window.location.href = `${API_BASE_URL}/gmail/connect`;
}

export async function getGmailStatus(): Promise<boolean> {
    const response = await fetch(
        `${API_BASE_URL}/gmail/status`,
    );

    if (!response.ok) {
        throw new Error(
            `Failed to check Gmail status (${response.status})`,
        );
    }

    const data: { connected: boolean } =
        await response.json();

    return data.connected;
}

export interface GmailMessage {
    id: string;
    thread_id?: string;
    subject: string;
    sender: string;
    date: string;
    snippet: string;
}

export async function getGmailMessages(
    limit = 10,
): Promise<GmailMessage[]> {
    const response = await fetch(
        `${API_BASE_URL}/gmail/messages?limit=${limit}`,
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail ||
                `Failed to fetch Gmail messages (${response.status})`,
        );
    }

    const data: { messages: GmailMessage[] } =
        await response.json();

    return data.messages;
}

export async function analyzeGmailMessage(
    messageId: string,
): Promise<EmailClassifyResponse> {
    const response = await fetch(
        `${API_BASE_URL}/gmail/messages/${messageId}/analyze`,
        {
            method: "POST",
        },
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail ||
                `Failed to analyze Gmail message (${response.status})`,
        );
    }

    return response.json();
}

export async function disconnectGmail(): Promise<void> {
    const response = await fetch(
        `${API_BASE_URL}/gmail/disconnect`,
        {
            method: "POST",
        },
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail ||
                `Failed to disconnect Gmail (${response.status})`,
        );
    }
}

export interface GmailFullMessage {
    id: string;
    thread_id?: string;
    subject: string;
    sender: string;
    date: string;
    body: string;
    snippet: string;
}

export async function getGmailMessage(
    messageId: string,
): Promise<GmailFullMessage> {
    const response = await fetch(
        `${API_BASE_URL}/gmail/messages/${messageId}`,
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail ||
            `Failed to fetch email (${response.status})`,
        );
    }

    return response.json();
}