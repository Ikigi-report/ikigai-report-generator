import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import CreateCompatibility from "./pages/CreateCompatibility";
import CreateReport from "./pages/CreateReport";
import Home from "./pages/Home";
import NotFound from "./pages/NotFound";
import ReportHistory from "./pages/ReportHistory";
import ReportViewer from "./pages/ReportViewer";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/create" component={CreateReport} />
      <Route path="/compatibility" component={CreateCompatibility} />
      <Route path="/reports" component={ReportHistory} />
      <Route path="/reports/:id" component={ReportViewer} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
