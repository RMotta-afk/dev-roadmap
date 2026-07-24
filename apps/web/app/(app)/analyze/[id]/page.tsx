"use client"

import * as React from "react"
import { use } from "react"

import { AgentProgressEvent, AnalyzeResult } from "@cv-analyzer/shared-types"
import { ProgressPanel } from "@/components/progress-panel"
import { ResultsView } from "@/components/results-view"
import { subscribeToAnalysis, isFinalEvent } from "@/lib/api"

export default function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const [events, setEvents] = React.useState<AgentProgressEvent[]>([])
  const [currentNode, setCurrentNode] = React.useState<string | undefined>()
  const [result, setResult] = React.useState<AnalyzeResult | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setEvents([])
    setCurrentNode(undefined)
    setResult(null)
    setError(null)

    const subscription = subscribeToAnalysis(id, (event) => {
      setEvents((prev) => [...prev, event])

      if (event.status === "started") {
        setCurrentNode(event.node)
      } else if (event.status === "completed" || event.status === "failed") {
        setCurrentNode(undefined)
      }

      if (isFinalEvent(event)) {
        setResult(event.payload as unknown as AnalyzeResult)
      }
    })

    return () => {
      subscription.close()
    }
  }, [id])

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-destructive">
        <p className="font-medium">Something went wrong</p>
        <p className="text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {result ? (
        <ResultsView result={result} />
      ) : (
        <ProgressPanel events={events} currentNode={currentNode} />
      )}
    </div>
  )
}
