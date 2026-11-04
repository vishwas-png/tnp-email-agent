import { Navigate } from "react-router-dom";
import { Loader2, WifiOff } from "lucide-react";
import { useAuth } from "./context";
import { Button } from "@/components/ui/button";
import Background from "@/components/Background";
import EmptyState from "@/components/EmptyState";
import Logo from "@/components/Logo";

function FullScreen({ children }) {
  return (
    <div className="relative grid min-h-svh place-items-center px-4">
      <Background />
      {children}
    </div>
  );
}

function ProtectedRoute({ children }) {
  const { status, retry } = useAuth();

  if (status === "loading") {
    return (
      <FullScreen>
        <div className="flex flex-col items-center gap-4 text-muted-foreground" role="status">
          <Logo />
          <Loader2 className="size-5 animate-spin" aria-label="Loading" />
        </div>
      </FullScreen>
    );
  }
  if (status === "error") {
    return (
      <FullScreen>
        <EmptyState icon={WifiOff} title="Can't reach the server" action={<Button onClick={retry} className="rounded-full">Try again</Button>}>
          The backend did not answer. Check that it is running, then try again.
        </EmptyState>
      </FullScreen>
    );
  }
  if (status === "out") {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default ProtectedRoute;
