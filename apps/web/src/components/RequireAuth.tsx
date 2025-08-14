import { isAuthenticated } from "@/lib/auth";
import { Navigate, useLocation } from "react-router-dom";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return <Navigate to="/" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}


