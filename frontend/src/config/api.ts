const PRODUCTION_API_URL = 'https://detec-production.up.railway.app';

const configuredApiUrl = String(import.meta.env.VITE_API_URL || '').trim();
const isLocalDevelopment = ['localhost', '127.0.0.1'].includes(window.location.hostname);

const normaliseApiUrl = (value: string) => {
  const withoutTrailingSlash = value.replace(/\/+$/, '');
  if (window.location.protocol === 'https:') {
    return withoutTrailingSlash.replace(/^http:\/\//i, 'https://');
  }
  return withoutTrailingSlash;
};

// Local Vite development keeps using its proxy. Hosted frontends fall back to the
// deployed API so a missing VITE_API_URL cannot accidentally call Vercel itself.
export const API_BASE_URL = normaliseApiUrl(
  configuredApiUrl || (isLocalDevelopment ? '' : PRODUCTION_API_URL),
);

export const getApiUrl = (path: string) => {
  if (!API_BASE_URL) return path;
  return new URL(path, `${API_BASE_URL}/`).toString();
};

export const getWebSocketUrl = (path: string) => {
  const url = new URL(path, `${API_BASE_URL || window.location.origin}/`);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
};
