# Contributing to bh-audit-schema

Thank you for your interest in contributing to the BH Audit Event schema standard.

## How to Contribute

### Reporting Issues

- **Bugs in documentation or examples**: Open a [bug report](https://github.com/bh-healthcare/bh-audit-schema/issues/new?template=bug_report.md)
- **Schema changes**: Open a [schema change request](https://github.com/bh-healthcare/bh-audit-schema/issues/new?template=schema_change_request.md)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Ensure examples validate against the schema
5. Submit a pull request

### What We Accept

| Contribution Type          | Process                                    |
|----------------------------|--------------------------------------------|
| Documentation improvements | Direct PR welcome                          |
| Example additions          | Direct PR welcome (must validate)          |
| Typo fixes                 | Direct PR welcome                          |
| Schema changes             | Requires issue discussion first            |

## Schema Change Process

Schema changes require careful consideration due to their impact on implementations.

### For Additive (Non-Breaking) Changes

1. Open a schema change request issue
2. Discuss with maintainers
3. If approved, submit PR with:
   - Updated schema in `schema/versions/<ver>/`
   - Updated `schema/audit_event.schema.json`
   - Updated CHANGELOG
   - Updated documentation
   - New/updated examples

### For Breaking Changes

Breaking changes require:
1. Strong justification
2. Extended discussion period
3. Migration guide
4. Major version bump

See [docs/versioning.md](docs/versioning.md) for versioning policy.

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Welcome newcomers
- Assume good faith

## Style Guidelines

### Documentation

- Use clear, concise language
- Prefer tables for structured information
- Include examples where helpful
- Avoid marketing language

### JSON Schema

- Use `additionalProperties: false` for strict validation
- Include `description` for all fields
- Use consistent naming (camelCase for fields)
- Keep schemas readable and well-formatted

### Examples

- Must validate against the corresponding schema version
- Use realistic but fictional data
- Never include actual PHI
- Include comments explaining non-obvious choices

## Questions?

Open a discussion or issue if you're unsure about anything. We're happy to help guide contributions.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

