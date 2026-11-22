"use client";

import { AlertCircleIcon, ArrowLeftIcon, ShieldIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { ApiError, getOfficerClaims } from "@/lib/api";
import { saveOfficerKey } from "@/lib/officer-key";

export default function OfficerLoginPage() {
  const router = useRouter();
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault();
    if (!key.trim()) {
      setError("Enter your officer key.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      // The backend is the real lock: a wrong key gets 401 here
      await getOfficerClaims(key.trim());
      saveOfficerKey(key.trim());
      // Reset this page: Next.js keeps its state alive for when we come back (after logout)
      setKey("");
      setLoading(false);
      router.push("/officer");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setError("Wrong key. Try again.");
      else setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center bg-brand-50 px-4 py-16">
      <form onSubmit={handleLogin} className="w-full max-w-sm rounded-2xl border border-brand-100 bg-white p-7">
        <div className="text-center">
          <span className="inline-flex size-12 items-center justify-center rounded-xl bg-brand-600 text-white">
            <ShieldIcon className="size-6" />
          </span>
          <h1 className="mt-3 text-xl font-medium text-brand-900">Officer login</h1>
          <p className="text-sm text-muted-foreground">For claims officers only.</p>
        </div>

        <div className="mt-6 grid gap-1.5">
          <Label htmlFor="key">Officer key</Label>
          <Input
            id="key"
            type="password"
            autoComplete="current-password"
            value={key}
            onChange={(e) => { setKey(e.target.value); setError(""); }}
            aria-invalid={Boolean(error)}
          />
          {error && (
            <p className="flex items-center gap-1 text-xs text-destructive"><AlertCircleIcon className="size-3.5" /> {error}</p>
          )}
        </div>

        <Button type="submit" className="mt-5 w-full" disabled={loading}>
          {loading && <Spinner />} Log in
        </Button>
        <Link href="/" className="mt-4 flex items-center justify-center gap-1 text-xs text-brand-600 hover:underline">
          <ArrowLeftIcon className="size-3.5" /> Back to home
        </Link>
      </form>
    </main>
  );
}
