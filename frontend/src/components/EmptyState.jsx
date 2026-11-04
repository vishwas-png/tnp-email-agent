import { cn } from "@/lib/utils";

function EmptyState({ icon: Icon, title, children, action, className }) {
  return (
    <div className={cn("glass mx-auto flex max-w-md flex-col items-center rounded-2xl px-6 py-12 text-center", className)}>
      {Icon && (
        <span className="mb-4 grid size-12 place-items-center rounded-xl bg-primary/12 text-primary">
          <Icon className="size-6" />
        </span>
      )}
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      {children && <div className="mt-1.5 text-sm text-muted-foreground">{children}</div>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export default EmptyState;
