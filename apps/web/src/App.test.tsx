import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("explains the evidence and approval boundaries", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /turn your real experience into a role-ready cv/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/no invented experience/i)).toBeInTheDocument();
    expect(screen.getByText(/nothing is exported until/i)).toBeInTheDocument();
  });

  it("validates short evidence before calling the API", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/your current cv/i), "Too short");
    await user.type(
      screen.getByLabelText(/job description/i),
      "Also too short",
    );
    await user.click(
      screen.getByRole("button", { name: /analyse my evidence/i }),
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      /at least 50 characters/i,
    );
  });

  it("provides labelled file inputs for supported evidence", () => {
    render(<App />);

    expect(screen.getAllByLabelText(/choose a file/i)).toHaveLength(3);
    expect(
      screen.getByRole("navigation", { name: /alignment progress/i }),
    ).toBeInTheDocument();
  });
});
