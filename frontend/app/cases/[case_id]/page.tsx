"use client";

import { useEffect, useState } from "react";

type CaseSnapshot = {
  one_liner: string;
  active_problems: string[];
  vitals: Record<string, string | number | boolean | null>;
  labs: Record<string, string | number | boolean | null>;
  meds: string[];
  pending: string[];
  code_status: string;
};

type CaseDetail = {
  case_id: string;
  title: string;
  snapshot: CaseSnapshot;
};

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function CaseDetailPage({ params }: { params: { case_id: string } }) {
  const [detail, setDetail] = useState<CaseDetail | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/cases/${params.case_id}?mode=exam`)
      .then((res) => res.json())
      .then((data: CaseDetail) => setDetail(data));
  }, [params.case_id]);

  if (!detail) {
    return <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>Loading case…</main>;
  }

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>{detail.title}</h1>
      <p>{detail.snapshot.one_liner}</p>

      <h2>Active Problems</h2>
      <ul>{detail.snapshot.active_problems.map((item) => <li key={item}>{item}</li>)}</ul>

      <h2>Vitals</h2>
      <ul>{Object.entries(detail.snapshot.vitals).map(([k, v]) => <li key={k}>{k}: {String(v)}</li>)}</ul>

      <h2>Labs</h2>
      <ul>{Object.entries(detail.snapshot.labs).map(([k, v]) => <li key={k}>{k}: {String(v)}</li>)}</ul>

      <h2>Meds</h2>
      <ul>{detail.snapshot.meds.map((item) => <li key={item}>{item}</li>)}</ul>

      <h2>Pending</h2>
      <ul>{detail.snapshot.pending.map((item) => <li key={item}>{item}</li>)}</ul>

      <h2>Code Status</h2>
      <p>{detail.snapshot.code_status}</p>
    </main>
  );
}
