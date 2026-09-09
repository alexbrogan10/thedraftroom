import type { ReactNode } from "react";

export function Card({
  title,
  subtitle,
  children,
  className = "",
  action,
}: {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}) {
  return (
    <div className={`rounded-lg border border-[var(--color-border)] bg-[var(--color-panel)] ${className}`}>
      {(title || action) && (
        <div className="flex items-start justify-between border-b border-[var(--color-border-subtle)] px-4 py-3">
          <div>
            {title && <h3 className="text-sm font-semibold tracking-wide text-[var(--color-text)]">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

export function Loading({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 p-8 text-sm text-[var(--color-text-muted)]">
      <div className="h-3 w-3 animate-pulse rounded-full bg-[var(--color-accent)]" />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-[var(--color-risk-high)]/30 bg-[var(--color-risk-high)]/10 p-4 text-sm text-[var(--color-risk-high)]">
      {message}
    </div>
  );
}
