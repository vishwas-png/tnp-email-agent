import { NavLink, Outlet, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Home, LayoutGrid, LogOut, MessageSquareText } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/auth/context";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Background from "@/components/Background";
import Logo from "@/components/Logo";
import ThemeToggle from "@/components/ThemeToggle";
import { initials, nameFromEmail } from "@/lib/format";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Home", icon: Home },
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/chatbot", label: "Chatbot", icon: MessageSquareText },
];

function DesktopNav() {
  return (
    <nav aria-label="Main" className="hidden items-center gap-1 rounded-full border bg-background/40 p-1 md:flex">
      {NAV.map(({ to, label }) => (
        <NavLink key={to} to={to} end className="relative rounded-full px-4 py-1.5 text-sm font-medium">
          {({ isActive }) => (
            <>
              {isActive && (
                <motion.span
                  layoutId="nav-pill"
                  className="absolute inset-0 rounded-full bg-primary/15 ring-1 ring-primary/25"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <span className={cn("relative", isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground")}>
                {label}
              </span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

// Phones get an app-style tab bar at the bottom, where thumbs can reach it.
function MobileNav() {
  return (
    <nav aria-label="Main" className="glass fixed inset-x-3 bottom-3 z-40 flex justify-around rounded-2xl p-1.5 shadow-lg md:hidden">
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[11px] font-medium transition-colors",
              isActive ? "bg-primary/15 text-primary" : "text-muted-foreground"
            )
          }
        >
          <Icon className="size-5" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const name = nameFromEmail(user.email);

  async function handleLogout() {
    await logout();
    queryClient.clear(); // the next person on this browser must not see cached notices
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="rounded-full" aria-label="Account menu">
          <span className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-primary to-placement text-xs font-semibold text-primary-foreground">
            {initials(name)}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel className="font-normal">
          <p className="font-medium">{name}</p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={handleLogout}>
          <LogOut /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function AppLayout() {
  const { pathname } = useLocation();

  return (
    <div className="relative min-h-svh">
      <Background />
      <a href="#main" className="sr-only rounded-md bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50">
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b bg-background/60 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <NavLink to="/" aria-label="TNP Agent home">
            <Logo />
          </NavLink>
          <DesktopNav />
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <UserMenu />
          </div>
        </div>
      </header>
      <motion.main
        id="main"
        key={pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="mx-auto max-w-6xl px-4 pb-28 pt-8 sm:px-6 md:pb-16"
      >
        <Outlet />
      </motion.main>
      <MobileNav />
    </div>
  );
}

export default AppLayout;
