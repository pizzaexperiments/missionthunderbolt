# GitHub Actions pause

The maintainer requested a temporary pause after an Actions storage alert.
All five repository workflows were verified as `disabled_manually` on
2026-10-27. No runs were running or queued at the check. Workflow definitions
remain in source for future use; their manual triggers do not authorize a run.

Do not enable, dispatch or add an active Actions workflow until the maintainer
explicitly requests resumption. A billing-cycle reset does not lift this pause.
Run tests/builds locally and post commands, actual results, platform/ABI, failures,
skips and remaining limitations in each PR. Identify APKs with a SHA-256 when
relevant. Keep generated artifacts local; do not upload them to Actions.

The connection can disable individual workflows, but cannot change the global
repository Actions permission setting: GitHub returned HTTP 403 requiring
`administration=write`. All existing workflows are disabled independently. A
repository administrator can additionally choose **Disable actions** under
Settings → Actions → General.

Disabling workflows does not delete existing artifacts/caches or change account
billing budgets. Existing storage was not deleted. The alert is account-level;
this change covers `pizzaexperiments/missionthunderbolt`.
