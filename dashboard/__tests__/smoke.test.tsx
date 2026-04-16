import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "@/app/page";

describe("Home page smoke", () => {
  it("renders the AI Agent Team Dashboard title", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /ai agent team dashboard/i, level: 1 }),
    ).toBeInTheDocument();
  });
});
