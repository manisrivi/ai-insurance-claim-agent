import { Suspense } from "react";

import { ClaimStatusView } from "./claim-status";

// Server shell: the live status view runs in the browser (it polls the API)
export default function ClaimPage() {
  return (
    <Suspense>
      <ClaimStatusView />
    </Suspense>
  );
}
