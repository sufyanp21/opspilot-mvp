import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { router } from "./routes";
import { queryClient } from "./lib/query";
import "./index.css";
import BuildBeacon from "@/components/BuildBeacon";
import ErrorBoundary from "@/components/ErrorBoundary";
import { forceUnregisterServiceWorkers } from "@/lib/sw-unregister";

if (import.meta.env.DEV) {
  // Log effective API base for diagnostics in dev
  // eslint-disable-next-line no-console
  console.info("[ENV] VITE_API_BASE=", import.meta.env.VITE_API_BASE);
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <RouterProvider router={router} />
          <BuildBeacon />
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

// Safety: Force-unregister any stale service workers once on load.
// This prevents old cached bundles from showing the legacy UI.
forceUnregisterServiceWorkers();
