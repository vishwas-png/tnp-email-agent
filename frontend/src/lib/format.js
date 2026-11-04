const IST = "Asia/Kolkata";
const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

export function formatDateTime(iso) {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: IST,
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function formatToday() {
  return new Intl.DateTimeFormat("en-IN", { timeZone: IST, weekday: "long", day: "numeric", month: "long" })
    .format(new Date());
}

export function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < HOUR) return `${Math.max(1, Math.round(diff / 60000))} min ago`;
  if (diff < DAY) return `${Math.round(diff / HOUR)} h ago`;
  if (diff < 7 * DAY) return `${Math.round(diff / DAY)} d ago`;
  return new Intl.DateTimeFormat("en-IN", { timeZone: IST, day: "numeric", month: "short" }).format(new Date(iso));
}

// tone: "passed" (grey), "urgent" (< 24 h, red), "soon" (< 3 days), "later"
export function deadlineStatus(iso) {
  const left = new Date(iso).getTime() - Date.now();
  if (left <= 0) return { tone: "passed", label: "Deadline passed" };
  if (left < DAY) {
    const hours = Math.max(1, Math.round(left / HOUR));
    return { tone: "urgent", label: `${hours} h left` };
  }
  const days = Math.round(left / DAY);
  return { tone: days <= 3 ? "soon" : "later", label: `${days} day${days === 1 ? "" : "s"} left` };
}

export function greeting() {
  const hour = Number(new Intl.DateTimeFormat("en-IN", { timeZone: IST, hour: "numeric", hourCycle: "h23" }).format(new Date()));
  if (hour < 5) return "Good night";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

// "vishwas.sharma.ug23@nsut.ac.in" -> "Vishwas Sharma". Parts with digits (roll numbers) are dropped.
export function nameFromEmail(email = "") {
  const parts = email.split("@")[0].split(/[._-]+/).filter((p) => p && !/\d/.test(p));
  return parts.map((p) => p[0].toUpperCase() + p.slice(1).toLowerCase()).join(" ") || email;
}

export function initials(name) {
  return name.split(" ").slice(0, 2).map((p) => p[0]).join("").toUpperCase();
}

// apply_link is extracted by the LLM from email text, so treat it as untrusted:
// only allow real web links (blocks javascript: and data: URLs).
export function safeLink(url) {
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : null;
  } catch {
    return null;
  }
}

export const CATEGORIES = {
  placement: { label: "Placement", color: "var(--placement)" },
  internship: { label: "Internship", color: "var(--internship)" },
  general_notice: { label: "Notice", color: "var(--general)" },
};
