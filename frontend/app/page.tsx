import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>signout-sim</h1>
      <p>Frontend scaffold is running.</p>
      <p>
        Example scoring page: <Link href="/signouts/demo-id">/signouts/demo-id</Link>
      </p>
    </main>
  );
}
