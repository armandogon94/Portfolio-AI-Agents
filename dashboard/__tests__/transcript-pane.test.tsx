import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TranscriptPane } from "@/components/TranscriptPane";
import type { AgentStateEvent } from "@/lib/types";

function ev(
  role: string,
  state: AgentStateEvent["state"],
  detail: string,
  at: number,
): AgentStateEvent {
  return {
    task_id: "t-42",
    agent_role: role,
    state,
    detail,
    ts: new Date(at).toISOString(),
  };
}

/**
 * Slice-29c contract for TranscriptPane:
 *  1. one <section> per unique agent_role
 *  2. active section auto-expands; inactive stay collapsed by default
 *  3. auto-scroll sticks to the latest entry of the active section
 *  4. user scroll-up (IntersectionObserver sentinel off-screen) pauses auto-scroll
 *  5. Copy-all on a section writes that agent's transcript to navigator.clipboard
 */
describe("TranscriptPane", () => {
  const originalClipboard = navigator.clipboard;
  const writeText = vi.fn();

  beforeEach(() => {
    writeText.mockReset();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
  });

  afterEach(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: originalClipboard,
    });
  });

  it("renders one section per unique agent_role", () => {
    render(
      <TranscriptPane
        events={[
          ev("researcher", "active", "searching", 1),
          ev("researcher", "completed", "done", 2),
          ev("analyst", "active", "thinking", 3),
        ]}
      />,
    );
    const sections = screen.getAllByRole("group", { name: /transcript for/i });
    expect(sections).toHaveLength(2);
    expect(sections[0]).toHaveAccessibleName(/researcher/i);
    expect(sections[1]).toHaveAccessibleName(/analyst/i);
  });

  it("auto-expands the currently-active agent's section and leaves others collapsed", () => {
    render(
      <TranscriptPane
        events={[
          ev("researcher", "completed", "done", 1),
          ev("analyst", "active", "thinking", 2),
        ]}
      />,
    );
    const analystSection = screen.getByRole("group", {
      name: /transcript for analyst/i,
    });
    const researcherSection = screen.getByRole("group", {
      name: /transcript for researcher/i,
    });

    // Analyst expanded: its entries list has aria-expanded=true on toggle
    const analystToggle = within(analystSection).getByRole("button", {
      name: /toggle analyst transcript/i,
    });
    expect(analystToggle).toHaveAttribute("aria-expanded", "true");
    expect(within(analystSection).getByText("thinking")).toBeVisible();

    const researcherToggle = within(researcherSection).getByRole("button", {
      name: /toggle researcher transcript/i,
    });
    expect(researcherToggle).toHaveAttribute("aria-expanded", "false");
  });

  it("auto-scrolls the active agent's list to the latest entry", () => {
    // jsdom doesn't paint; we assert the imperative scroll call.
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    render(
      <TranscriptPane
        events={[
          ev("researcher", "active", "one", 1),
          ev("researcher", "active", "two", 2),
          ev("researcher", "active", "three", 3),
        ]}
      />,
    );
    expect(scrollIntoView).toHaveBeenCalled();
  });

  it("pauses auto-scroll when the user scrolls up (sentinel off-screen)", () => {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;

    // Stub IntersectionObserver to immediately report "not intersecting"
    // once, then stay that way — simulating the user scrolled up.
    let capturedCallback:
      | ((entries: IntersectionObserverEntry[]) => void)
      | null = null;
    class Stub {
      constructor(cb: (entries: IntersectionObserverEntry[]) => void) {
        capturedCallback = cb;
      }
      observe() {
        capturedCallback?.([
          { isIntersecting: false } as IntersectionObserverEntry,
        ]);
      }
      unobserve() {}
      disconnect() {}
      takeRecords() {
        return [];
      }
    }
    (globalThis as unknown as { IntersectionObserver: typeof Stub })
      .IntersectionObserver = Stub;

    const { rerender } = render(
      <TranscriptPane
        events={[ev("researcher", "active", "one", 1)]}
      />,
    );
    scrollIntoView.mockClear();
    // New event arrives — but user has scrolled up, so auto-scroll must
    // NOT fire.
    rerender(
      <TranscriptPane
        events={[
          ev("researcher", "active", "one", 1),
          ev("researcher", "active", "two", 2),
        ]}
      />,
    );
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("copy-all writes that agent's transcript to navigator.clipboard", async () => {
    render(
      <TranscriptPane
        events={[
          ev("researcher", "active", "searching", 1),
          ev("researcher", "completed", "done", 2),
          ev("analyst", "active", "thinking", 3),
        ]}
      />,
    );
    const researcherSection = screen.getByRole("group", {
      name: /transcript for researcher/i,
    });
    fireEvent.click(
      within(researcherSection).getByRole("button", {
        name: /copy researcher transcript/i,
      }),
    );

    // Give the async handler a microtask to flush.
    await Promise.resolve();

    expect(writeText).toHaveBeenCalledTimes(1);
    const written = writeText.mock.calls[0][0] as string;
    expect(written).toContain("searching");
    expect(written).toContain("done");
    // Only the researcher's events — no analyst content.
    expect(written).not.toContain("thinking");
  });
});
