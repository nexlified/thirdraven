# Publishing Docs

ThirdRaven docs are built with [VitePress](https://vitepress.dev) and published automatically to **GitHub Pages** on every push to `main` that touches the `docs/` directory.

The live site is available at:
```
https://nexlified.github.io/thirdraven/
```

---

## How the workflow works

The workflow lives at `.github/workflows/docs.yml` and has two jobs:

| Job | Runs on | Purpose |
|-----|---------|---------|
| `build` | every PR + push to `main` | Installs deps and runs `npm run docs:build` |
| `deploy` | push to `main` only | Uploads the built `docs/.vitepress/dist/` to GitHub Pages |

The `deploy` job uses the official GitHub Actions:
- [`actions/upload-pages-artifact@v3`](https://github.com/actions/upload-pages-artifact)
- [`actions/deploy-pages@v4`](https://github.com/actions/deploy-pages)

No secrets need to be configured — the workflow uses the default `GITHUB_TOKEN` with the `pages: write` and `id-token: write` permissions that are declared in the YAML.

---

## Manual one-time setup (repository settings)

Before the workflow can deploy, a maintainer with **Admin** access must enable GitHub Pages for the repository **once**.

### Steps

1. Go to **Settings → Pages** in the `nexlified/thirdraven` repository.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Save. No branch or folder needs to be selected — the workflow handles everything.

> **Note:** The "GitHub Actions" source option is only available after at least one successful run of a workflow that uses `actions/deploy-pages`. If you haven't merged a docs change to `main` yet, push one first (e.g., a trivial whitespace change inside `docs/`), then come back to this settings page.

That's it. Every subsequent push to `main` that touches `docs/**` will re-deploy automatically.

---

## Verifying a deployment

1. Open the **Actions** tab and select the **Docs** workflow.
2. Click the latest run triggered by a push to `main`.
3. Expand the **Deploy to GitHub Pages** step — it shows the deployed URL.
4. Navigate to `https://nexlified.github.io/thirdraven/` to confirm.

---

## Custom domain (optional)

To serve the docs from a custom domain (e.g. `docs.thirdraven.app`):

1. Add a `CNAME` file to `docs/` containing your domain name.
2. Update `base` in `docs/.vitepress/config.ts` from `'/thirdraven/'` to `'/'`.
3. Configure your DNS to point to `nexlified.github.io`.
4. In **Settings → Pages**, enter your custom domain and enable **Enforce HTTPS**.

---

## Versioned releases

Currently the docs track the `main` branch and are labelled **dev** in the navigation bar.

When a stable release is cut, versioned docs can be published by:

1. Building the docs at the release tag and copying the output into a `versions/<tag>/` subdirectory of the `gh-pages` branch (or a dedicated static-hosting path).
2. Adding a version switcher to the VitePress nav that links between `dev` and each tagged version.

A concrete implementation can follow once the first stable release is ready. The recommended approach is to extend the existing workflow with a matrix strategy over release tags, or to maintain separate per-version builds that are committed into a `versions/` subdirectory of the `gh-pages` branch.
