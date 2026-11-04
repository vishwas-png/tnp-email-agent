import { motion } from "framer-motion";
import { ArrowUpRight, ListChecks } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CategoryChip, DeadlineBadge } from "@/components/NoticeBadges";
import { CATEGORIES, formatDateTime, safeLink, timeAgo } from "@/lib/format";

function NoticeCard({ notice, index = 0 }) {
  const accent = (CATEGORIES[notice.category] ?? CATEGORIES.general_notice).color;
  const applyLink = notice.apply_link && safeLink(notice.apply_link);
  const title = notice.company_name || notice.subject;

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: Math.min(index, 8) * 0.04, ease: "easeOut" }}
      whileHover={{ y: -4, rotate: -0.35 }}
      className="surface group relative flex flex-col overflow-hidden rounded-xl p-5 shadow-sm transition-shadow hover:shadow-xl hover:shadow-black/5 dark:hover:shadow-black/30"
    >
      {/* Category accent: a colour strip plus a soft corner glow on hover */}
      <span className="absolute inset-y-0 left-0 w-1" style={{ backgroundColor: accent }} />
      <span
        className="pointer-events-none absolute -right-16 -top-16 size-40 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-60"
        style={{ backgroundColor: accent }}
      />

      <div className="relative flex flex-wrap items-center justify-between gap-2">
        <CategoryChip category={notice.category} />
        <DeadlineBadge deadline={notice.deadline} />
      </div>

      <h3 className="relative mt-3 line-clamp-2 text-base font-semibold leading-snug tracking-tight">{title}</h3>
      {notice.role && <p className="relative mt-0.5 text-sm font-medium text-primary">{notice.role}</p>}
      {notice.company_name && (
        <p className="relative mt-1 line-clamp-1 text-xs text-muted-foreground" title={notice.subject}>
          {notice.subject}
        </p>
      )}

      <p className="relative mt-3 line-clamp-3 text-sm leading-relaxed text-muted-foreground">{notice.summary}</p>

      <div className="relative mt-auto flex items-center justify-between gap-3 pt-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-3">
          <time dateTime={notice.received_at} title={`Received ${formatDateTime(notice.received_at)} IST`}>
            {timeAgo(notice.received_at)}
          </time>
          {notice.action_items.length > 0 && (
            <span className="flex items-center gap-1" title={notice.action_items.join("\n")}>
              <ListChecks className="size-3.5" />
              {notice.action_items.length} step{notice.action_items.length === 1 ? "" : "s"}
            </span>
          )}
        </span>
        {applyLink && (
          <Button asChild size="sm" variant="secondary" className="h-7 rounded-full px-3">
            <a href={applyLink} target="_blank" rel="noopener noreferrer">
              Apply <ArrowUpRight className="size-3.5" />
            </a>
          </Button>
        )}
      </div>
    </motion.article>
  );
}

export function NoticeCardSkeleton() {
  return (
    <div className="surface flex h-[228px] flex-col rounded-xl p-5">
      <div className="flex justify-between">
        <Skeleton className="h-5 w-24 rounded-full" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <Skeleton className="mt-4 h-5 w-3/4" />
      <Skeleton className="mt-2 h-4 w-1/3" />
      <Skeleton className="mt-4 h-3.5 w-full" />
      <Skeleton className="mt-2 h-3.5 w-11/12" />
      <Skeleton className="mt-2 h-3.5 w-2/3" />
      <Skeleton className="mt-auto h-3 w-16" />
    </div>
  );
}

export default NoticeCard;
