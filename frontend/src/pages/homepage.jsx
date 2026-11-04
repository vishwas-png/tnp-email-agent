import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, CalendarClock, Inbox, LayoutGrid, Layers, MessageSquareText } from "lucide-react";
import { useAuth } from "@/auth/context";
import { Skeleton } from "@/components/ui/skeleton";
import NotificationBanner from "@/components/NotificationBanner";
import { CategoryChip, DeadlineBadge } from "@/components/NoticeBadges";
import { formatDateTime, formatToday, greeting, nameFromEmail } from "@/lib/format";
import { useStats, useUpcomingDeadlines } from "@/lib/queries";

const STATS = [
  { key: "new_this_week", label: "New this week", icon: Inbox },
  { key: "deadlines_next_7_days", label: "Deadlines in 7 days", icon: CalendarClock },
  { key: "total", label: "Notices tracked", icon: Layers },
];

function StatTiles() {
  const { data, isPending, isError } = useStats();
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {STATS.map(({ key, label, icon: Icon }) => (
        <div key={key} className="glass rounded-xl p-5">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            {label}
            <Icon className="size-4" />
          </div>
          {isPending ? (
            <Skeleton className="mt-3 h-9 w-14" />
          ) : (
            <p className="mt-2 text-3xl font-semibold tabular-nums tracking-tight">{isError ? "–" : data[key]}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function ActionCard({ to, icon: Icon, title, text, tag }) {
  return (
    <Link
      to={to}
      className="glass group relative overflow-hidden rounded-2xl p-6 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-primary/10 focus-visible:ring-[3px] focus-visible:ring-ring/50"
    >
      <span className="pointer-events-none absolute -right-10 -top-10 size-40 rounded-full bg-primary/20 opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100" />
      <div className="relative flex items-start justify-between">
        <span className="grid size-11 place-items-center rounded-xl bg-gradient-to-br from-primary to-placement text-primary-foreground shadow-lg shadow-primary/25">
          <Icon className="size-5" />
        </span>
        {tag && <span className="rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground">{tag}</span>}
      </div>
      <h2 className="relative mt-5 text-lg font-semibold tracking-tight">{title}</h2>
      <p className="relative mt-1 text-sm text-muted-foreground">{text}</p>
      <ArrowRight className="relative mt-5 size-5 text-primary transition-transform group-hover:translate-x-1" />
    </Link>
  );
}

function UpcomingDeadlines() {
  const { data, isPending, isError } = useUpcomingDeadlines();

  return (
    <section className="glass rounded-2xl p-5 sm:p-6" aria-labelledby="upcoming">
      <div className="flex items-center justify-between">
        <h2 id="upcoming" className="font-semibold tracking-tight">Upcoming deadlines</h2>
        <Link to="/dashboard" className="text-sm text-primary hover:underline">View all</Link>
      </div>
      <ul className="mt-4 divide-y">
        {isPending &&
          [0, 1, 2].map((i) => (
            <li key={i} className="flex items-center justify-between py-3">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </li>
          ))}
        {isError && <li className="py-3 text-sm text-muted-foreground">Could not load deadlines.</li>}
        {data?.length === 0 && <li className="py-3 text-sm text-muted-foreground">No upcoming deadlines. Enjoy the calm.</li>}
        {data?.map((n) => (
          <li key={n.gmail_message_id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="truncate font-medium">{n.company_name || n.subject}</p>
              <p className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                <CategoryChip category={n.category} />
                {formatDateTime(n.deadline)}
              </p>
            </div>
            <DeadlineBadge deadline={n.deadline} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function HomePage() {
  const { user } = useAuth();
  const firstName = nameFromEmail(user.email).split(" ")[0];

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <p className="text-sm text-muted-foreground">{formatToday()}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">
          {greeting()}, <span className="text-gradient-accent">{firstName}</span>
        </h1>
      </motion.div>

      <NotificationBanner />
      <StatTiles />

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-1 xl:grid-cols-2">
          <ActionCard to="/dashboard" icon={LayoutGrid} title="Dashboard" text="Browse, search and filter every notice with deadlines at a glance." />
          <ActionCard to="/chatbot" icon={MessageSquareText} title="Chatbot" text="Ask questions about your notices in plain English." tag="Coming soon" />
        </div>
        <div className="lg:col-span-2">
          <UpcomingDeadlines />
        </div>
      </div>
    </div>
  );
}

export default HomePage;
