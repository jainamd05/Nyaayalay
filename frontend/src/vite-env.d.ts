/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend base URL, e.g. https://your-api.onrender.com (preferred). */
  readonly VITE_API_BASE_URL?: string;
  /** Legacy name for VITE_API_BASE_URL, still supported. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
