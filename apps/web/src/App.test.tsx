import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("labels the current product stage honestly", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /tailor the evidence, never invent the person/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      /document analysis is not available yet/i,
    );
  });

  it("renders all planned review workflow stages", () => {
    render(<App />);

    expect(screen.getAllByRole("listitem")).toHaveLength(8);
    expect(screen.getByText("Review changes")).toBeInTheDocument();
  });
});
