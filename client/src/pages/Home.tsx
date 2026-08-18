import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import CosmicNav from "@/components/CosmicNav";
import { startLogin } from "@/const";
import { ArrowRight, FileText, HeartHandshake, LockKeyhole, Sparkles } from "lucide-react";
import { useLocation } from "wouter";

export default function Home() {
  const { isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();
  const begin = () => isAuthenticated ? setLocation("/create") : startLogin();

  return (
    <div className="cosmos">
      <CosmicNav />
      <main className="relative z-10 mx-auto grid min-h-[calc(100vh-5.5rem)] max-w-6xl items-center gap-10 px-5 pb-16 pt-8 md:grid-cols-[1.15fr_.85fr] md:px-8 md:pt-0">
        <section className="max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-cyan-200/5 px-3 py-1.5 text-xs font-medium tracking-[.12em] text-cyan-100/90"><Sparkles className="h-3.5 w-3.5" />EVIDENCE-AWARE CALCULATION REPORTS</div>
          <h1 className="space-font luminous-text max-w-xl text-5xl font-semibold leading-[.98] tracking-tight text-slate-50 sm:text-6xl">Find a clearer<br /><span className="text-cyan-200">orbit for your work.</span></h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-slate-300 sm:text-lg">A private, birth-data-first calculation report with a clear line between symbolic calculations and measurements you actually provide.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button onClick={begin} size="lg" className="bg-cyan-200 px-5 text-slate-950 shadow-[0_0_30px_rgba(82,235,244,.35)] hover:bg-cyan-100">Start your report <ArrowRight className="ml-2 h-4 w-4" /></Button>
            <Button onClick={() => isAuthenticated ? setLocation("/compatibility") : startLogin()} size="lg" variant="outline" className="border-violet-300/30 bg-violet-300/[.07] text-violet-100 hover:bg-violet-200/10 hover:text-white"><HeartHandshake className="mr-2 h-4 w-4" />Compare two people</Button>
            {isAuthenticated && <Button onClick={() => setLocation("/reports")} size="lg" variant="outline" className="border-cyan-200/30 bg-white/[.03] text-cyan-50 hover:bg-cyan-100/10 hover:text-white">View history</Button>}
          </div>
          <div className="mt-10 grid max-w-xl gap-3 sm:grid-cols-2">
            <div className="flex gap-3 rounded-xl border border-white/10 bg-white/[.035] p-4"><LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-cyan-200" /><p className="text-sm leading-5 text-slate-300"><strong className="block font-medium text-slate-100">Private by account</strong>Your report files are saved only under your signed-in history.</p></div>
            <div className="flex gap-3 rounded-xl border border-white/10 bg-white/[.035] p-4"><FileText className="mt-0.5 h-5 w-5 shrink-0 text-cyan-200" /><p className="text-sm leading-5 text-slate-300"><strong className="block font-medium text-slate-100">English or Arabic</strong>Choose the language before generating or exporting your report.</p></div>
          </div>
        </section>
        <section className="relative mx-auto w-full max-w-sm py-8">
          <div className="orbit-line absolute inset-3 rounded-full border" />
          <div className="orbit-line absolute inset-12 rounded-full border border-dashed" />
          <div className="meteor absolute -right-7 top-16 w-44 opacity-70" />
          <div className="planet relative mx-auto mt-11 h-56 w-56 rounded-full sm:h-64 sm:w-64" />
          <div className="planet-small absolute bottom-7 left-3 h-12 w-12 rounded-full" />
          <div className="stellar-panel relative mx-auto -mt-5 max-w-[18rem] rounded-2xl border border-cyan-100/15 p-4 text-center"><p className="space-font text-xs tracking-[.2em] text-cyan-100/65">YOUR REPORT</p><p className="mt-1 text-sm text-slate-200">Calculations, supplied evidence, and limits — held separately.</p></div>
        </section>
      </main>
    </div>
  );
}
