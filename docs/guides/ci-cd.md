# CI/CD Integration

Integrate Crux into your continuous integration and deployment pipelines.

## GitHub Actions

### Validate Project Config

Add a step to your CI workflow to validate `crux.json`:

```yaml
- name: Validate crux.json
  run: |
    pip install crux-cli
    python -c "
    from crux_cli.manifest import load_crux_json
    from crux_cli.validation import validate_crux_json
    from pathlib import Path
    data = load_crux_json(Path('.'))
    if data:
        ok, errors = validate_crux_json(data)
        if not ok:
            for e in errors:
                print(f'::error::{e}')
            raise SystemExit(1)
    print('crux.json is valid')
    "
```

### Sync on Deploy

```yaml
- name: Install Crux
  run: pip install crux-cli

- name: Setup Crux
  run: crux setup

- name: Sync project
  run: crux sync
```

## Reproducible Environments

The key to reproducible Crux setups in CI:

1. **`crux.json`** is committed to git — declares which MCPs the project needs
2. **`crux sync`** generates `.mcp.json` from the manifest
3. **Secrets** are stored in CI secrets (GitHub Secrets, etc.) and passed via environment variables

```yaml
env:
  WIKIJS_API_KEY: ${{ secrets.WIKIJS_API_KEY }}
steps:
  - run: |
      crux secret set wikijs WIKIJS_API_KEY "$WIKIJS_API_KEY"
      crux sync
```

## Version Pinning

Pin Crux to a specific version in CI:

```yaml
- run: pip install crux-cli==0.1.0
```

Or use the latest:

```yaml
- run: pip install crux-cli
```
