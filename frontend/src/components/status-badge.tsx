import { CheckIcon, Loader2Icon, UserCheckIcon, XIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { ClaimStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const STATUS = {
  processing: { label: "Processing", icon: Loader2Icon, className: "bg-amber-50 text-amber-900 border-amber-200", spin: true },
  approved: { label: "Approved", icon: CheckIcon, className: "bg-green-50 text-green-900 border-green-200", spin: false },
  rejected: { label: "Rejected", icon: XIcon, className: "bg-red-50 text-red-900 border-red-200", spin: false },
  officer_review: { label: "Officer review", icon: UserCheckIcon, className: "bg-blue-50 text-blue-900 border-blue-200", spin: false },
} as const;

export function StatusBadge({ status, className }: { status: ClaimStatus; className?: string }) {
  const s = STATUS[status];
  const Icon = s.icon;
  return (
    <Badge variant="outline" className={cn("rounded-full px-2.5", s.className, className)}>
      <Icon className={cn(s.spin && "animate-spin")} />
      {s.label}
    </Badge>
  );
}

export function RiskBadge({ risk }: { risk: "low" | "high" | null }) {
  if (!risk) return null;
  return risk === "high" ? (
    <Badge variant="outline" className="rounded-full border-red-200 bg-red-50 text-red-900">High risk</Badge>
  ) : (
    <Badge variant="outline" className="rounded-full border-green-200 bg-green-50 text-green-900">Low risk</Badge>
  );
}
