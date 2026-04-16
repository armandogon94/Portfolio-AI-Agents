import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { server } from "./mocks/server";
import { emptyHistoryHandler } from "./mocks/handlers";

import HistoryTable from "@/components/HistoryTable";

describe("HistoryTable", () => {
  it("renders a row per history entry", async () => {
    render(<HistoryTable />);
    await waitFor(() =>
      expect(screen.getByText(/AI in healthcare/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Renewable energy 2025/i)).toBeInTheDocument();
    expect(screen.getByText(/Crypto regulation/i)).toBeInTheDocument();
  });

  it("renders an empty state when there are no runs", async () => {
    server.use(emptyHistoryHandler);
    render(<HistoryTable />);
    await waitFor(() =>
      expect(screen.getByText(/no runs yet/i)).toBeInTheDocument(),
    );
  });
});
