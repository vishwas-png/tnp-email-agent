import { MailCheck } from "lucide-react";
import { cn } from "@/lib/utils";

function Logo({ className, showText = true }) {
  return (
    <span className={cn("flex items-center gap-2.5 font-semibold tracking-tight", className)}>
      <span className="grid size-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-placement text-primary-foreground shadow-lg shadow-primary/25">
        <MailCheck className="size-4.5" strokeWidth={2.25} />
      </span>
      {showText && <span>TNP Agent</span>}
    </span>
  );
}

export default Logo;
