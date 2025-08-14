import './globals.css';
import Link from 'next/link';
import { ReactNode } from 'react';
import Providers from './providers';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <nav className="bg-white border-b border-gray-200">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-4">
            <div className="font-semibold">OpsPilot</div>
            <Link className="hover:underline" href="/upload">Upload</Link>
            <Link className="hover:underline" href="/results">Results</Link>
            <Link className="hover:underline" href="/risk/changes">Risk Changes</Link>
            <Link className="hover:underline" href="/(recon)/predicted">Predicted Breaks</Link>
            <Link className="hover:underline" href="/(recon)/clusters">Clusters</Link>
            <Link className="hover:underline" href="/(reports)/reg-pack">Reg Pack</Link>
            <Link className="hover:underline" href="/(margin)/impact">Margin Impact</Link>
            <Link className="hover:underline" href="/(recon)/nway">N-way</Link>
            <Link className="hover:underline" href="/(wizard)/demo">Demo</Link>
          </div>
        </nav>
        <Providers>
          <main className="mx-auto max-w-6xl p-4">{children}</main>
        </Providers>
      </body>
    </html>
  );
}


