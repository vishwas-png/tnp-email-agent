import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BellOff, BellRing, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { alreadyAsked, enableNotifications, getPermission, markAsked, subscribeAndSave } from "@/push";

function NotificationBanner() {
  const [permission, setPermission] = useState(getPermission);
  const [busy, setBusy] = useState(false);

  async function enable() {
    setBusy(true);
    try {
      const result = await enableNotifications();
      setPermission(result);
      if (result === "granted") toast.success("Notifications are on for this device");
    } catch {
      toast.error("Could not turn on notifications. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    const current = getPermission();
    if (current === "granted") {
      // Keep the backend's copy of this device's subscription in sync.
      subscribeAndSave().catch(() => toast.error("Could not register this device for notifications."));
    } else if (current === "default" && !alreadyAsked()) {
      // Ask once, right after the first login. Some browsers ignore prompts that are
      // not caused by a click; the banner button is the fallback.
      markAsked();
      enableNotifications()
        .then(setPermission)
        .catch(() => setPermission(getPermission()));
    }
  }, []);

  const content = {
    default: {
      icon: BellRing,
      title: "Turn on notifications",
      text: "Get an alert on this device the moment a new TNP notice arrives.",
      action: (
        <Button onClick={enable} disabled={busy} className="rounded-full">
          {busy && <Loader2 className="animate-spin" />} Enable
        </Button>
      ),
    },
    denied: {
      icon: BellOff,
      title: "Notifications are blocked",
      text: "Allow them in your browser's site settings (the icon left of the address bar), then reload this page.",
    },
    unsupported: {
      icon: BellOff,
      title: "Notifications not supported",
      text: "This browser cannot receive push notifications. Try Chrome, Edge or Firefox.",
    },
  }[permission];

  return (
    <AnimatePresence>
      {content && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, height: 0 }}
          role="status"
          className="glass flex flex-col gap-4 rounded-xl p-4 sm:flex-row sm:items-center"
        >
          <span
            className={
              permission === "default"
                ? "grid size-10 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary"
                : "grid size-10 shrink-0 place-items-center rounded-lg bg-general/15 text-general"
            }
          >
            <content.icon className="size-5" />
          </span>
          <div className="flex-1">
            <p className="font-medium">{content.title}</p>
            <p className="text-sm text-muted-foreground">{content.text}</p>
          </div>
          {content.action}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default NotificationBanner;
