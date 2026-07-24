"use client"

import * as React from "react"
import { CheckCircle2, Loader2, XCircle } from "lucide-react"

import { AgentProgressEvent } from "@cv-analyzer/shared-types"
import { cn } from "@/lib/utils"

interface ProgressPanelProps {
  events: AgentProgressEvent[]
  currentNode?: string
}

function statusIcon(status: AgentProgressEvent["status"]) {
  switch (status) {
    case "started":
      return <Loader2 className="size-4 animate-spin text-primary" />
    case "completed":
      return <CheckCircle2 className="size-4 text-emerald-500" />
    case "failed":
      return <XCircle className="size-4 text-destructive" />
    default:
      return null
  }
}

export function ProgressPanel({ events, currentNode }: ProgressPanelProps) {
  const completed = events.filter((e) => e.status === "completed").length
  const total = Math.max(events.length, 1)
  const progress = Math.round((completed / total) * 100)

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold tracking-tight">Analyzing…</h2>
        <p className="text-sm text-muted-foreground">
          {currentNode
            ? `Running: ${currentNode}`
            : "Waiting for the analysis to start…"}
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">{progress}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={cn(
              "h-full rounded-full bg-primary transition-all duration-500",
              progress === 0 && "w-0"
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium">Completed steps</h3>
        <ul className="space-y-2">
          {events.map((ev, i) => (
            <li
              key={`${ev.node}-${i}`}
              className="flex items-center gap-3 rounded-md border bg-card px-3 py-2 text-sm"
            >
              {statusIcon(ev.status)}
              <span className="flex-1">{ev.node}</span>
              {ev.message && (
                <span className="text-xs text-muted-foreground">
                  {ev.message}
                </span>
              )}
            </li>
          ))}
          {events.length === 0 && (
            <li className="text-sm text-muted-foreground">
              No steps completed yet.
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
