import { notFound } from "next/navigation";

import { serverApiBaseUrl } from "../../../utils/api";

type Props = {
  params: { signout_id: string };
};

type Signout = {
  id: string;
  case_id: string;
  created_at: string;
  illness_severity: string;
  patient_summary: string;
  action_list: string[];
  situational_awareness: string[];
  contingency_plans: string[];
  receiver_synthesis: string;
  free_text: string | null;
};

async function getSignout(signoutId: string): Promise<Signout | null> {
  const response = await fetch(`${serverApiBaseUrl}/api/signouts/${signoutId}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load signout");
  }

  return response.json();
}

export default async function SignoutDetailsPage({ params }: Props) {
  const signout = await getSignout(params.signout_id);

  if (!signout) {
    notFound();
  }

  return (
    <main>
      <h1>Signout {signout.id}</h1>
      <p>Case: {signout.case_id}</p>
      <p>Created at: {new Date(signout.created_at).toLocaleString()}</p>
      <p>Illness severity: {signout.illness_severity}</p>

      <h2>Patient summary</h2>
      <p>{signout.patient_summary}</p>

      <h2>Action list</h2>
      <ul>
        {signout.action_list.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>Situational awareness</h2>
      <ul>
        {signout.situational_awareness.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>Contingency plans</h2>
      <ul>
        {signout.contingency_plans.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>Receiver synthesis</h2>
      <p>{signout.receiver_synthesis}</p>

      {signout.free_text ? (
        <>
          <h2>Free text</h2>
          <p>{signout.free_text}</p>
        </>
      ) : null}
    </main>
  );
}
