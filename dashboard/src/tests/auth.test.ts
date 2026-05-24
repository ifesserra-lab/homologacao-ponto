import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  checkCredentials,
  getSession,
  setSession,
  clearSession,
} from "../lib/auth";

// SubtleCrypto is available natively in the Vitest/Node 20+ environment
// but we must ensure it is wired to the global crypto.subtle

const sha256 = async (text: string): Promise<string> => {
  const buf = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
};

describe("checkCredentials", () => {
  it("T006 returns false for wrong credentials", async () => {
    const userHash = await sha256("admin");
    const passHash = await sha256("secret");
    expect(await checkCredentials("wrong", "wrong", userHash, passHash)).toBe(false);
  });

  it("T007 returns true for correct credentials", async () => {
    const userHash = await sha256("admin");
    const passHash = await sha256("secret");
    expect(await checkCredentials("admin", "secret", userHash, passHash)).toBe(true);
  });

  it("T010 returns false when hashes are undefined (no env vars)", async () => {
    expect(await checkCredentials("admin", "secret", undefined, undefined)).toBe(false);
  });

  it("T010b does not reveal which field is wrong (same false result)", async () => {
    const userHash = await sha256("admin");
    const passHash = await sha256("secret");
    const wrongUser = await checkCredentials("wrong", "secret", userHash, passHash);
    const wrongPass = await checkCredentials("admin", "wrong", userHash, passHash);
    expect(wrongUser).toBe(false);
    expect(wrongPass).toBe(false);
    // Both return the same value — no field discrimination possible
    expect(wrongUser).toBe(wrongPass);
  });
});

describe("session management", () => {
  const mockStorage: Record<string, string> = {};

  beforeEach(() => {
    Object.keys(mockStorage).forEach((k) => delete mockStorage[k]);
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => mockStorage[k] ?? null,
      setItem: (k: string, v: string) => { mockStorage[k] = v; },
      removeItem: (k: string) => { delete mockStorage[k]; },
    });
  });

  it("T008 getSession returns null when sessionStorage is empty", () => {
    expect(getSession()).toBeNull();
  });

  it("T009 setSession persists authenticated:true in sessionStorage", () => {
    setSession();
    const session = getSession();
    expect(session).not.toBeNull();
    expect(session!.authenticated).toBe(true);
  });

  it("T009b setSession stores redirect URL when provided", () => {
    setSession("/servidor/celio");
    const session = getSession();
    expect(session!.redirect).toBe("/servidor/celio");
  });

  it("T022 clearSession removes dashboard_auth from sessionStorage", () => {
    setSession();
    expect(getSession()).not.toBeNull();
    clearSession();
    expect(getSession()).toBeNull();
  });
});
