# AI collaboration

Start with the root [AGENTS.md](../AGENTS.md). It contains durable project
conventions and a source map; keep task-specific discussion in task briefs.

## Start a task

For a small request, paste the fields from the [task template](../.ai/task-template.md)
into your prompt. For work spanning sessions or teammates, copy it into
`.ai/tasks/<short-task-name>.md`, creating the directory if needed. Replace all
placeholders and choose one status. Record an owner and branch when useful.

Describe an observable result, a few acceptance criteria, relevant paths, and
anything out of scope. Specify verification commands that fit the change.
Use one focused task per branch/session where practical and commit shared briefs
with the related work. Check local changes before editing shared files.

Example prompt:

```text
Implement .ai/tasks/book-detail-accessibility.md.
Read AGENTS.md and the relevant template and tests first.
Meet the listed acceptance criteria and record verification results.
```

## Keep context small

- Link to specific documentation sections or symbols instead of pasting whole docs.
- Search before reading, then inspect the relevant code and its callers/tests.
- Read archived feature plans only when historical context is necessary.
- Put stable decisions in the relevant reference doc; avoid duplicate summaries.
- Keep the active task current instead of appending a transcript of every attempt.

## Finish and transfer work

Use the [handoff template](../.ai/handoff-template.md) in the final response.
For a session transfer or unfinished task, save it to
`.ai/handoffs/<short-task-name>.md` and link it from the task brief. Create the
directory when first needed. Update that handoff in place; aim for 5–10 lines.
Include exact verification commands/results and any uncommitted work or blocker.
Never include credentials or private user data.

Mark criteria complete only with implementation/review evidence. If a check could
not run, say why. Ask the next collaborator to inspect the working tree and
confirm the current state before relying on an older handoff.

## Close a feature

Mark the task complete and retain its short outcome. Move large completed plans
under `docs/archive/<feature>/` when their history is useful, then update links.
Archived checklists describe their recorded review date; closure does not imply
that every old checkbox was independently verified again.

The PatternFly migration was closed per maintainer confirmation on November 23,
2026. Its [archive](archive/patternfly/README.md) retains historical evidence.
