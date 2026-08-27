# FRIDAY Release & Publishing Plan

Publishing is deliberately separated from development changes. This document defines the release gate for a future production/public release.

## Release gates

### Security

- [ ] No credentials are present in `.env.example` or other tracked files.
- [ ] Required API credentials are stored only in local secret stores or GitHub Secrets.
- [ ] Any previously exposed credential has been rotated/revoked.
- [ ] MCP access has an appropriate authentication and authorization boundary.
- [ ] Production logs have been checked for secret leakage.

### Code quality

- [ ] `python -m unittest discover -v` passes.
- [ ] `python -m compileall friday_agent tests` passes.
- [ ] `git diff --check` passes.
- [ ] Docker build succeeds.
- [ ] GitHub Actions is green on the release commit.

### Runtime

- [ ] LiveKit worker starts cleanly.
- [ ] Test room connection succeeds.
- [ ] Groq STT works.
- [ ] Groq LLM works.
- [ ] ElevenLabs TTS works and audio quality is acceptable.
- [ ] VAD and turn detection are stable.
- [ ] MCP tools operate within their configured security limits.

### Container

- [ ] Image is tagged with a version.
- [ ] Image is pushed to the selected registry.
- [ ] Deployment references an immutable version/digest.
- [ ] Runtime secrets are injected by the deployment platform.
- [ ] Health/log monitoring is enabled.

## Suggested versioning

Use semantic-style versions such as:

```text
v0.1.0  first public technical release
v0.2.0  feature release
v0.2.1  bug/security fix
v1.0.0  first production-stable release
```

## Publishing sequence

```text
Feature complete
      ↓
Security review
      ↓
Tests + Docker build
      ↓
GitHub Actions green
      ↓
Build/version container
      ↓
Push container registry
      ↓
Deploy worker
      ↓
Production smoke test
      ↓
Create GitHub Release
      ↓
Publish announcement/documentation
```

## Rollback

Keep the previous known-good container version available. If a release fails production validation, redeploy the previous immutable image and investigate before publishing the release as stable.

## Important

A successful GitHub commit is not the same as a production deployment. Publishing should happen only after the runtime smoke test and security gates pass.
