# FraudRAG landing page — publication steps

The static website is `docs/index.html`. Its original, inline CSS and vector images under `docs/assets/` require **no JavaScript, package manager, third-party CDN or GitHub Actions workflow**.

## Preview locally

From a checkout of the documentation branch:

```bash
python -m http.server 8008 --directory docs
```

Open `http://localhost:8008/`. Check desktop and narrow mobile layouts, keyboard focus, links, alt text and horizontal scrolling for the architecture diagram and evidence table.

## Enable GitHub Pages after PR review

1. Merge the focused documentation PR into `main`; do **not** merge experimental research PR #1 just to publish the website.
2. Open **GitHub → FraudRAG → Settings → Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Choose branch **main**, directory **/docs**, and save.
5. Once GitHub reports a successful deployment, open the expected project URL: `https://akshaysharma1088.github.io/fraudrag/`.
6. Check internal links, DOI resolution, mobile responsiveness and the final footer against the published site. If Pages is already configured differently, reconcile the existing source before changing the setting.

**Site creation in GitHub does not itself confirm a live website.** GitHub Pages must be enabled and deployed by a repository administrator.

## Metadata and release checklist

- [ ] Verify whether Zenodo DOI `10.5281/zenodo.23679156` resolves publicly and that its record title, author, resource type, version and license correspond to this repository. DOI was provided by the project maintainer; independent verification was unavailable when this page was authored.
- [ ] Align `CITATION.cff` with the actual Zenodo record, or update the DOI if it refers to a different research artifact.
- [ ] Confirm rights for all source code and public-facing assets. No root LICENSE file was available on the main branch at site creation, so the page does not advertise an unverified license.
- [ ] Preserve prior SSRN attribution separately from the newer research draft.
- [ ] Do not add old unsupported AUC/F1, real-bank-fraud detection, real-time bank integration, or IEEE submission/acceptance claims.
- [ ] Keep the audited raw study links and negative comparisons visible to prospective research readers.

## Where to edit

- `README.md`: project landing page inside GitHub.
- `docs/index.html`: public GitHub Pages landing page.
- `docs/assets/fraudrag-banner.svg`: GitHub README hero artwork.
- `docs/assets/verification-flow.svg`: self-contained scientific workflow artwork.
- `CITATION.cff`: repository citation metadata.
- `research/publication/README.md`: source-traced science, kept separate from public-facing marketing copy.
