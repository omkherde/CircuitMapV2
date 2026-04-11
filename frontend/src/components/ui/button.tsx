import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-primary to-cyan-400 text-bg-base font-semibold shadow-lg shadow-primary/25 hover:from-primary/90 hover:to-cyan-300 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5 active:translate-y-0",
        destructive:
          "bg-gradient-to-r from-confidence-low to-rose-600 text-white shadow-lg shadow-confidence-low/25 hover:from-confidence-low/90 hover:to-rose-500 hover:shadow-xl",
        outline:
          "border border-white/[0.08] bg-bg-surface text-text-primary hover:bg-bg-surface-hover hover:border-white/[0.12]",
        secondary:
          "bg-bg-surface text-text-primary border border-white/[0.08] hover:bg-bg-surface-hover hover:border-white/[0.12]",
        ghost:
          "text-text-primary hover:bg-bg-surface",
        link:
          "text-primary underline-offset-4 hover:underline",
        success:
          "bg-gradient-to-r from-confidence-high to-emerald-400 text-bg-base font-semibold shadow-lg shadow-confidence-high/25 hover:from-confidence-high/90 hover:to-emerald-300 hover:shadow-xl hover:shadow-confidence-high/30 hover:-translate-y-0.5 active:translate-y-0",
        action:
          "relative bg-bg-surface border border-primary/30 text-primary font-semibold overflow-hidden hover:border-primary/50 hover:shadow-glow-primary",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-11 rounded-lg px-6 text-base",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
