'use client';

export default function Error({ error }: { error: Error & { digest?: string } }) {
  return <div className="text-red-700">Error: {error.message}</div>;
}


