interface GoogleCredentialResponse {
    credential: string;
}

interface GoogleIdentityServices {
    accounts: {
        id: {
            initialize(options: { client_id: string; callback: (response: GoogleCredentialResponse) => void }): void;
            renderButton(element: HTMLElement, options: Record<string, string>): void;
            prompt(): void;
        };
    };
}

interface Window {
    google?: GoogleIdentityServices;
}
