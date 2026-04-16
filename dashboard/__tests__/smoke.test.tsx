import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

import Home from "@/app/page";

describe("Home page smoke", () => {
  it("renders the AI Agent Team Dashboard title", async () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /ai agent team dashboard/i, level: 1 }),
    ).toBeInTheDocument();
    // Let MSW's initial /workflows fetch resolve so no unhandled-promise
    // warnings bleed into other tests.
    await waitFor(() =>
      expect(screen.getByLabelText(/topic/i)).toBeInTheDocument(),
    );
  });
});
