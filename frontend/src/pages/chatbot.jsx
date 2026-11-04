import { motion } from "framer-motion";
import { SendHorizontal, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const EXAMPLES = ["Which internships are still open?", "Did I miss any deadline this week?", "What has TNP said about Acme?"];

// Placeholder until the RAG chatbot (Stage 6) exists. Nothing here is wired up.
function Chatbot() {
  return (
    <div className="mx-auto flex min-h-[60svh] max-w-2xl flex-col items-center justify-center text-center">
      <motion.span
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="grid size-14 place-items-center rounded-2xl bg-gradient-to-br from-primary to-placement text-primary-foreground shadow-xl shadow-primary/30"
      >
        <Sparkles className="size-7" />
      </motion.span>
      <span className="mt-6 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground">Coming soon</span>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">
        Ask your <span className="text-gradient-accent">inbox</span>
      </h1>
      <p className="mt-2 max-w-md text-muted-foreground">
        Soon you can ask questions about your notices and get answers with the source emails shown underneath.
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-2" aria-label="Example questions">
        {EXAMPLES.map((q) => (
          <span key={q} className="glass rounded-full px-3.5 py-1.5 text-sm text-muted-foreground">{q}</span>
        ))}
      </div>

      <div className="glass mt-6 flex w-full items-center gap-2 rounded-full p-1.5 pl-5 opacity-70">
        <Input disabled placeholder="The chatbot is not available yet" aria-label="Chat message" className="h-9 border-0 bg-transparent px-0 shadow-none focus-visible:ring-0 dark:bg-transparent" />
        <Button disabled size="icon" className="rounded-full" aria-label="Send">
          <SendHorizontal />
        </Button>
      </div>
    </div>
  );
}

export default Chatbot;
