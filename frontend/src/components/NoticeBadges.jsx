import { Clock } from "lucide-react";
import { CATEGORIES, deadlineStatus, formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export function CategoryChip({ category }) {
  const meta = CATEGORIES[category] ?? CATEGORIES.general_notice;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ color: meta.color, backgroundColor: `color-mix(in oklch, ${meta.color} 14%, transparent)` }}
    >
      <span className="size-1.5 rounded-full" style={{ backgroundColor: meta.color }} />
      {meta.label}
    </span>
  );
}

const TONES = {
  urgent: "bg-destructive/15 text-destructive ring-destructive/30",
  soon: "bg-general/15 text-general ring-general/30",
  later: "bg-primary/12 text-primary ring-primary/25",
  passed: "bg-muted text-muted-foreground ring-border line-through decoration-1",
};

export function DeadlineBadge({ deadline }) {
  if (!deadline) return null;
  const { tone, label } = deadlineStatus(deadline);
  return (
    <span
      title={`Deadline: ${formatDateTime(deadline)} IST`}
      className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset", TONES[tone])}
    >
      <Clock className="size-3" />
      {label}
      {tone === "urgent" && <span className="sr-only"> (less than a day)</span>}
    </span>
  );
}
