import { createBrowserRouter } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Exceptions from "./pages/Exceptions";
import Reconciliation from "./pages/Reconciliation";
import FileUpload from "./pages/FileUpload";
import SpanAnalysis from "./pages/SpanAnalysis";
import OtcProcessing from "./pages/OtcProcessing";
import AuditTrail from "./pages/AuditTrail";
import Demo from "./pages/Demo";
import Login from "./pages/Login";
import ProtectedRoute from "./components/ProtectedRoute";
import { Outlet } from "react-router-dom";

export const router = createBrowserRouter([
  { 
    path: "/login", 
    element: <Login /> 
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout>
          <Outlet />
        </AppLayout>
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Dashboard /> },
      { path: "exceptions", element: <Exceptions /> },
      { path: "reconciliation", element: <Reconciliation /> },
      { path: "upload", element: <FileUpload /> },
      { path: "span", element: <SpanAnalysis /> },
      { path: "otc", element: <OtcProcessing /> },
      { path: "audit", element: <AuditTrail /> },
      { path: "demo", element: <Demo /> },
    ],
  },
]);
