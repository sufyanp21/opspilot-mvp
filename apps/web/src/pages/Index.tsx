import Dashboard from "./Dashboard";
import { useState } from "react";
import { postJson } from "@/lib/api";
import { setTokens } from "@/lib/auth";
import { Link } from "react-router-dom";

const Index = () => {
  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("demo");
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const t = await postJson<{ access_token: string; refresh_token: string }>("/auth/login", { email, password });
    setTokens(t.access_token, t.refresh_token);
    alert("Logged in");
  }
  return (
    <div className="space-y-6">
      <form className="flex items-center gap-2" onSubmit={handleLogin}>
        <input className="border px-2 py-1" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
        <input className="border px-2 py-1" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" type="password" />
        <button className="border px-3 py-1" type="submit">Login</button>
      </form>
      <Dashboard />
      <div className="grid grid-cols-2 gap-2">
        <Link to="/upload" className="underline">File Upload</Link>
        <Link to="/reconciliation" className="underline">Reconciliation</Link>
        <Link to="/exceptions" className="underline">Exceptions</Link>
        <Link to="/audit" className="underline">Audit</Link>
      </div>
    </div>
  );
};

export default Index;
