"use client"

import * as React from "react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { submitAnalysis } from "@/lib/api"
import { cn } from "@/lib/utils"

export function AnalyzeForm() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const form = e.currentTarget
      const formData = new FormData(form)
      const res = await submitAnalysis(formData)
      router.push(`/analyze/${res.analysis_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "space-y-5 rounded-lg border bg-card p-5 sm:p-6",
        "text-card-foreground shadow-sm"
      )}
    >
      <div className="space-y-1.5">
        <Label htmlFor="user_name">Name</Label>
        <Input
          id="user_name"
          name="user_name"
          placeholder="Your full name"
          required
        />
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="phone">Phone</Label>
          <Input
            id="phone"
            name="phone"
            type="tel"
            placeholder="+1 234 567 890"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="you@example.com"
            required
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          placeholder="Tell us about your experience, goals, and what you are looking for..."
          rows={5}
          required
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="cv">CV / Resume</Label>
        <Input
          id="cv"
          name="cv"
          type="file"
          accept=".pdf,.doc,.docx,.txt,.md"
          required
        />
        <p className="text-xs text-muted-foreground">
          Accepted formats: PDF, DOC, DOCX, TXT, MD
        </p>
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Submitting…" : "Analyze CV"}
        </Button>
      </div>
    </form>
  )
}
