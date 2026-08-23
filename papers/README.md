# Papers

This directory contains research papers and technical documentation related to the BH Audit Schema project.

## Contents

### bh-audit-schema-paper.pdf / .tex

**BH Audit Schema: An Open Standard for PHI-Safe Audit Logging in Behavioral Health Systems**

A research paper describing the schema's design principles, threat model,
specification, regulatory control mappings (HIPAA Security Rule, 42 CFR Part 2,
SOC 2), and reference implementation. The paper includes a comparison against
existing audit logging approaches (IHE ATNA, FHIR AuditEvent, CloudTrail,
generic structured logging) and limited production observations from initial
deployment.

- **Format:** LaTeX source and compiled PDF
- **Length:** 12 pages
- **Author:** Tanmaya Kumar (Behavioral Health Open Source)
- **Date:** April 2026
- **Version:** Corresponds to schema v1.1

## Building the PDF

The paper uses standard LaTeX packages (graphicx, hyperref, listings,
tabularx, booktabs, pifont, natbib). To rebuild:

    pdflatex bh-audit-schema-paper.tex
    pdflatex bh-audit-schema-paper.tex
    pdflatex bh-audit-schema-paper.tex

Three passes are required to resolve all cross-references (listings, tables).

## Citation

If you reference this work, please cite:

    Kumar, T. (2026). BH Audit Schema: An Open Standard for PHI-Safe Audit
    Logging in Behavioral Health Systems. Technical Report BHOS-TR-2026-01,
    Behavioral Health Open Source. https://doi.org/10.5281/zenodo.21683079

## Related Documentation

- [Schema specification](../schema/versions/1.1/audit_event.schema.json)
- [Controls mapping](../docs/controls-mapping.md)
- [CHANGELOG](../CHANGELOG.md)
- [Project README](../README.md)

## License

This paper is available under the [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).
You may share and adapt the material with appropriate attribution.
