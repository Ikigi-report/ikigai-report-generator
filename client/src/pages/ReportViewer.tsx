import { useAuth } from "@/_core/hooks/useAuth";
import CosmicNav from "@/components/CosmicNav";
import { Button } from "@/components/ui/button";
import { startLogin } from "@/const";
import { openDownload } from "@/lib/openDownload";
import { trpc } from "@/lib/trpc";
import { ArrowLeft, Download, FileJson2, FileText, Loader2, Mail, Printer } from "lucide-react";
import { Streamdown } from "streamdown";
import { toast } from "sonner";
import { useLocation, useParams } from "wouter";

export default function ReportViewer() {
  const { isAuthenticated, loading } = useAuth();
  const [, setLocation] = useLocation();
  const params = useParams<{ id: string }>();
  const reportId = Number(params.id);
  const report = trpc.reports.get.useQuery({ id: reportId }, { enabled: isAuthenticated && Number.isInteger(reportId) && reportId > 0 });
  const download = trpc.reports.download.useMutation({ onSuccess: data => { try { openDownload(data.downloadUrl); } catch (error) { toast.error(error instanceof Error ? error.message : "The download link could not be opened."); } }, onError: error => toast.error(error.message) });
  const exportPdf = trpc.reports.exportPdf.useMutation({ onSuccess: data => { try { openDownload(data.downloadUrl); } catch (error) { toast.error(error instanceof Error ? error.message : "The PDF download link could not be opened."); } }, onError: error => toast.error(error.message) });

  if (!loading && !isAuthenticated) return <div className="cosmos"><CosmicNav /><main className="relative z-10 mx-auto max-w-xl px-5 py-20 text-center"><div className="stellar-panel rounded-3xl border border-cyan-100/15 p-8"><h1 className="space-font text-3xl font-semibold text-white">This report is private.</h1><p className="mt-3 text-slate-300">Sign in to view reports saved under your account.</p><Button className="mt-6 bg-cyan-200 text-slate-950 hover:bg-cyan-100" onClick={startLogin}>Sign in</Button></div></main></div>;

  const isCompatibility = report.data?.report.reportType === "compatibility";
  const reportTitle = isCompatibility && report.data?.report.secondaryName ? `${report.data.report.recipientName} × ${report.data.report.secondaryName}` : report.data?.report.recipientName;

  return <div className="cosmos"><CosmicNav /><main className="relative z-10 mx-auto max-w-6xl px-5 pb-16 pt-5 md:px-8"><div className="flex flex-wrap items-center justify-between gap-3"><Button variant="ghost" onClick={() => setLocation("/reports")} className="text-cyan-100 hover:bg-cyan-100/10 hover:text-white"><ArrowLeft className="mr-2 h-4 w-4" />Report history</Button>{report.data && <div className="flex flex-wrap gap-2"><Button variant="outline" disabled={download.isPending} onClick={() => download.mutate({ id: report.data.report.id, format: "markdown" })} className="border-cyan-100/25 bg-white/[.03] text-cyan-50 hover:bg-cyan-100/10 hover:text-white"><FileText className="mr-2 h-4 w-4" />Markdown</Button><Button variant="outline" disabled={download.isPending} onClick={() => download.mutate({ id: report.data.report.id, format: "calculations" })} className="border-cyan-100/25 bg-white/[.03] text-cyan-50 hover:bg-cyan-100/10 hover:text-white"><FileJson2 className="mr-2 h-4 w-4" />JSON</Button><Button disabled={exportPdf.isPending} onClick={() => exportPdf.mutate({ id: report.data.report.id })} className="bg-cyan-200 text-slate-950 hover:bg-cyan-100">{exportPdf.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Printer className="mr-2 h-4 w-4" />}{isCompatibility ? (report.data.report.hasPdf ? "Download compatibility PDF" : "Prepare compatibility PDF") : (report.data.report.hasPdf ? "Download PDF" : "Export PDF")}</Button>{isCompatibility && <Button variant="outline" onClick={() => toast.info("Email delivery will unlock after a verified Resend sender and API key are configured.")} className="border-violet-300/30 bg-violet-300/[.07] text-violet-100 hover:bg-violet-200/10 hover:text-white"><Mail className="mr-2 h-4 w-4" />Email PDF</Button>}</div>}</div>{report.isLoading ? <div className="mt-16 flex justify-center text-cyan-100"><Loader2 className="mr-2 h-5 w-5 animate-spin" />Opening report…</div> : report.error ? <div className="stellar-panel mx-auto mt-10 max-w-xl rounded-3xl border border-rose-200/20 p-8 text-center"><h1 className="space-font text-2xl font-semibold text-rose-100">Report unavailable</h1><p className="mt-3 text-slate-300">{report.error.message}</p><Button className="mt-6 bg-cyan-200 text-slate-950 hover:bg-cyan-100" onClick={() => setLocation("/reports")}>Return to history</Button></div> : report.data ? <article className="stellar-panel mx-auto mt-6 max-w-4xl rounded-3xl border border-cyan-100/15 p-5 sm:p-10"><div className="mb-7 border-b border-cyan-100/10 pb-6"><p className="space-font text-xs font-semibold tracking-[.2em] text-cyan-200/70">{isCompatibility ? "SAVED COMPATIBILITY REPORT" : "SAVED REPORT"}</p><h1 className="space-font mt-2 text-3xl font-semibold text-white">{reportTitle}</h1><p className="mt-2 text-sm text-slate-300">{isCompatibility ? "Download a private PDF now. Email delivery is prepared for a verified transactional sender." : "Generated report source. Group A remains supplied-only; Group B remains calculated and symbolic."}</p></div><div className="report-markdown"><Streamdown>{report.data.markdown}</Streamdown></div></article> : null}</main></div>;
}
