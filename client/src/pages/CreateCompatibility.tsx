import { useAuth } from "@/_core/hooks/useAuth";
import CosmicNav from "@/components/CosmicNav";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { startLogin } from "@/const";
import { compatibilityRequestSchema, type CompatibilityRequest } from "@shared/reportValidation";
import { trpc } from "@/lib/trpc";
import { ArrowLeft, CheckCircle2, HeartHandshake, Languages, Loader2, Orbit, ShieldCheck, UsersRound } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useLocation } from "wouter";

type PersonDraft = CompatibilityRequest["personOne"];

const blankPerson = (): PersonDraft => ({ fullName: "", arabicName: "", birthDate: "", birthTime: "", birthPlace: "", consent: false as true });
const fieldClass = "mt-2 h-11 border-cyan-100/15 bg-slate-950/35 text-slate-50 placeholder:text-slate-400/60 focus-visible:border-cyan-200/60 focus-visible:ring-cyan-200/30";

function PersonPanel({ number, person, update, error }: { number: 1 | 2; person: PersonDraft; update: (key: keyof PersonDraft, value: string | boolean) => void; error?: string }) {
  return <section className="rounded-2xl border border-cyan-100/12 bg-slate-950/20 p-4 sm:p-5"><div className="mb-5 flex items-center gap-3"><span className="grid h-8 w-8 place-items-center rounded-full bg-cyan-200 text-sm font-bold text-slate-950">{number}</span><div><h2 className="space-font text-lg font-semibold text-white">Person {number}</h2><p className="text-xs text-slate-400">Birth data used for the symbolic comparison.</p></div></div><div className="grid gap-4 sm:grid-cols-2"><div className="sm:col-span-2"><Label htmlFor={`name-${number}`} className="text-slate-100">Full name in Latin script</Label><Input id={`name-${number}`} value={person.fullName} onChange={event => update("fullName", event.target.value)} placeholder="Example: Casey Example" className={fieldClass} /></div><div className="sm:col-span-2"><Label htmlFor={`arabic-${number}`} className="text-slate-100">Arabic name <span className="font-normal text-slate-400">optional</span></Label><Input id={`arabic-${number}`} value={person.arabicName} onChange={event => update("arabicName", event.target.value)} placeholder="مثال: الاسم الكامل" className={fieldClass} dir="auto" /></div><div><Label htmlFor={`date-${number}`} className="text-slate-100">Birth date</Label><Input id={`date-${number}`} type="date" value={person.birthDate} onChange={event => update("birthDate", event.target.value)} className={fieldClass} /></div><div><Label htmlFor={`time-${number}`} className="text-slate-100">Local time</Label><Input id={`time-${number}`} type="time" value={person.birthTime} onChange={event => update("birthTime", event.target.value)} className={fieldClass} /></div><div className="sm:col-span-2"><Label htmlFor={`place-${number}`} className="text-slate-100">Birth place</Label><Input id={`place-${number}`} value={person.birthPlace} onChange={event => update("birthPlace", event.target.value)} placeholder="Example: Sample City, Example Country" className={fieldClass} /></div></div><div className="mt-5 flex items-start gap-2 rounded-xl border border-cyan-100/10 bg-cyan-200/[.04] p-3"><Checkbox id={`consent-${number}`} checked={person.consent} onCheckedChange={checked => update("consent", checked === true)} className="mt-0.5 border-cyan-100/40" /><Label htmlFor={`consent-${number}`} className="cursor-pointer text-xs leading-5 text-slate-300">I confirm that this person has agreed to this private compatibility report and the use of their supplied birth details.</Label></div>{error && <p className="mt-3 text-sm text-rose-300">{error}</p>}</section>;
}

