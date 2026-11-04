import { useEffect, useState } from "react";
import { ArrowDownWideNarrow, Inbox, Loader2, RotateCw, Search, SearchX, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import EmptyState from "@/components/EmptyState";
import NoticeCard, { NoticeCardSkeleton } from "@/components/NoticeCard";
import { CATEGORIES } from "@/lib/format";
import { useNotices } from "@/lib/queries";
import { cn } from "@/lib/utils";

const FILTERS = [{ value: "", label: "All" }, ...Object.entries(CATEGORIES).map(([value, { label }]) => ({ value, label }))];
const SORTS = [
  { value: "received", label: "Newest" },
  { value: "deadline", label: "Deadline" },
];

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function Segmented({ options, value, onChange, label }) {
  return (
    <div role="radiogroup" aria-label={label} className="flex shrink-0 gap-1 rounded-full border bg-background/40 p-1">
      {options.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
            value === o.value ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground"
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Dashboard() {
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("received");
  const [search, setSearch] = useState("");
  const q = useDebounced(search.trim());

  const { data, isPending, isError, refetch, isFetching, fetchNextPage, hasNextPage, isFetchingNextPage, isPlaceholderData } =
    useNotices({ category, q, sort });
  const notices = data?.pages.flatMap((page) => page.items) ?? [];
  const filtered = Boolean(category || q);

  return (
    <div>
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Every verified notice from the TNP cell.</p>
      </div>

      {/* Toolbar: sticks under the header while scrolling */}
      <div className="sticky top-16 z-20 -mx-4 mt-6 border-b bg-background/70 px-4 py-3 backdrop-blur-xl sm:-mx-6 sm:px-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              inputMode="search"
              enterKeyHint="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search company, subject or summary"
              aria-label="Search notices"
              className="h-10 rounded-full bg-background/50 pl-9 pr-9"
            />
            {search && (
              <button onClick={() => setSearch("")} aria-label="Clear search" className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                <X className="size-4" />
              </button>
            )}
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 lg:pb-0">
            <Segmented label="Category" options={FILTERS} value={category} onChange={setCategory} />
            <div className="flex shrink-0 items-center gap-1.5">
              <ArrowDownWideNarrow className="size-4 text-muted-foreground" aria-hidden="true" />
              <Segmented label="Sort by" options={SORTS} value={sort} onChange={setSort} />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6" aria-busy={isFetching}>
        {isError ? (
          <EmptyState
            icon={RotateCw}
            title="Could not load notices"
            action={<Button onClick={() => refetch()} className="rounded-full"><RotateCw /> Try again</Button>}
          >
            The server did not answer. Check that the backend is running.
          </EmptyState>
        ) : isPending ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }, (_, i) => <NoticeCardSkeleton key={i} />)}
          </div>
        ) : notices.length === 0 ? (
          filtered ? (
            <EmptyState
              icon={SearchX}
              title="No matching notices"
              action={<Button variant="secondary" className="rounded-full" onClick={() => { setSearch(""); setCategory(""); }}>Clear filters</Button>}
            >
              Try a different word or category.
            </EmptyState>
          ) : (
            <EmptyState icon={Inbox} title="No notices yet">
              New TNP emails show up here a few minutes after they arrive.
            </EmptyState>
          )
        ) : (
          <>
            <div className={cn("grid gap-4 transition-opacity sm:grid-cols-2 lg:grid-cols-3", isPlaceholderData && "opacity-60")}>
              {notices.map((notice, i) => (
                <NoticeCard key={notice.gmail_message_id} notice={notice} index={i % 12} />
              ))}
            </div>
            {hasNextPage && (
              <div className="mt-8 flex justify-center">
                <Button variant="secondary" className="rounded-full px-6" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
                  {isFetchingNextPage && <Loader2 className="animate-spin" />} Load more
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
