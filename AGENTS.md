# Hugin Agent Contract

## Goal

Lokale Windows-App fuer Diktieren und Vorlesen mit Whisper, Qwen und Freya/Tyr als Ersatz fuer Whispering und PipPal.

## Start

Read `README.md`, this file, `CONTEXT.md`, and the exact handoff named by the
task or `CONTEXT.md`. Never infer the task from the newest handoff filename.
Use the current `valhalla-hq/brian-projects` lifecycle contract for shared
rules instead of copying them here.

Complete a clear, bounded request using known context and defaults. Ask one
grouped question only when a missing decision materially changes the result.
Explanation depth does not change authorization.

## Boundaries

- Run Brian Projects preflight and use one exclusive runtime-local worktree for
  each concrete task. Pure initialization creates none.
- Checkpoint only reviewed paths; push `CONTEXT.md` and the exact handoff.
  Treat an unchanged matching remote head as already saved.
- Follow the central bounded-request authorization for routine integration;
  require concrete approval for protected actions and policy/authority changes.
  Never direct/force-push main or bypass a check.
- Commit no secrets, personal raw data, confidential customer sources, or
  large generated media by default. Keep protected source truth external.
