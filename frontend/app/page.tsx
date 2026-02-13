import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>signout-sim</h1>
      <p>Frontend scaffold is running.</p>
      <p>
        <Link href="/cases">View cases</Link>
      </p>
    </main>
  );
}
