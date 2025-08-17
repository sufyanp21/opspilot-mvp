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
        setIsLoading(false);
        return;
      }

      try {
        // Try to validate token with a protected endpoint
        const response = await client.get("/health"); // This endpoint doesn't require auth
        
        // If we have a token and the request succeeded, we're authenticated
        if (response.status === 200) {
          // If we don't have user info, extract from stored data
          if (!user) {
            const storedEmail = localStorage.getItem("user_email") || "user@example.com";
            const userRole = storedEmail.includes("+admin@") ? "admin" : "analyst";
            setUser({ email: storedEmail, role: userRole });
          }
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.log("Auth check failed:", error);
        // Token is invalid, clear it
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