export default function CreateCompatibility() {
  const { isAuthenticated, loading } = useAuth();
  const [, setLocation] = useLocation();
  const [personOne, setPersonOne] = useState<PersonDraft>(blankPerson());
  const [personTwo, setPersonTwo] = useState<PersonDraft>(blankPerson());
  const [language, setLanguage] = useState<"en" | "ar">("en");
  const [comparisonConsent, setComparisonConsent] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const create = trpc.reports.createCompatibility.useMutation({ onSuccess: data => { toast.success("Compatibility report is ready."); setLocation(`/reports/${data.report.id}`); }, onError: error => toast.error(error.message) });

  const updatePerson = (number: 1 | 2) => (key: keyof PersonDraft, value: string | boolean) => {
    const setter = number === 1 ? setPersonOne : setPersonTwo;
    setter(current => ({ ...current, [key]: value } as PersonDraft));
  };

  const submit = () => {
    const candidate = { personOne, personTwo, language, comparisonConsent };
    const parsed = compatibilityRequestSchema.safeParse(candidate);
    if (!parsed.success) {
      const next: Record<string, string> = {};
      parsed.error.issues.forEach(issue => { next[String(issue.path[0] || "form")] = issue.message; });
      setErrors(next);
      toast.error("Please complete both records and confirm consent before generating.");
      return;
    }
    setErrors({});
    create.mutate(parsed.data);
  };

  if (!loading && !isAuthenticated) return <div className="cosmos"><CosmicNav /><main className="relative z-10 mx-auto max-w-xl px-5 py-20 text-center"><div className="stellar-panel rounded-3xl border border-cyan-100/15 p-8"><ShieldCheck className="mx-auto h-10 w-10 text-cyan-200" /><h1 className="space-font mt-5 text-3xl font-semibold text-white">Sign in to compare two private records</h1><p className="mt-3 text-slate-300">Compatibility reports are stored only under your authenticated history.</p><Button className="mt-6 bg-cyan-200 text-slate-950 hover:bg-cyan-100" onClick={startLogin}>Sign in to continue</Button></div></main></div>;

  return <div className="cosmos"><CosmicNav /><main className="relative z-10 mx-auto max-w-5xl px-5 pb-16 pt-5 md:px-8"><div className="mx-auto max-w-2xl text-center"><div className="inline-flex items-center gap-2 rounded-full border border-cyan-100/15 bg-cyan-200/[.05] px-3 py-1.5 text-xs tracking-[.16em] text-cyan-100"><HeartHandshake className="h-3.5 w-3.5" />TWO-PERSON SYMBOLIC COMPARISON</div><h1 className="space-font luminous-text mt-4 text-4xl font-semibold text-white sm:text-5xl">Compare two paths,<br />not two destinies.</h1><p className="mx-auto mt-4 max-w-2xl text-slate-300">This compares implemented birth-data outputs transparently. It does not score personality, predict a relationship, or replace real conversation and consent.</p></div><div className="mx-auto mt-8 flex max-w-3xl flex-wrap items-center justify-between gap-4 rounded-2xl border border-cyan-100/12 bg-slate-950/20 p-4"><div className="flex items-center gap-3"><Languages className="h-5 w-5 text-cyan-200" /><div><p className="font-medium text-white">Report language</p><p className="text-xs text-slate-400">The view and exported PDF follow this selection.</p></div></div><div className="flex rounded-xl border border-cyan-100/15 bg-slate-950/30 p-1"><Button size="sm" onClick={() => setLanguage("en")} className={language === "en" ? "bg-cyan-200 text-slate-950 hover:bg-cyan-100" : "bg-transparent text-slate-300 hover:bg-white/5"}>English</Button><Button size="sm" onClick={() => setLanguage("ar")} className={language === "ar" ? "bg-cyan-200 text-slate-950 hover:bg-cyan-100" : "bg-transparent text-slate-300 hover:bg-white/5"}>العربية</Button></div></div><div className="mx-auto mt-5 grid max-w-3xl gap-5 md:grid-cols-2"><PersonPanel number={1} person={personOne} update={updatePerson(1)} error={errors.personOne} /><PersonPanel number={2} person={personTwo} update={updatePerson(2)} error={errors.personTwo} /></div><div className="stellar-panel mx-auto mt-5 max-w-3xl rounded-2xl border border-cyan-100/15 p-5"><div className="flex items-start gap-3"><UsersRound className="mt-0.5 h-5 w-5 shrink-0 text-cyan-200" /><div><h2 className="space-font text-lg font-semibold text-white">Comparison consent and boundary</h2><p className="mt-1 text-sm leading-6 text-slate-300">The result will compare only deterministic symbolic outputs. A percentage is a transparent overlap index, not a scientific score or a decision tool for marriage, partnership, hiring, or health.</p><div className="mt-4 flex items-start gap-2"><Checkbox id="comparison-consent" checked={comparisonConsent} onCheckedChange={checked => setComparisonConsent(checked === true)} className="mt-0.5 border-cyan-100/40" /><Label htmlFor="comparison-consent" className="cursor-pointer text-sm leading-5 text-slate-200">I confirm both people agreed to this private symbolic comparison.</Label></div>{errors.comparisonConsent && <p className="mt-2 text-sm text-rose-300">{errors.comparisonConsent}</p>}</div></div><div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-cyan-100/10 pt-5"><Button variant="ghost" onClick={() => setLocation("/create")} className="text-cyan-100 hover:bg-cyan-100/10 hover:text-white"><ArrowLeft className="mr-2 h-4 w-4" />Single-person report</Button><Button onClick={submit} disabled={create.isPending} className="bg-cyan-200 text-slate-950 shadow-[0_0_25px_rgba(84,235,243,.3)] hover:bg-cyan-100">{create.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Comparing records…</> : <><Orbit className="mr-2 h-4 w-4" />Generate compatibility report</>}</Button></div></div>{create.isPending && <p className="mt-5 text-center text-sm text-cyan-100/75">Generating both calculation records and their comparison. This can take 2–3 minutes.</p>}</main></div>;
}
