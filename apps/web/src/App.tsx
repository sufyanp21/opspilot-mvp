import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { ThemeProvider } from "@/components/theme-provider";
import AppLayout from "@/components/layout/AppLayout";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import FileUpload from "./pages/FileUpload";
import Reconciliation from "./pages/Reconciliation";
import Exceptions from "./pages/Exceptions";
import RequireAuth from "@/components/RequireAuth";
import SpanAnalysis from "./pages/SpanAnalysis";
import OtcProcessing from "./pages/OtcProcessing";
import AuditTrail from "./pages/AuditTrail";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HelmetProvider>
        <ThemeProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <AppLayout>
                <Routes>
                  <Route path="/" element={<Index />} />
                  <Route path="/upload" element={<RequireAuth><FileUpload /></RequireAuth>} />
                  <Route path="/reconciliation" element={<RequireAuth><Reconciliation /></RequireAuth>} />
                  <Route path="/exceptions" element={<RequireAuth><Exceptions /></RequireAuth>} />
                  <Route path="/span" element={<RequireAuth><SpanAnalysis /></RequireAuth>} />
                  <Route path="/otc" element={<RequireAuth><OtcProcessing /></RequireAuth>} />
                  <Route path="/audit" element={<RequireAuth><AuditTrail /></RequireAuth>} />
                  {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </AppLayout>
            </BrowserRouter>
          </TooltipProvider>
        </ThemeProvider>
      </HelmetProvider>
    </QueryClientProvider>
  );
}
