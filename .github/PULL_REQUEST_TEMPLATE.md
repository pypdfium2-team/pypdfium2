**Important:** External contributors are required to comply with the template.

## Description

*Explain your changes here*

## Checklist

<!--
- Use the Preview tab to see how the PR will render.
- Answer the questions below, choosing the section(s) relevant to your PR. Non-applying sections shall be set to `closed`.
- Place an `x` in the [ ] for yes, leave it empty for no. If a question is not applicable, remove the [ ], but keep the message in place.
-->

<details open><summary>Helpers</summary>

- [ ] This PR changes helpers code.
- [ ] The change comes with sufficient test cases to confirm correct functionality.
- [ ] Any new test files are under a suitable license and have been registered in `REUSE.toml`.

</details>
<details open><summary>Setup</summary>

- [ ] This PR changes setup code (`setupsrc/`, `setup.py` etc.).
- [ ] I have at least skimmed through [Installation -> With setup][1] and subsections.
- [ ] I have tested the change does not break internal callers.
- [ ] I believe the change is maintainable and does not cause unreasonable complexity or code fragmentation.
- [ ] The change does not shift a maintenance burden or upstream downstream tasks. *Keep handlers generic, avoid overly downstream-specific or (for us) effectively dead code passages.*
- [ ] I have assessed that the targeted use case cannot reasonably be satisfied by existing means, such as [Caller-provided data files][2], or the change forms a notable improvement over possible alternatives.
- [ ] I believe the targeted use case is supported by pypdfium2-team. *Note that we may not want to support esoteric or artificially restricted setup envs.*

</details>
<details open><summary>Other</summary>

- [ ] This PR changes other things, namely: ... <!-- sum up change (keyword/topic) -->

</details>

[1]: https://github.com/pypdfium2-team/pypdfium2?tab=readme-ov-file#from-the-repository--with-setup
[2]: https://github.com/pypdfium2-team/pypdfium2?tab=readme-ov-file#with-caller-provided-data-files
