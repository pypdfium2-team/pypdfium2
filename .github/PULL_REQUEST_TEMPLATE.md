**Important:** External contributors are required to comply with the template.

## Description

<!-- Explain your changes -->

## Checklist

<!--
- Choose the section(s) relevant to your PR and answer the questions. A section is indicated by `### Heading`.
- Non-applying sections can be ignored or removed.
- Place an `x` in the [ ] for yes, leave it empty for no. If a question is not applicable, remove the [ ], but keep the message in place.
- Use the Preview tab to confirm the PR will render correctly.
-->

### Helpers

- [ ] This PR changes helpers code.
- [ ] The change comes with sufficient test cases to confirm correct functionality.
- [ ] Any new test files are under a suitable license and have been registered in `reuse/dep5`.

### Other

- [ ] This PR changes other things, namely: ... <!-- briefly specify what was changed -->

### Setup

- [ ] This PR changes setup code (`setupsrc/`, `setup.py` etc.).
- [ ] I have tested the change does not break internal callers.
- [ ] I believe the change is maintainable and does not cause unreasonable complexity or code pollution.
- [ ] The change does not try to shift a maintenance burden or upstream downstream tasks. *Keep handlers generic, avoid overly downstream-specific or effectively dead code passages.*
- [ ] I have assessed that the targeted use case cannot reasonably be satisfied by existing means, or the change forms a notable improvement over possible alternatives.
- [ ] I believe the targeted use case is supported by pypdfium2-team. *Note that we may not want to support esoteric or artificially restricted setup envs.*
