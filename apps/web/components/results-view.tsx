"use client"

import * as React from "react"
import { Target, TrendingUp } from "lucide-react"

import { AnalyzeResult, RoadmapNode } from "@cv-analyzer/shared-types"
import { cn } from "@/lib/utils"

interface ResultsViewProps {
  result: AnalyzeResult
}

function ScoreIndicator({ score }: { score: number }) {
  const clamped = Math.min(100, Math.max(0, score))
  const color =
    clamped >= 75
      ? "text-emerald-500"
      : clamped >= 50
      ? "text-amber-500"
      : "text-destructive"

  return (
    <div className="flex items-center gap-4">
      <div className={cn("text-4xl font-bold tabular-nums", color)}>
        {clamped}
      </div>
      <div className="flex-1 space-y-1">
        <div className="h-3 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={cn("h-full rounded-full transition-all duration-700",
              clamped >= 75 ? "bg-emerald-500" : clamped >= 50 ? "bg-amber-500" : "bg-destructive"
            )}
            style={{ width: `${clamped}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground">Compatibility score (0–100)</p>
      </div>
    </div>
  )
}

function RoadmapCard({ node }: { node: RoadmapNode }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border bg-card p-4 text-card-foreground shadow-sm transition-colors hover:bg-muted/50">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold leading-tight">{node.name}</h4>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
            node.importance >= 8
              ? "bg-destructive/10 text-destructive"
              : node.importance >= 5
              ? "bg-amber-500/10 text-amber-600"
              : "bg-emerald-500/10 text-emerald-600"
          )}
        >
          Importance {node.importance}
        </span>
      </div>
      <p className="text-xs text-muted-foreground line-clamp-3">
        {node.description ?? "No description available."}
      </p>
      <div className="mt-auto flex items-center gap-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5">
          <Target className="size-3" />
          {node.category}
        </span>
        <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5">
          <TrendingUp className="size-3" />
          {node.level}
        </span>
      </div>
    </div>
  )
}

export function ResultsView({ result }: ResultsViewProps) {
  const { level_resume, compatibility_score, personalized_roadmap } = result

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold tracking-tight">Analysis Results</h2>
        <p className="text-muted-foreground">
          Here is what we found based on your CV and description.
        </p>
      </div>

      <section className="space-y-4 rounded-lg border bg-card p-5 sm:p-6">
        <h3 className="text-lg font-semibold">Level Resume</h3>
        <div className="space-y-3 text-sm leading-relaxed">
          <p>{level_resume.summary}</p>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <h4 className="font-medium text-emerald-600 dark:text-emerald-400">
                Strong points
              </h4>
              <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                {level_resume.strong_points.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium text-destructive">Weak points</h4>
              <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                {level_resume.weak_points.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm font-medium">
            <span className="text-muted-foreground">Estimated level:</span>
            <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-primary">
              {level_resume.estimated_level}
            </span>
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-lg border bg-card p-5 sm:p-6">
        <h3 className="text-lg font-semibold">Compatibility Score</h3>
        <ScoreIndicator score={compatibility_score} />
      </section>

      <section className="space-y-4">
        <h3 className="text-lg font-semibold">Personalized Roadmap</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {personalized_roadmap.map((node) => (
            <RoadmapCard key={node.id} node={node} />
          ))}
        </div>
      </section>
    </div>
  )
}
