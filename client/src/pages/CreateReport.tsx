import { useAuth } from "@/_core/hooks/useAuth";
import CosmicNav from "@/components/CosmicNav";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { startLogin } from "@/const";
import { measurementLabels, reportRequestSchema, supportedMeasurementKeys, type MeasurementKey } from "@shared/reportValidation";
import { trpc } from "@/lib/trpc";
import { ArrowLeft, ArrowRight, CheckCircle2, CircleAlert, Compass, FileCheck2, Languages, Loader2, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useLocation } from "wouter";

type MeasurementDraft = { result: string; notes: string; confirmed: boolean };

const fieldClass = "mt-2 h-11 border-cyan-100/15 bg-slate-950/35 text-slate-50 placeholder:text-slate-400/60 focus-visible:border-cyan-200/60 focus-visible:ring-cyan-200/30";
const steps = ["Identity", "Birth data", "Supplied measurements", "Review"];

export default function CreateReport() {
  const { isAuthenticated, loading } = useAuth();
  const [, setLocation] = useLocation();
  const [step, setStep] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState({ fullName: "", arabicName: "", birthDate: "", birthTime: "", birthPlace: "" });
  const [measurements, setMeasurements] = useState<Partial<Record<MeasurementKey, MeasurementDraft>>>({});
  const [language, setLanguage] = useState<"en" | "ar">("en");

  const create = trpc.reports.create.useMutation({
    onSuccess: data => {
      toast.success("Your calculation report is ready.");
      setLocation(`/reports/${data.report.id}`);
    },
    onError: error => toast.error(error.message),
  });

  const updateDraft = (key: keyof typeof draft, value: string) => setDraft(current => ({ ...current, [key]: value }));
  const toggleMeasurement = (key: MeasurementKey, checked: boolean) => setMeasurements(current => {
    if (!checked) {
      const next = { ...current };
      delete next[key];
      return next;
    }
    return { ...current, [key]: { result: "", notes: "", confirmed: false } };
  });
  const updateMeasurement = (key: MeasurementKey, update: Partial<MeasurementDraft>) => setMeasurements(current => ({ ...current, [key]: { ...(current[key] || { result: "", notes: "", confirmed: false }), ...update } }));

  const payload = () => ({
    ...draft,
    language,
    measurements: supportedMeasurementKeys.flatMap(key => {
      const value = measurements[key];
      return value ? [{ key, ...value }] : [];
    }),
  });

  const validate = () => {
    const result = reportRequestSchema.safeParse(payload());
    if (result.success) {
      setErrors({});
      return result.data;
    }
    const next: Record<string, string> = {};
    result.error.issues.forEach(issue => { next[String(issue.path[0] || "form")] = issue.message; });
    setErrors(next);
    return null;
  };

  const stepIsReady = () => {
    if (step === 0) return Boolean(draft.fullName.trim()) && !errors.fullName;
    if (step === 1) return Boolean(draft.birthDate && draft.birthTime && draft.birthPlace.trim());
    if (step === 2) return Object.values(measurements).every(value => !value || (Boolean(value.result.trim()) && value.confirmed));
    return true;
  };

  const next = () => {
    if (step === 0 && !draft.fullName.trim()) return setErrors({ fullName: "Your full Latin-script name is required." });
    if (step === 1 && (!draft.birthDate || !draft.birthTime || !draft.birthPlace.trim())) return setErrors({ form: "Please complete all birth-data fields before continuing." });
    if (step === 2 && !stepIsReady()) return setErrors({ measurements: "Each selected measurement needs a supplied result and confirmation, or you can remove it." });
    setErrors({});
    setStep(current => Math.min(current + 1, steps.length - 1));
  };

  const submit = () => {
    const validated = validate();
    if (!validated) {
      toast.error("Please fix the highlighted information before generating your report.");
      return;
    }
    create.mutate(validated);
  };

  if (!loading && !isAuthenticated) {
    return <div className="cosmos"><CosmicNav /><main className="relative z-10 mx-auto max-w-xl px-5 py-20 text-center"><div className="stellar-panel rounded-3xl border border-cyan-100/15 p-8"><ShieldCheck className="mx-auto h-10 w-10 text-cyan-200" /><h1 className="space-font mt-5 text-3xl font-semibold text-white">Sign in to create a private report</h1><p className="mt-3 text-slate-300">Your report files and calculation record are saved under your own account.</p><Button className="mt-6 bg-cyan-200 text-slate-950 hover:bg-cyan-100" onClick={startLogin}>Sign in to continue</Button></div></main></div>;
  }

  return (
    <div className="cosmos">
      <CosmicNav />
      <main className="relative z-10 mx-auto max-w-4xl px-5 pb-16 pt-5 md:px-8">
        <div className="mx-auto max-w-2xl text-center"><p className="space-font text-xs font-semibold tracking-[.2em] text-cyan-200/70">CALCULATION INTAKE</p><h1 className="space-font luminous-text mt-3 text-4xl font-semibold text-white sm:text-5xl">Set your coordinates.</h1><p className="mx-auto mt-4 max-w-xl text-slate-300">Four short steps. You control what measured information, if any, enters the report.</p></div>
        <div className="mx-auto mt-5 flex max-w-2xl items-center justify-between rounded-2xl border border-cyan-100/12 bg-slate-950/20 p-3"><div className="flex items-center gap-2 text-sm text-slate-200"><Languages className="h-4 w-4 text-cyan-200" />Report language</div><div className="flex rounded-xl border border-cyan-100/15 bg-slate-950/30 p-1"><Button size="sm" onClick={() => setLanguage("en")} className={language === "en" ? "bg-cyan-200 text-slate-950 hover:bg-cyan-100" : "bg-transparent text-slate-300 hover:bg-white/5"}>English</Button><Button size="sm" onClick={() => setLanguage("ar")} className={language === "ar" ? "bg-cyan-200 text-slate-950 hover:bg-cyan-100" : "bg-transparent text-slate-300 hover:bg-white/5"}>العربية</Button></div></div>
        <div className="mx-auto mt-9 grid max-w-2xl grid-cols-4 gap-2">{steps.map((label, index) => <div key={label} className="text-center"><div className={`mx-auto grid h-7 w-7 place-items-center rounded-full text-xs ${index <= step ? "bg-cyan-200 text-slate-950" : "bg-slate-700/60 text-slate-300"}`}>{index < step ? <CheckCircle2 className="h-4 w-4" /> : index + 1}</div><p className={`mt-2 hidden text-[11px] sm:block ${index === step ? "text-cyan-100" : "text-slate-400"}`}>{label}</p></div>)}</div>
        <section className="stellar-panel mx-auto mt-8 max-w-2xl rounded-3xl border border-cyan-100/15 p-5 sm:p-8">
          {step === 0 && <div><div className="mb-7"><p className="space-font text-sm font-semibold tracking-wide text-cyan-100">1. Identity</p><h2 className="mt-2 text-2xl font-semibold text-white">Start with the name you use.</h2><p className="mt-2 text-sm leading-6 text-slate-300">Your Latin-script name is required for the Pythagorean name calculation. Arabic is optional and is used only for Abjad.</p></div><Label htmlFor="fullName" className="text-slate-100">Full name in Latin script <span className="text-cyan-200">required</span></Label><Input id="fullName" value={draft.fullName} onChange={event => updateDraft("fullName", event.target.value)} placeholder="Example: Casey Example" className={fieldClass} autoComplete="name" />{errors.fullName && <p className="mt-2 text-sm text-rose-300">{errors.fullName}</p>}<Label htmlFor="arabicName" className="mt-6 block text-slate-100">Full name in Arabic script <span className="font-normal text-slate-400">optional</span></Label><Input id="arabicName" value={draft.arabicName} onChange={event => updateDraft("arabicName", event.target.value)} placeholder="مثال: الاسم الكامل" className={fieldClass} dir="auto" /></div>}
          {step === 1 && <div><div className="mb-7"><p className="space-font text-sm font-semibold tracking-wide text-cyan-100">2. Birth data</p><h2 className="mt-2 text-2xl font-semibold text-white">Use the closest confirmed record.</h2><p className="mt-2 text-sm leading-6 text-slate-300">Time is sensitive: it may affect house-dependent and timing-based calculated outputs. Confirm it against an official record when possible.</p></div><div className="grid gap-5 sm:grid-cols-2"><div><Label htmlFor="birthDate" className="text-slate-100">Birth date <span className="text-cyan-200">YYYY-MM-DD</span></Label><Input id="birthDate" type="date" value={draft.birthDate} onChange={event => updateDraft("birthDate", event.target.value)} className={fieldClass} /></div><div><Label htmlFor="birthTime" className="text-slate-100">Local birth time <span className="text-cyan-200">24-hour</span></Label><Input id="birthTime" type="time" value={draft.birthTime} onChange={event => updateDraft("birthTime", event.target.value)} className={fieldClass} /></div></div><Label htmlFor="birthPlace" className="mt-6 block text-slate-100">Birth place <span className="text-cyan-200">city and country</span></Label><Input id="birthPlace" value={draft.birthPlace} onChange={event => updateDraft("birthPlace", event.target.value)} placeholder="Example: Sample City, Example Country" className={fieldClass} autoComplete="address-level2" />{errors.form && <p className="mt-3 text-sm text-rose-300">{errors.form}</p>}</div>}
          {step === 2 && <div><div className="mb-7"><p className="space-font text-sm font-semibold tracking-wide text-cyan-100">3. Group A — Supplied Measurements</p><h2 className="mt-2 text-2xl font-semibold text-white">Add real results only, or skip.</h2><p className="mt-2 text-sm leading-6 text-slate-300">These are optional. The report never invents, scores, or infers an uncompleted assessment. A blank section is valid.</p></div><div className="space-y-3">{supportedMeasurementKeys.map(key => { const entry = measurements[key]; return <div key={key} className="rounded-2xl border border-cyan-100/12 bg-slate-950/20 p-4"><div className="flex items-start gap-3"><Checkbox id={`measure-${key}`} checked={Boolean(entry)} onCheckedChange={checked => toggleMeasurement(key, checked === true)} className="mt-1 border-cyan-100/40" /><label htmlFor={`measure-${key}`} className="cursor-pointer text-sm font-semibold text-slate-100">{measurementLabels[key]}<span className="mt-0.5 block font-normal text-slate-400">Only enter a result you received from a completed assessment.</span></label></div>{entry && <div className="mt-4 space-y-3 pl-7"><Textarea value={entry.result} onChange={event => updateMeasurement(key, { result: event.target.value })} placeholder="Paste or summarize the actual result from the completed test." className="min-h-24 border-cyan-100/15 bg-slate-950/35 text-slate-50 placeholder:text-slate-400/60 focus-visible:ring-cyan-200/30" /><Input value={entry.notes} onChange={event => updateMeasurement(key, { notes: event.target.value })} placeholder="Optional source note or boundary for this result" className={fieldClass} /><div className="flex items-center gap-2"><Checkbox id={`confirm-${key}`} checked={entry.confirmed} onCheckedChange={checked => updateMeasurement(key, { confirmed: checked === true })} className="border-cyan-100/40" /><label htmlFor={`confirm-${key}`} className="cursor-pointer text-xs leading-5 text-slate-300">I confirm this is my supplied result from a completed test. It is not calculated from my birth data.</label></div></div>}</div>; })}</div>{errors.measurements && <p className="mt-3 text-sm text-rose-300">{errors.measurements}</p>}</div>}
          {step === 3 && <div><div className="mb-7"><p className="space-font text-sm font-semibold tracking-wide text-cyan-100">4. Review</p><h2 className="mt-2 text-2xl font-semibold text-white">Ready to generate the record.</h2><p className="mt-2 text-sm leading-6 text-slate-300">The generator will calculate implemented symbolic systems from your provided birth data and preserve your Group A inputs exactly as supplied.</p></div><div className="divide-y divide-cyan-100/10 rounded-2xl border border-cyan-100/12 bg-slate-950/20">{[["Latin name", draft.fullName], ["Arabic name", draft.arabicName || "Not supplied"], ["Birth date", draft.birthDate], ["Local birth time", draft.birthTime], ["Birth place", draft.birthPlace], ["Group A measurements", Object.keys(measurements).length ? Object.keys(measurements).map(key => measurementLabels[key as MeasurementKey]).join(", ") : "None supplied"]].map(([label, value]) => <div className="grid gap-1 p-4 sm:grid-cols-[10rem_1fr]" key={label}><span className="text-xs font-medium uppercase tracking-[.12em] text-cyan-100/55">{label}</span><span className="text-sm text-slate-100">{value}</span></div>)}</div><div className="mt-5 flex gap-3 rounded-xl border border-cyan-200/15 bg-cyan-200/[.06] p-3 text-sm leading-6 text-cyan-50"><CircleAlert className="mt-0.5 h-5 w-5 shrink-0 text-cyan-200" />Calculated systems are reflective and not validated predictors of personality, health, future outcomes, or career fit.</div></div>}
          <div className="mt-8 flex items-center justify-between border-t border-cyan-100/10 pt-6"><Button variant="ghost" onClick={() => setStep(current => Math.max(0, current - 1))} disabled={step === 0 || create.isPending} className="text-cyan-100 hover:bg-cyan-100/10 hover:text-white"><ArrowLeft className="mr-2 h-4 w-4" />Back</Button>{step < 3 ? <Button onClick={next} className="bg-cyan-200 text-slate-950 hover:bg-cyan-100">Continue <ArrowRight className="ml-2 h-4 w-4" /></Button> : <Button onClick={submit} disabled={create.isPending} className="bg-cyan-200 text-slate-950 shadow-[0_0_25px_rgba(84,235,243,.3)] hover:bg-cyan-100">{create.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating report…</> : <><FileCheck2 className="mr-2 h-4 w-4" />Generate report</>}</Button>}</div>
        </section>
        {create.isPending && <p className="mt-5 text-center text-sm text-cyan-100/75">The calculation may take 1–2 minutes while place, time-zone, and report outputs are resolved.</p>}
      </main>
    </div>
  );
}
