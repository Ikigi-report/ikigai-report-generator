import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { Button } from "@/components/ui/button";
import { Link, useLocation } from "wouter";
import { History, LogIn, Orbit } from "lucide-react";

export default function CosmicNav() {
  const { isAuthenticated, loading, user, logout } = useAuth();
  const [, setLocation] = useLocation();

  return (
    <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-5 md:px-8">
      <Link href="/" className="group flex items-center gap-2.5 text-slate-100 no-underline">
        <span className="grid h-9 w-9 place-items-center rounded-full border border-cyan-200/40 bg-cyan-300/10 text-cyan-100 shadow-[0_0_24px_rgba(88,231,223,.28)] transition-transform group-hover:scale-105"><Orbit className="h-5 w-5" /></span>
        <span className="space-font text-base font-semibold tracking-[.18em] sm:text-lg">IKIGAI / COSMOS</span>
      </Link>
      <nav className="flex items-center gap-2">
        {isAuthenticated && <Button onClick={() => setLocation("/reports")} variant="ghost" className="hidden text-cyan-50 hover:bg-cyan-300/10 hover:text-cyan-50 sm:inline-flex"><History className="mr-2 h-4 w-4" />History</Button>}
        {!loading && !isAuthenticated && <Button onClick={startLogin} className="bg-cyan-200 text-slate-950 shadow-[0_0_25px_rgba(84,235,243,.34)] hover:bg-cyan-100"><LogIn className="mr-2 h-4 w-4" />Sign in</Button>}
        {isAuthenticated && <div className="hidden items-center gap-2 pl-2 text-xs text-cyan-100/70 md:flex"><span className="max-w-28 truncate">{user?.name || "Signed in"}</span><button onClick={() => logout()} className="text-cyan-200 underline-offset-4 hover:text-white hover:underline">Sign out</button></div>}
      </nav>
    </header>
  );
}
