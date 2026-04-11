import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-10 w-full rounded-lg border border-white/[0.08] bg-bg-surface px-3 py-2 text-sm text-text-primary transition-all",
        "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-text-primary",
        "placeholder:text-text-muted",
        "focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20",
        "disabled:cursor-not-allowed disabled:bg-bg-elevated disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

export { Input }
