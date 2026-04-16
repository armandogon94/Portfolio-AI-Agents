import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

import LauncherForm from "@/components/LauncherForm";

describe("LauncherForm", () => {
  it("lists workflows fetched from the API", async () => {
    render(<LauncherForm />);
    await waitFor(() =>
      expect(
        screen.getByText(/Classic 4-agent research pipeline/i),
      ).toBeInTheDocument(),
    );
  });

  it("navigates to /runs/:id after a successful launch", async () => {
    pushMock.mockClear();
    const user = userEvent.setup();
    render(<LauncherForm />);

    await waitFor(() =>
      expect(screen.getByLabelText(/topic/i)).toBeInTheDocument(),
    );
    await user.type(screen.getByLabelText(/topic/i), "AI in healthcare");
    await user.click(screen.getByRole("button", { name: /launch/i }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/runs/new-task-id-from-msw");
    });
  });

  it("shows a validation error when topic is empty", async () => {
    const user = userEvent.setup();
    render(<LauncherForm />);
    await waitFor(() =>
      expect(screen.getByLabelText(/topic/i)).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: /launch/i }));

    expect(
      await screen.findByText(/topic is required/i),
    ).toBeInTheDocument();
  });
});
