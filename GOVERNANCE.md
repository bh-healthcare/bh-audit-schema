# Governance

This document describes the governance model for the bh-audit-schema project.

## Overview

bh-audit-schema is an open-source project that defines audit event standards for behavioral health systems. The project prioritizes stability, backward compatibility, and community input.

## Roles

### Maintainers

Maintainers are responsible for:
- Reviewing and merging pull requests
- Triaging issues
- Making decisions on schema changes
- Ensuring project quality and consistency
- Releasing new schema versions

Current maintainers are listed in the repository's team settings.

### Contributors

Anyone who contributes to the project through:
- Pull requests
- Issue reports
- Documentation improvements
- Community discussion

## Decision Making

### Documentation and Examples

Minor changes (typos, clarifications, new examples) can be merged by any maintainer after basic review.

### Schema Changes

Schema changes follow a structured process:

#### 1. Proposal Phase

- Open a schema change request issue
- Clearly state motivation and proposed changes
- Identify backward compatibility implications

#### 2. Discussion Phase

- Minimum 7-day discussion period for non-trivial changes
- 14-day discussion period for breaking changes
- Maintainers and community provide feedback

#### 3. Decision Phase

- Maintainers reach consensus on the change
- If no consensus, the change is deferred or rejected
- Breaking changes require unanimous maintainer approval

#### 4. Implementation Phase

- PR submitted with all required updates
- Review by at least one maintainer
- Merge and release

### Versioning Decisions

- Minor version bumps: Any maintainer can approve
- Major version bumps: Requires all maintainers to approve

## Release Process

1. Maintainer proposes release with changelog summary
2. Other maintainers review
3. Tag release in git
4. Update `schema/audit_event.schema.json` to latest version
5. Announce release (if applicable)

## Becoming a Maintainer

Maintainers are added based on:
- Sustained, quality contributions
- Demonstrated understanding of project goals
- Invitation from existing maintainers

## Conflict Resolution

If maintainers cannot reach consensus:
1. Extended discussion period (additional 7 days)
2. If still unresolved, the change is deferred
3. Deferred changes can be revisited after 30 days

## Changes to Governance

Changes to this governance document require:
- PR with proposed changes
- 14-day discussion period
- Approval from all maintainers

## Contact

For governance questions, open an issue or contact the maintainers through GitHub.

