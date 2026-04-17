import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Scrubber } from "@/components/Scrubber";
import type { AgentStateEvent } from "@/lib/types";

function ev(
  role: string,
  state: AgentStateEvent["state"],
  detail: string,
  at: number,
): AgentStateEvent {
  return {
    task_id: "t-share",
    agent_role: role,
    state,
    detail,
    ts: new Date(at).toISOString(),
  };
}

const EVENTS: AgentStateEvent[] = [
  ev("researcher", "active", "start", 0),
  ev("researcher", "completed", "done", 500),
  ev("analyst", "active", "work", 1_000),
  ev("analyst", "completed", "done", 1_500),
];

describe("Scrubber", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("initial index is events.length (shows full run)", () => {
    const onChange = vi.fn();
    render(<Scrubber events={EVENTS} index={EVENTS.length} onChange={onChange} />);
    const slider = screen.getByRole("slider", { name: /scrub run/i });
    expect(slider).toHaveAttribute("aria-valuenow", String(EVENTS.length));
    expect(slider).toHaveAttribute("aria-valuemax", String(EVENTS.length));
  });

  it("drag to 0 emits onChange(0) and shows empty-prefix label", () => {
    const onChange = vi.fn();
    render(<Scrubber events={EVENTS} index={EVENTS.length} onChange={onChange} />);
    const slider = screen.getByRole("slider", { name: /scrub run/i });
    fireEvent.change(slider, { target: { value: "0" } });
    expect(onChange).toHaveBeenCalledWith(0);

    // Re-render at index 0 — the position label reads 0 / N.
    render(<Scrubber events={EVENTS} index={0} onChange={onChange} />);
    expect(screen.getAllByText(/0 \/ 4/)[0]).toBeInTheDocument();
  });

  it("play advances the index through events over time (fake timers)", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <Scrubber events={EVENTS} index={0} onChange={onChange} />,
    );

    // Press play.
    fireEvent.click(screen.getByRole("button", { name: /play/i }));

    // Advance 1s — at least one tick should have fired and moved the index.
    act(() => {
      vi.advanceTimersByTime(1_000);
    });
    // After a second, we expect onChange to have been called at least once
    // with an index > 0.
    expect(onChange).toHaveBeenCalled();
    const highest = Math.max(
      ...onChange.mock.calls.map((c) => c[0] as number),
    );
    expect(highest).toBeGreaterThan(0);

    // Re-render with the advanced index and make sure the pause button
    // is now the label (component is in playing state).
    rerender(<Scrubber events={EVENTS} index={highest} onChange={onChange} />);
    expect(
      screen.getByRole("button", { name: /pause/i }),
    ).toBeInTheDocument();
  });

  it("keyboard: ArrowRight advances, ArrowLeft steps back, Space toggles play/pause", () => {
    const onChange = vi.fn();
    render(<Scrubber events={EVENTS} index={2} onChange={onChange} />);
    const scrubber = screen.getByTestId("scrubber");

    // Focus the scrubber to receive keyboard events.
    scrubber.focus();

    fireEvent.keyDown(scrubber, { key: "ArrowRight" });
    expect(onChange).toHaveBeenLastCalledWith(3);

    fireEvent.keyDown(scrubber, { key: "ArrowLeft" });
    expect(onChange).toHaveBeenLastCalledWith(1);

    // Space toggles play. Re-render with onChange the slider itself doesn't
    // move on Space, but the play button label flips.
    fireEvent.keyDown(scrubber, { key: " " });
    expect(
      screen.getByRole("button", { name: /pause/i }),
    ).toBeInTheDocument();

    fireEvent.keyDown(scrubber, { key: " " });
    expect(
      screen.getByRole("button", { name: /play/i }),
    ).toBeInTheDocument();
  });
});
