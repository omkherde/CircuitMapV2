import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold transition-all",
  {
    variants: {
      variant: {
        default:
          "bg-bg-surface text-text-secondary border border-white/[0.08]",
        success:
          "bg-confidence-high/10 text-confidence-high border border-confidence-high/30",
        warning:
          "bg-confidence-moderate/10 text-confidence-moderate border border-confidence-moderate/30",
        destructive:
          "bg-confidence-low/10 text-confidence-low border border-confidence-low/30",
        outline:
          "border border-white/[0.08] text-text-secondary bg-transparent",
        secondary:
          "bg-bg-surface text-text-muted border border-white/[0.08]",
        pending:
          "bg-bg-surface text-text-muted border border-white/[0.08]",
        primary:
          "bg-primary/10 text-primary border border-primary/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
