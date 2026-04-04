# Ripper Skill

Short guide to use the `ripper` CLI and integrate this repository as a skill.

**Purpose:**
- **Skill:** Expose `ripper` as a system CLI and document installation and usage for automation or other agents.

**Install (development)**:
- From the repository root, install editable for local development:

```bash
pip install --editable .
```

After this, the `ripper` command will be available in your active Python environment.

**Install (recommended for system-wide use)**:
- Use `pipx` to install the package in an isolated environment:

```bash
pipx install .
```

Or build and install a wheel:

```bash
python -m build
pip install dist/ripper-*.whl
```

**Run without installing**:
- Run directly as a module from the project root:

```bash
python -m ripper --help
```

**Basic usage examples:**
- Download a single song (preferring YouTube):

```bash
ripper song -a "Artist Name" -s "Song Title" --source youtube
```

- Download a Spotify playlist to a directory:

```bash
ripper playlist --uri spotify:playlist:YOUR_PLAYLIST_ID --dir ~/Music/Ripper
```

- Rename files to include Spotify IDs:

```bash
ripper rename --directory ~/Downloads
```

**Notes for integrators / agents:**
- The console script is already declared in `pyproject.toml` as `ripper = "ripper.cli:main"`.
- For CI or automation, prefer `pipx install .` or install the wheel to ensure the `ripper` entry point is available.

**Further work:**
- Add packaging metadata (classifiers, long description) if publishing to PyPI.
