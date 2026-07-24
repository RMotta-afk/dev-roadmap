"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { signOutAction } from "@/app/actions/auth"
import { Button } from "@/components/ui/button"

function Header() {
  const pathname = usePathname()
  const isSignInPage = pathname === "/sign-in"

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container flex h-14 items-center px-4 sm:px-6 lg:px-8">
        {/* Logo / Brand */}
        <div className="flex flex-1 items-center gap-2">
          <Link
            href="/home"
            className="text-lg font-semibold tracking-tight text-foreground hover:text-primary transition-colors"
          >
            DevRoadmap
          </Link>
        </div>

        {!isSignInPage && (
          <form action={signOutAction}>
            <Button type="submit" variant="ghost" size="sm">
              Sign out
            </Button>
          </form>
        )}
      </div>
    </header>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />
      <main className="flex-1 container px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        {children}
      </main>
      <footer className="border-t py-4 text-center text-sm text-muted-foreground">
        <div className="container px-4 sm:px-6 lg:px-8">
          &copy; {new Date().getFullYear()} DevRoadmap. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
