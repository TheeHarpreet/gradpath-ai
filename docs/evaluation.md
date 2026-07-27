# Evaluation Strategy

GradPath AI treats evaluation data as a product specification, not as a set of
prompts that merely look realistic. Each case defines the source material, the
claims that source material can support, and facts that the system must never
invent.

## Why evaluation starts before model integration

Language-model output can be fluent while still being wrong. A fixed expected
answer lets us measure whether a later change improves the product or only
changes its wording. It also gives automated tests a stable safety contract.

## Golden-case structure

Each directory under `evals/cases` contains:

- `candidate-cv.md`: fictional CV text supplied by the candidate;
- `job-description.md`: fictional role description supplied by an employer;
- `supporting-evidence.md`: optional candidate-controlled evidence;
- `expected.json`: the reviewable expected requirements, evidence mappings,
  assessments, prohibited claims, and output checks;
- `reference-aligned-cv.md`: one acceptable truthful output, not the only valid
  wording.

Stable source IDs inside the Markdown documents allow expected results and
generated claims to cite exact evidence without relying on fragile line
numbers.

## Assessment labels

- `supported`: the supplied evidence directly demonstrates the requirement;
- `partially_supported`: related evidence exists but does not fully demonstrate
  the stated scope or level;
- `unsupported`: no supplied evidence supports the requirement;
- `uncertain`: the source is ambiguous or contradictory and needs clarification.

## Safety invariants

Every implementation must satisfy these rules:

1. A supported or partially supported assessment cites candidate evidence.
2. Job-description text is never evidence that the candidate has a skill.
3. Unsupported claims never appear as candidate facts in the aligned CV.
4. Metrics, dates, employers, qualifications, and technologies are preserved
   unless candidate-controlled evidence explicitly supports a change.
5. Learning interest is not rewritten as professional experience.
6. A reference CV is an example of acceptable output, not an instruction to
   reproduce its prose verbatim.

## Dataset growth

The first case proves the vertical slice. Later stages will expand to at least
20 cases covering frontend, backend, full-stack, data, conflicting evidence,
prompt injection, missing details, provider failures, and adversarial claims.
