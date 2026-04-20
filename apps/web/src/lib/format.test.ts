import { describe, expect, it } from "vitest";
import { formatDateLabel, formatHours } from "./format";

describe("format helpers", () => {
  it("formats hours to one decimal place", () => {
    expect(formatHours(3)).toBe("3.0 hr");
    expect(formatHours(3.26)).toBe("3.3 hr");
  });

  it("formats ISO dates into readable labels", () => {
    expect(formatDateLabel("2026-04-17")).toContain("2026");
  });
});
