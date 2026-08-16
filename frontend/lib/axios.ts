import axios from 'axios';

const apiClient = axios.create({
    // Keep browser requests same-origin. Next.js proxies /api to the FastAPI
    // service, so the session cookie works without cross-site cookie settings.
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 20000,
    withCredentials: true,
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => Promise.reject(error)
);

export default apiClient;
