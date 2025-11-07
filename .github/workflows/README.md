# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, linting, and deployment.

## Workflows

### 1. `ci.yml` - Full Test Suite (Primary)

**Trigger:** Push or PR to `main` or `develop` branches

**What it does:**
- Runs complete test suite for both backend and frontend
- Required for branch protection rules
- Reports overall pass/fail status

**Jobs:**
- `check-status` - Initiates CI pipeline
- `backend-tests` - Runs all backend tests with coverage
- `frontend-tests` - Runs all frontend tests with coverage + build
- `all-tests-complete` - Reports final status

**Use this for:** Branch protection requirements

---

### 2. `backend-ci.yml` - Backend Only

**Trigger:** Push or PR when backend files change

**What it does:**
- Python linting (flake8, black)
- Runs pytest suite
- Coverage reporting
- Security scanning (bandit, safety)

**Jobs:**
- `test` - Runs tests on Python 3.11
- `security` - Security vulnerability scanning

**Environment Variables:**
- `FLASK_ENV=testing`
- `SECRET_KEY=test-secret-key-for-ci`
- `DATABASE_URL=sqlite:///test.db`

---

### 3. `frontend-ci.yml` - Frontend Only

**Trigger:** Push or PR when frontend files change

**What it does:**
- ESLint linting
- Prettier formatting check
- Runs Jest test suite
- Production build validation
- Bundle size check

**Jobs:**
- `test` - Runs tests on Node 18.x and 20.x

**Environment Variables:**
- `CI=true` (for tests)
- `CI=false` (for build - suppresses warnings as errors)

---

## Setting Up Branch Protection

To require tests to pass before merging:

1. Go to **Settings** → **Branches**
2. Add rule for `main` branch
3. Enable **Require status checks to pass before merging**
4. Select these checks:
   - `all-tests-complete` (from `ci.yml`)
   - `backend-tests` (from `ci.yml`)
   - `frontend-tests` (from `ci.yml`)
5. Enable **Require branches to be up to date before merging**

## Testing Locally

Before pushing, run tests locally to catch issues early:

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Full Test Suite
```bash
# Terminal 1 - Backend
cd backend && pytest tests/

# Terminal 2 - Frontend
cd frontend && npm test
```

## Coverage Reports

Coverage reports are generated on every CI run:

- **Backend:** Available in workflow logs, shows line-by-line coverage
- **Frontend:** Available in workflow logs, includes branch/function coverage
- **Optional:** Codecov integration (uncomment in workflows)

## Adding Codecov (Optional)

To enable coverage tracking with Codecov:

1. Sign up at https://codecov.io
2. Add repository to Codecov
3. Add `CODECOV_TOKEN` to GitHub Secrets
4. Uncomment Codecov steps in workflows
5. Coverage reports will be posted on PRs

## Workflow Status Badges

Add to README.md:

```markdown
![Backend CI](https://github.com/YOUR_USERNAME/LCH/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/YOUR_USERNAME/LCH/workflows/Frontend%20CI/badge.svg)
![CI](https://github.com/YOUR_USERNAME/LCH/workflows/CI%20-%20Full%20Test%20Suite/badge.svg)
```

## Troubleshooting

### Tests pass locally but fail in CI

**Common causes:**
- Environment variable missing (add to workflow)
- Different Python/Node version (check matrix)
- Dependencies not installed (check workflow steps)
- Database setup issues (ensure test DB is created)

**Solution:** Check workflow logs for detailed error messages

### Slow CI runs

**Optimization tips:**
- Use caching for pip and npm (already configured)
- Run backend and frontend tests in parallel (already configured)
- Only run workflows when relevant files change (already configured with `paths`)

### Skipping CI

To skip CI on a commit (use sparingly):
```bash
git commit -m "docs: Update README [skip ci]"
```

## Future Enhancements

Planned additions (Phase 10.1 continued):

- [ ] Automated deployment workflow (CD)
- [ ] Docker image building and pushing
- [ ] Staging environment deployment
- [ ] Production deployment (manual approval)
- [ ] Performance benchmarking
- [ ] E2E testing with Playwright/Cypress
- [ ] Scheduled security scans (weekly)
- [ ] Dependency update automation (Dependabot)

---

**Status:** ✅ Active
**Last Updated:** 2025-11-07
**Maintained By:** Development Team
