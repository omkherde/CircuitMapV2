import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm transition-all",
        "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-slate-900",
        "placeholder:text-slate-400",
        "focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20",
        "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

export { Input }
