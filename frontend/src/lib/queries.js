import { QueryClient, keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { AuthError, apiFetch } from "@/api";

export const PAGE_SIZE = 12;

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      // A 401 already went through apiFetch's refresh-retry; retrying again is pointless.
      retry: (count, error) => !(error instanceof AuthError) && count < 2,
    },
  },
});

function noticesUrl({ category, q, sort, limit, offset }) {
  const params = new URLSearchParams({ limit, offset, sort });
  if (category) params.set("category", category);
  if (q) params.set("q", q);
  return `/notices?${params}`;
}

export function useNotices({ category, q, sort }) {
  return useInfiniteQuery({
    queryKey: ["notices", { category, q, sort }],
    queryFn: ({ pageParam }) => apiFetch(noticesUrl({ category, q, sort, limit: PAGE_SIZE, offset: pageParam })),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => (last.has_more ? pages.length * PAGE_SIZE : undefined),
    placeholderData: keepPreviousData, // keep old cards on screen while a new filter loads
  });
}

export function useUpcomingDeadlines(limit = 4) {
  return useQuery({
    queryKey: ["notices", "upcoming", limit],
    queryFn: () => apiFetch(noticesUrl({ sort: "deadline", limit, offset: 0 })),
    select: (data) => data.items.filter((n) => n.deadline && new Date(n.deadline) > new Date()),
  });
}

export function useStats() {
  return useQuery({ queryKey: ["stats"], queryFn: () => apiFetch("/stats") });
}
