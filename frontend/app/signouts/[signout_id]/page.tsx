"use client";

import { useState } from "react";

type RubricScore = {
  strengths: string[];
  improvements: string[];
  missing_critical: string[];
  subscores: Record<string, number>;
  total_score: number;
  rubric_version: string;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function SignoutScorePage({ params }: { params: { signout_id: string } }) {
  const [score, setScore] = useState<RubricScore | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleScore = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${BACKEND_URL}/api/signouts/${params.signout_id}/score`, {
        method: "POST"
      });
      if (!response.ok) {
        throw new Error(`Unable to score signout (status ${response.status}).`);
      }
      const payload = (await response.json()) as RubricScore;
      setScore(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setScore(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Signout scoring</h1>
      <p>Signout ID: {params.signout_id}</p>
      <button onClick={handleScore} disabled={loading}>
        {loading ? "Scoring..." : "Score this signout"}
      </button>

      {error ? <p style={{ color: "crimson" }}>{error}</p> : null}

      {score ? (
        <section style={{ marginTop: "1.5rem" }}>
          <h2>
            Total score: {score.total_score} <small>({score.rubric_version})</small>
          </h2>

          <h3>Subscores</h3>
          <ul>
            {Object.entries(score.subscores).map(([domain, value]) => (
              <li key={domain}>
                {domain}: {value}
              </li>
            ))}
          </ul>

          <h3>Strengths</h3>
          <ul>
            {score.strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3>Improvements</h3>
          <ul>
            {score.improvements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3>Missing critical</h3>
          <ul>
            {score.missing_critical.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
