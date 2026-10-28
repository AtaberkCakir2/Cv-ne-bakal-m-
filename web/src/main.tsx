import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { isRetryable } from "./api/client";
import "./index.css";
import { router } from "./routes";

const queryClient = new QueryClient({
  defaultOptions: {
    // Ağ ve 5xx hatalarında bir kez yeniden dene; 4xx kalıcıdır, hemen gösterilsin.
    queries: { retry: (count, error) => count < 1 && isRetryable(error), refetchOnWindowFocus: false },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
