export interface AuthSession {
  authenticated: boolean;
  redirect?: string | null;
}

const SESSION_KEY = "dashboard_auth";

export async function checkCredentials(
  user: string,
  password: string,
  userHash: string | undefined,
  passwordHash: string | undefined,
): Promise<boolean> {
  if (!userHash || !passwordHash) return false;
  const [inputUserHash, inputPassHash] = await Promise.all([
    sha256(user),
    sha256(password),
  ]);
  return inputUserHash === userHash && inputPassHash === passwordHash;
}

export function getSession(): AuthSession | null {
  if (typeof sessionStorage === "undefined") return null;
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function setSession(redirect?: string | null): void {
  const session: AuthSession = { authenticated: true, redirect: redirect ?? null };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  sessionStorage.removeItem(SESSION_KEY);
}

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
