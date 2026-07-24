import { AnalyzeForm } from "@/components/analyze-form"

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">
          CV Analyzer
        </h1>
        <p className="text-muted-foreground">
          Submit your CV and a brief description to get a personalized
          development roadmap.
        </p>
      </div>
      <AnalyzeForm />
    </div>
  )
}
