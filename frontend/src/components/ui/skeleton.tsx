import * as React from "react"

import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn(
        "animate-pulse rounded-md bg-gradient-to-r from-bg-surface via-bg-elevated to-bg-surface bg-[length:200%_100%]",
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
