# Offline package preparation and restore

Run with existing **Python 3.12.10 x64 and Tk 8.6**. The tools check these facts;
they do not install or upgrade Python, Tk or system software. Virtual
environments are created at their final paths and never moved.

`tools/runtime_packages.py` owns package names, exact pins, wheel metadata,
SHA256 validation and local requirements. `locks/runtime-wheels.json` is the
single artifact lock for controller (7 wheels), STT (21) and TTS (94).
The former controller-only artifact lock was removed after all seven original
filenames, sizes and SHA256 values matched. Existing version pins are unchanged.

## Prepare while online

From the Hugin checkout:

```powershell
python tools/prepare_engines.py --prepare-wheelhouse
python tools/prepare_engines.py --prepare-wheelhouse --apply
```

The first command is read-only. Only explicit preparation Apply accesses PyPI,
the PyTorch CUDA 12.8 index and the fixed Faster Qwen Git archive. It writes
Hugin-owned `.runtime/wheelhouse`, and creates the combined lock only if absent.
Existing published artifact hashes must match; differing bytes are preserved
and rejected. A complete matching wheelhouse is a no-op without downloads.
Source-build environments additionally bind their canonical runtime path.
Foreign junctions, moved environments and older pathless build markers are
preserved and rejected; preparation never adopts or relocates them automatically.

Faster Qwen 0.3.2 is built from Git revision
`a70afc0f81f7f5f8801c3227968f1102f43f211c`. Sox 1.5.0 is also built from its
release sdist because that release supplies no wheel. Both builds use isolated
Hugin-owned Python, setuptools 78.1.0, wheel 0.45.1, no dependency resolution,
and `SOURCE_DATE_EPOCH=315532800`. The lock records source URLs, source hashes,
revision, tool versions and resulting wheel hashes. Preparation retains a
build receipt binding each source build to its wheel bytes. Model files are
never downloaded or loaded here.

## Restore while offline

Initialize the destination from the required Hugin Git checkpoint first.
Provide a verified Hugin source checkout holding the locked model/CUDA bytes.
The wheelhouse may be supplied separately:

```powershell
python tools/restore.py --target C:/HuginRestored --source-root C:/HuginSource --wheelhouse-source C:/HuginSource/.runtime/wheelhouse
python tools/restore.py --target C:/HuginRestored --source-root C:/HuginSource --wheelhouse-source C:/HuginSource/.runtime/wheelhouse --apply
```

Default is a read-only plan; `--install all` is the default and includes all
three environments. `--install controller`, `stt`, `tts` or `none` narrows it.
The plan validates source/target model identity, file hashes, every selected
wheel, Python/Tk, existing environment ownership and available disk space.
The environment expansion reserve is an estimate, shown separately from
observed free bytes.

Apply copies verified local files additively, then installs **only local wheel
URIs with `--no-index --no-deps --require-hashes`**. Pip ignores ambient user,
global and environment configuration and uses no shared cache. Restore never
downloads, resolves dependencies or builds source. An unowned environment,
divergent version, artifact or lock fails before other copies. A failed
installation remains at its owned path for a same-lock retry. Each successful
environment gets a profile-hash proof after exact metadata checks and
`pip check`; repeated Apply keeps that proof and avoids reinstalling packages.

Build and profile environments share an installation-path preflight. Before
starting their Python or writing package inputs, it rejects inner junctions or
symlinks escaping the owned runtime, including package, script, header and data
subtrees. It then asks that interpreter's pip for its actual installation scheme
and checks the interpreter prefix plus all five write destinations. A marker
alone cannot authorize a redirected installation. The same checks run after a
new environment is created. Existing paths are checked afresh; no live filesystem
validation is cached. This is a preflight, not protection against concurrent
filesystem replacement by another actor during an installation.

Python probes and pip both use `-I`, so ambient PYTHONHOME, PYTHONPATH and the
working directory cannot change the checked interpreter layout. The base Python
standard library remains a permitted read-only input; it is not a pip write
destination and is neither traversed nor required to live in the venv. Build
markers use schema 2 and bind the final runtime path. Older pathless build markers
are preserved and rejected; there is no automatic adoption or migration.

These tools do not activate Hugin, input hooks, autostart, audio or models.
Sox's external executable is a separate native prerequisite if a provider path
uses it; the Python wheel does not install it. Real model inference, device
behavior and migration remain separate acceptance checks.

## Evidence boundary

The contract suite includes actual pip/venv installation of a tiny fixture
wheel and guards for corrupt hashes, changed pins/manifests, foreign metadata,
ownership conflicts and Python/Tk preflight. The full offline probe uses all
122 real package wheels in fresh controller/STT/TTS environments, synthetic
25-byte model/CUDA fixtures, socket-blocked child processes and no model
imports. Curated results and exact checkpoint details live in the helper
handoff. Runtime wheels, environments, probe outputs and raw logs stay ignored.

On 14 October 2026, merged main `cf1c70570b790211b54ce27e8a93b8e641703d69`
was restored into `C:/Users/brian/brian-projects/_repos/hugin`: all 29 real
model/CUDA files (5,934,025,392 bytes), 122 real wheels and their manifest,
and three fresh environments at their final paths. Exact versions and all
three `pip check` runs passed. Apply took 279.716 seconds; a repeated Apply
took 63.824 seconds without reinstalling packages. Native Windows checks
passed 44/44 without skips in the restored controller, and its own CPU
Whisper delivered the 17-word synthetic reference exactly once to a RAM target,
then closed all own workers. This full real-file run used local-only inputs
and no-index pip; unlike the earlier fixture probe, its network was not
externally blocked or monitored. No GPU inference or productive migration
was performed. The stable `C:/Users/brian/Hugin` junction targets this clean
main clone; all six original planning files were preserved and hash-checked.
