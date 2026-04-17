import Link from "next/link";
import { Bot, History, Home } from "lucide-react";

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200/70 bg-white/80 backdrop-blur dark:border-zinc-800/70 dark:bg-zinc-950/70">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-sm">
            <Bot className="h-5 w-5" aria-hidden />
          </span>
          <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            AI Agent Team
          </span>
          <span className="rounded-full border border-zinc-200 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-500 dark:border-zinc-800">
            v4
          </span>
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-1 text-sm">
          <NavLink href="/" icon={<Home className="h-4 w-4" />}>Launch</NavLink>
          <NavLink href="/runs" icon={<History className="h-4 w-4" />}>History</NavLink>
        </nav>
      </div>
    </header>
  );
}

function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-50"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
