import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:
          "bg-slate-100 text-slate-700",
        success:
          "bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-700",
        warning:
          "bg-gradient-to-r from-amber-100 to-orange-100 text-amber-700",
        destructive:
          "bg-gradient-to-r from-red-100 to-rose-100 text-red-700",
        outline:
          "border border-slate-200 text-slate-700 bg-white",
        secondary:
          "bg-slate-100 text-slate-600",
        pending:
          "bg-gradient-to-r from-slate-100 to-slate-200 text-slate-500",
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
