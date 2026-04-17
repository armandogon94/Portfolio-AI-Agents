import "@testing-library/jest-dom/vitest";
import * as matchers from "vitest-axe/matchers";
import { expect } from "vitest";

// Register vitest-axe's `toHaveNoViolations` assertion globally (slice-29e).
expect.extend(matchers);
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./mocks/server";

// React Flow polls ResizeObserver + matchMedia; jsdom ships neither.
// Define minimal stubs so components can mount in tests.
if (typeof window !== "undefined") {
  if (!window.ResizeObserver) {
    class ResizeObserverStub {
      observe(): void {}
      unobserve(): void {}
      disconnect(): void {}
    }
    (window as unknown as { ResizeObserver: typeof ResizeObserverStub }).ResizeObserver =
      ResizeObserverStub;
  }
  if (!window.matchMedia) {
    window.matchMedia = (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    });
  }
  // jsdom doesn't implement scrollIntoView; TranscriptPane (slice-29c)
  // calls it on a sentinel for auto-scroll. No-op default; tests that
  // want to assert scroll behaviour override it.
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = function scrollIntoView(): void {};
  }
}

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
