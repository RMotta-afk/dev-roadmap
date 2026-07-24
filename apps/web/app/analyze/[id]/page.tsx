"use client"

import * as React from "react"
import { use } from "react"
import Link from "next/link"

import { Loader2 } from "lucide-react"
import { AgentProgressEvent, AnalyzeResult } from "@cv-analyzer/shared-types"
import { ProgressPanel } from "@/components/progress-panel"
import { ResultsView } from "@/components/results-view"
import { subscribeToAnalysis, isFinalEvent } from "@/lib/api"
import { buttonVariants } from "@/components/ui/button"

export default function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  return <AnalysisContent id={id} key={id} />
}

function AnalysisContent({ id }: { id: string }) {
  const [events, setEvents] = React.useState<AgentProgressEvent[]>([])
  const [currentNode, setCurrentNode] = React.useState<string | undefined>()
  const [result, setResult] = React.useState<AnalyzeResult | null>(null)
  const [status, setStatus] = React.useState<"connecting" | "streaming" | "error">(
    "connecting"
  )

  React.useEffect(() => {
    const subscription = subscribeToAnalysis(
      id,
      (event) => {
        setStatus("streaming")
        setEvents((prev) => [...prev, event])

        if (event.status === "started") {
          setCurrentNode(event.node)
        } else if (event.status === "completed" || event.status === "failed") {
          setCurrentNode(undefined)
        }

        if (isFinalEvent(event)) {
          setResult(event.payload as unknown as AnalyzeResult)
        }
      },
      () => setStatus("error")
    )

    return () => {
      subscription.close()
    }
  }, [id])

  if (result) {
    return (
      <div className="mx-auto max-w-3xl space-y-8">
        <ResultsView result={result} />
      </div>
    )
  }

  if (status === "error") {
    return (
      <div className="mx-auto max-w-md space-y-6 text-center">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-destructive">
          <p className="font-medium">Something went wrong</p>
          <p className="text-sm">
            We could not connect to the analysis stream. Please try submitting
            your CV again.
          </p>
        </div>
        <Link href="/home" className={buttonVariants()}>
          Back to home
        </Link>
      </div>
    )
  }

  if (status === "connecting") {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center space-y-4 py-20 text-center">
        <Loader2 className="size-10 animate-spin text-primary" />
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">
            Analyzing your CV…
          </h2>
          <p className="text-sm text-muted-foreground">
            This may take a minute while we build your roadmap.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <ProgressPanel events={events} currentNode={currentNode} />
    </div>
  )
}
