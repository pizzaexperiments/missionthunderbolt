# Sequential branches with integration PR targets

The maintainer authorizes starting dependent work from the preceding PR head,
without waiting for its merge. Every implementation PR now targets `develop`.
List prerequisites and incremental commits in its body. A dependent PR initially
contains prerequisite changes; its diff shrinks as those changes reach `develop`.
Merge approval remains required, and GitHub Actions remains disabled.

The earlier PRs #43 and #44 targeted temporary predecessor branches. GitHub
reported them merged, but `develop` contained only #42. The repair branch carries
the original incremental commits 0cb865d and bd6938b onto live `develop` using
`cherry-pick -x`. Their engine/test content is unchanged. This is integration
repair, not additional gameplay recovery. Never infer integration from a closed
PR alone: verify the base and actual contents of `develop`.

New work can branch from the repair head and target `develop` immediately. It
must identify the repair PR as a prerequisite. Do not merge into a temporary
feature branch, force-push/rewrite existing PR branches, or change `main`.
