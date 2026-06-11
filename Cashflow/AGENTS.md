# Agent instructions

When you change this codebase, **extend what exists**. Do not add parallel implementations of the same behavior.

## Core rule

Every change should leave the codebase **smaller or equally sized**, not larger with duplicates.

1. **Search before you write** — look for similar logic, types, components, helpers, or constants already in the repo.
2. **Reuse or extend** — import and parameterize existing code; add options or props instead of copying.
3. **Delete the old path** — when you move or consolidate logic, remove the superseded code in the same change. Do not leave “just in case” copies.
4. **One source of truth** — each concern (formatting, validation, labels, colors, API shaping, UI patterns) should live in one place.

If you are about to paste the same block twice, stop and extract or reuse.

## What to avoid

- Copy-pasting logic into a second file “for convenience”
- Defining the same type, constant, or helper under a different name
- Inline reimplementations of behavior that already exists in a shared module
- Leaving dead code after a refactor
- Adding a new code path without removing the old one

## General patterns

**Backend**

- Keep route handlers thin: validate, call a service, return a response.
- Put shared business logic in service modules, not in handlers or routers.
- Remove unused imports, dead functions, and duplicate constants in the same change as your feature.

**Frontend**

- Put shared UI in reusable components; use props (`variant`, `size`, etc.) for small differences instead of duplicating markup.
- Put shared formatting and validation in utility modules.
- Define API-related types once; do not redefine the same shape locally.
- After extracting a component or helper, delete the inlined version from the caller.

## Before finishing

- [ ] No duplicate constants, types, or copy-pasted blocks for the same feature
- [ ] Old code removed if replaced
- [ ] New code uses existing helpers and components where applicable
- [ ] Tests and typechecks still pass for the areas you touched

## When duplication is acceptable

Only when two pieces are **genuinely different** (different contract, lifecycle, or UX) and sharing would force awkward coupling. If you choose not to reuse, add a brief comment explaining why.
