"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { clientApiBaseUrl } from "../../../../utils/api";

type Props = {
  params: { case_id: string };
};

export default function CreateSignoutPage({ params }: Props) {
  const [illnessSeverity, setIllnessSeverity] = useState("Stable");
  const [patientSummary, setPatientSummary] = useState("");
  const [actionList, setActionList] = useState("");
  const [situationalAwareness, setSituationalAwareness] = useState("");
  const [contingencyPlans, setContingencyPlans] = useState("");
  const [receiverSynthesis, setReceiverSynthesis] = useState("");
  const [freeText, setFreeText] = useState("");
  const [signoutId, setSignoutId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setSignoutId(null);

    const response = await fetch(`${clientApiBaseUrl}/api/signouts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        case_id: params.case_id,
        illness_severity: illnessSeverity,
        patient_summary: patientSummary,
        action_list: actionList,
        situational_awareness: situationalAwareness,
        contingency_plans: contingencyPlans,
        receiver_synthesis: receiverSynthesis,
        free_text: freeText || null,
      }),
    });

    if (!response.ok) {
      setErrorMessage("Failed to create signout.");
      return;
    }

    const data: { signout_id: string } = await response.json();
    setSignoutId(data.signout_id);
  }

  return (
    <main>
      <h1>Create Signout for Case {params.case_id}</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Illness severity
          <select
            value={illnessSeverity}
            onChange={(event) => setIllnessSeverity(event.target.value)}
          >
            <option value="Stable">Stable</option>
            <option value="Watcher">Watcher</option>
            <option value="Unstable">Unstable</option>
          </select>
        </label>

        <label>
          Patient summary
          <textarea
            value={patientSummary}
            onChange={(event) => setPatientSummary(event.target.value)}
            required
          />
        </label>

        <label>
          Action list
          <textarea
            value={actionList}
            onChange={(event) => setActionList(event.target.value)}
            required
          />
        </label>

        <label>
          Situational awareness
          <textarea
            value={situationalAwareness}
            onChange={(event) => setSituationalAwareness(event.target.value)}
            required
          />
        </label>

        <label>
          Contingency plans
          <textarea
            value={contingencyPlans}
            onChange={(event) => setContingencyPlans(event.target.value)}
            required
          />
        </label>

        <label>
          Receiver synthesis
          <textarea
            value={receiverSynthesis}
            onChange={(event) => setReceiverSynthesis(event.target.value)}
            required
          />
        </label>

        <label>
          Free text (optional)
          <textarea
            value={freeText}
            onChange={(event) => setFreeText(event.target.value)}
          />
        </label>

        <button type="submit">Create signout</button>
      </form>

      {signoutId ? (
        <p>
          Created signout: {signoutId} ({" "}
          <Link href={`/signouts/${signoutId}`}>View signout</Link>)
        </p>
      ) : null}

      {errorMessage ? <p>{errorMessage}</p> : null}
    </main>
  );
}
