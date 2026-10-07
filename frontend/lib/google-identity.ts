let scriptPromise: Promise<void> | null = null;
let initializedClientId: string | null = null;
let activeCallback: ((response: GoogleCredentialResponse) => void) | null = null;
let activeRegistration: symbol | null = null;

function loadGoogleIdentityScript(): Promise<void> {
    if (window.google?.accounts?.id) return Promise.resolve();
    if (scriptPromise) return scriptPromise;

    scriptPromise = new Promise((resolve, reject) => {
        const existing = document.querySelector<HTMLScriptElement>('script[data-quant-google-identity]');
        if (existing) {
            existing.addEventListener('load', () => resolve(), { once: true });
            existing.addEventListener('error', () => reject(new Error('Google Identity Services failed to load')), { once: true });
            return;
        }
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.dataset.quantGoogleIdentity = 'true';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Google Identity Services failed to load'));
        document.head.appendChild(script);
    });
    return scriptPromise;
}

export async function configureGoogleIdentity(
    clientId: string,
    callback: (response: GoogleCredentialResponse) => void,
): Promise<() => void> {
    const registration = Symbol('google-identity-registration');
    activeRegistration = registration;
    activeCallback = callback;
    await loadGoogleIdentityScript();

    if (activeRegistration !== registration) return () => undefined;

    if (!window.google?.accounts?.id) throw new Error('Google Identity Services is unavailable');
    if (initializedClientId && initializedClientId !== clientId) {
        throw new Error('Google Identity Services was initialized with a different client ID');
    }
    if (!initializedClientId) {
        window.google.accounts.id.initialize({
            client_id: clientId,
            callback: (response) => activeCallback?.(response),
        });
        initializedClientId = clientId;
    }

    return () => {
        if (activeRegistration === registration) {
            activeRegistration = null;
            activeCallback = null;
        }
    };
}
