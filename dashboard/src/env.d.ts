/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  readonly PUBLIC_DASHBOARD_USER_HASH: string | undefined;
  readonly PUBLIC_DASHBOARD_PASSWORD_HASH: string | undefined;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}