# Plan

Inspect installed provider implementation, then run an explicit synthetic probe
through production WorkerClient/WorkerServer. Change batching only in the probe
worker, leaving deployed code untouched. Counterbalance variants on the same
resident CUDA models. Observe alignment against each generated PCM. Report only
counts, times and resource metrics; retain PCM solely in bounded RAM.

If the screen demonstrates a useful gain, change the single producer setting,
test real cancellation and the existing native reading pipeline, then run local
checks and independent review. Integrate only an unchanged reviewed/CI-passing
head under the existing bounded request. If not, retain a curated investigation
receipt and the existing application behavior. Hearing acceptance is separate.
