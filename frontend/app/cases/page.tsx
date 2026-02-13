"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type CaseSummary = {
  case_id: string;
  title: string;
  tags: string[];
  difficulty: string;
};

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/cases`)
      .then((res) => res.json())
      .then((data: CaseSummary[]) => setCases(data));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Cases</h1>
      <ul>
        {cases.map((c) => (
          <li key={c.case_id}>
            <Link href={`/cases/${c.case_id}`}>{c.title}</Link> — {c.difficulty} — {c.tags.join(", ")}
          </li>
        ))}
      </ul>
    </main>
  );
}
