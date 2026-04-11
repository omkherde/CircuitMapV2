import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

function Progress({
  className,
  value,
  indicatorClassName,
  duration = 1000,
  ...props
}: React.ComponentProps<typeof ProgressPrimitive.Root> & {
  indicatorClassName?: string
  duration?: number
}) {
  const [displayValue, setDisplayValue] = React.useState(0)

  // On mount: delay briefly so the browser paints 0 state first, then animate to value
  // On updates: animate to new value immediately
  React.useLayoutEffect(() => {
    const timer = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setDisplayValue(value || 0)
      })
    })
    return () => cancelAnimationFrame(timer)
  }, [value])

  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-bg-surface",
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className={cn(
          "h-full w-full flex-1 rounded-full bg-gradient-to-r from-primary to-cyan-400 ease-out",
          indicatorClassName
        )}
        style={{
          transform: `translateX(-${100 - displayValue}%)`,
          transition: `transform ${duration}ms ease-out`
        }}
      />
    </ProgressPrimitive.Root>
  )
}

export { Progress }
