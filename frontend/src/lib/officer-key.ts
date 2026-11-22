// officer-key.ts: keeps the officer key for this browser tab only (sessionStorage)
const STORAGE_KEY = "claimcare-officer-key";

export function getOfficerKey(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function saveOfficerKey(key: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY, key);
  } catch {
    // storage blocked (private mode): the key just won't be remembered
  }
}

export function clearOfficerKey() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // nothing to clear
  }
}
