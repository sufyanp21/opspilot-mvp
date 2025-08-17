import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useApp } from "@/lib/store";
import client from "@/lib/api";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, setUser } = useApp();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("opspilot_access");
      
      if (!token) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      try {
        // Use the new /auth/me endpoint to validate the token and get user info
        const { data } = await client.get("/auth/me");
        if (data && data.email) {
          setUser({ email: data.email, role: data.roles.includes("admin") ? "admin" : "analyst" });
          setIsAuthenticated(true);
        } else {
          // Token might be valid but something is wrong with the user data
          throw new Error("Invalid user data");
        }
      } catch (error) {
        console.error("Authentication check failed:", error);
        // Token is invalid or expired, clear it
        localStorage.removeItem("opspilot_access");
        localStorage.removeItem("opspilot_refresh");
        localStorage.removeItem("user_email");
        setUser(null);
        setIsAuthenticated(false);
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, [user, setUser]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
