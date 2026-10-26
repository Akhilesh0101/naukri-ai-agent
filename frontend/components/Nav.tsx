"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Overview" },
  { href: "/hunting", label: "Auto Job Hunting" },
  { href: "/search", label: "URL Search" },
  { href: "/jobs", label: "Jobs" },
  { href: "/applications", label: "Applications" },
  { href: "/resume", label: "Resume & Profile" },
  { href: "/settings", label: "Settings" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <aside className="w-60 shrink-0 bg-white border-r border-slate-200 p-4 hidden md:block">
      <div className="px-2 py-3 mb-4">
        <div className="text-lg font-bold text-brand">Naukri AI Agent</div>
        <div className="text-xs text-slate-400">Local · Personal use</div>
      </div>
      <nav className="space-y-1">
        {links.map((l) => {
          const active = path === l.href;
          return (
            <Link key={l.href} href={l.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                active ? "bg-brand text-white" : "text-slate-600 hover:bg-slate-100"
              }`}>
              {l.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
