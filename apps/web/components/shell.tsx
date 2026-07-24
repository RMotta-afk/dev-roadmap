"use client"

import * as React from "react"
import Link from "next/link"
import { Menu } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

const navItems = [
  { href: "/", label: "Home" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/about", label: "About" },
]

function NavLinks({ onClick }: { onClick?: () => void }) {
  return (
    <>
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          onClick={onClick}
          className={cn(
            "text-sm font-medium text-foreground transition-colors",
            "hover:text-primary",
            "px-3 py-2 rounded-md",
            "block sm:inline-block"
          )}
        >
          {item.label}
        </Link>
      ))}
    </>
  )
}

function Header() {
  const [open, setOpen] = React.useState(false)

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container flex h-14 items-center px-4 sm:px-6 lg:px-8">
        {/* Logo / Brand */}
        <div className="mr-4 flex items-center gap-2">
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight text-foreground hover:text-primary transition-colors"
          >
            DevRoadmap
          </Link>
        </div>

        {/* Desktop nav — hidden on mobile */}
        <nav className="hidden sm:flex flex-1 items-center gap-1">
          <NavLinks />
        </nav>

        {/* Mobile hamburger — visible only on small screens */}
        <div className="flex flex-1 justify-end sm:hidden">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger>
              <Button variant="ghost" size="icon" aria-label="Open menu">
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-3/4 sm:max-w-xs">
              <SheetHeader>
                <SheetTitle className="text-left">Menu</SheetTitle>
              </SheetHeader>
              <nav className="flex flex-col gap-2 mt-4">
                <NavLinks onClick={() => setOpen(false)} />
              </nav>
            </SheetContent>
          </Sheet>
        </div>
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
