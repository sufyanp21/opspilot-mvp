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
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./components/ProtectedRoute";
import { Outlet } from "react-router-dom";

function RouteErrorElement() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-2">Route Error</h1>
        <p className="text-gray-600 mb-4">Something went wrong loading this page.</p>
        <button 
          onClick={() => window.location.href = "/"} 
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Go Home
        </button>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  { 
    path: "/login", 
    element: <Login />,
    errorElement: <RouteErrorElement />
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
    errorElement: <RouteErrorElement />,
    children: [
      { index: true, element: <Dashboard />, errorElement: <RouteErrorElement /> },
      { path: "exceptions", element: <Exceptions />, errorElement: <RouteErrorElement /> },
      { path: "reconciliation", element: <Reconciliation />, errorElement: <RouteErrorElement /> },
      { path: "upload", element: <FileUpload />, errorElement: <RouteErrorElement /> },
      { path: "span", element: <SpanAnalysis />, errorElement: <RouteErrorElement /> },
      { path: "otc", element: <OtcProcessing />, errorElement: <RouteErrorElement /> },
      { path: "audit", element: <AuditTrail />, errorElement: <RouteErrorElement /> },
      { path: "demo", element: <Demo />, errorElement: <RouteErrorElement /> },
    ],
  },
  {
    path: "*",
    element: <NotFound />,
    errorElement: <RouteErrorElement />
  }
]);
