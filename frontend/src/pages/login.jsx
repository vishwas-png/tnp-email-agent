import { Navigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertCircle, BellRing, ShieldCheck, Sparkles } from "lucide-react";
import { API_URL } from "@/api";
import { useAuth } from "@/auth/context";
import { Button } from "@/components/ui/button";
import Background from "@/components/Background";
import Logo from "@/components/Logo";
import ThemeToggle from "@/components/ThemeToggle";
import { CategoryChip } from "@/components/NoticeBadges";
import { cn } from "@/lib/utils";

const ERRORS = {
  denied: "Google login was cancelled.",
  state: "That login link expired or was already used. Please try again.",
};

const FEATURES = [
  { icon: Sparkles, title: "AI extraction", text: "Company, role, deadline and next steps pulled out of every email." },
  { icon: BellRing, title: "Instant alerts", text: "A push notification the moment a new notice lands." },
  { icon: ShieldCheck, title: "Private by design", text: "Read-only access. Your Google token is encrypted at rest." },
];

// Illustration only: made-up companies, not real emails.
const PREVIEW = [
  { category: "internship", company: "Acme Labs", role: "SDE Intern", badge: "2 days left", tone: "text-general" },
  { category: "placement", company: "Globex", role: "Data Analyst", badge: "5 h left", tone: "text-destructive" },
  { category: "general_notice", company: "Pre-placement talk", role: "Auditorium, 4 PM", badge: "Tomorrow", tone: "text-primary" },
];

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="size-5">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15A10.6 10.6 0 0 0 12 1 11 11 0 0 0 2.18 7.06l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z" />
    </svg>
  );
}

function PreviewStack() {
  return (
    <div aria-hidden="true" className="relative mx-auto h-[380px] w-full max-w-sm">
      {PREVIEW.map((card, i) => (
        <motion.div
          key={card.company}
          initial={{ opacity: 0, y: 30, rotate: 0 }}
          animate={{ opacity: 1, y: 0, rotate: [-4, 3, -1.5][i] }}
          transition={{ delay: 0.25 + i * 0.12, duration: 0.6, ease: "easeOut" }}
          className={cn("glass absolute inset-x-0 rounded-xl p-5 shadow-2xl shadow-black/10 dark:shadow-black/40", ["top-0", "top-[7.5rem] left-6", "top-[15rem] -left-4"][i])}
        >
          <div className="flex items-center justify-between">
            <CategoryChip category={card.category} />
            <span className={cn("text-xs font-medium", card.tone)}>{card.badge}</span>
          </div>
          <p className="mt-3 font-semibold">{card.company}</p>
          <p className="text-sm text-muted-foreground">{card.role}</p>
        </motion.div>
      ))}
    </div>
  );
}

function LoginPage() {
  const { status } = useAuth();
  const [params] = useSearchParams();
  const error = ERRORS[params.get("error")];

  if (status === "in") {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="relative flex min-h-svh flex-col">
      <Background />
      <header className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <Logo />
        <ThemeToggle />
      </header>

      <main className="mx-auto grid w-full max-w-6xl flex-1 items-center gap-12 px-4 py-10 sm:px-6 lg:grid-cols-2">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-flex items-center gap-2 rounded-full border bg-background/50 px-3 py-1 text-xs font-medium text-muted-foreground">
            <span className="size-1.5 animate-pulse rounded-full bg-internship" />
            For your placement-cell inbox
          </span>
          <h1 className="mt-5 text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
            <span className="text-gradient">Never miss a placement deadline.</span>
          </h1>
          <p className="mt-5 max-w-lg text-base text-muted-foreground sm:text-lg">
            TNP Agent reads your placement-cell emails, pulls out companies, roles and deadlines with AI,
            and alerts you the moment something new arrives.
          </p>

          {error && (
            <p role="alert" className="mt-6 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="size-4" /> {error}
            </p>
          )}

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button asChild size="lg" className="h-12 rounded-full bg-white px-6 text-base text-zinc-900 shadow-lg shadow-primary/20 hover:bg-zinc-100">
              <a href={`${API_URL}/connect-gmail`}>
                <GoogleIcon /> Continue with Google
              </a>
            </Button>
            <p className="text-xs text-muted-foreground sm:max-w-56">
              Asks for read-only Gmail access. Only emails from the TNP cell are read and stored.
            </p>
          </div>

          <ul className="mt-12 grid gap-4 sm:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <li key={title} className="glass rounded-xl p-4">
                <Icon className="size-5 text-primary" />
                <p className="mt-3 text-sm font-medium">{title}</p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{text}</p>
              </li>
            ))}
          </ul>
        </motion.section>

        <div className="hidden lg:block">
          <PreviewStack />
        </div>
      </main>
    </div>
  );
}

export default LoginPage;
