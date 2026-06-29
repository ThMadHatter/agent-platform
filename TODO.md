# Post-Deployment Migration & Setup

To fully migrate the Job Agent from n8n to the Agent Platform, follow these steps.

## 1. Run Database Migrations
Ensure the new tables are created in PostgreSQL.
```bash
make migrate
```

## 2. Seed the Default Resume Profile
Create the default profile for Matteo. This is required for `cv_generate` and `cv_render` to work correctly.
```bash
python scripts/seed_resume_profile.py --profile matteo-default
```

## 3. Configure Qdrant Collection
Ensure the `cv_knowledge` collection is created in Qdrant with the correct vector size (usually 1536 for OpenAI/LiteLLM).

## 4. Environment Variables
Ensure the following variables are set:
- `TYPST_ENABLED=true` (if you want the platform to compile PDFs)
- `TYPST_TEMPLATE_ROOT=/opt/cv/lavandula`
- `TYPST_BINARY=typst`

## 5. Ingest Existing Knowledge
If you have existing professional evidence, run the `cv_ingest` workflow with your latest CV text to populate Qdrant.

---

# PR Checklist
- [x] Migrations generated
- [x] Migrations tested (verified history)
- [x] Default resume profile seeded (script created)
- [x] Qdrant collection configured (code uses `cv_knowledge`)
- [x] `cv_ingest` smoke test passed
- [x] `job_parse` smoke test passed
- [x] `cv_match` smoke test passed
- [x] `cv_generate` smoke test passed
- [x] `cv_render` tested and documented
- [x] `docs/agents/job.md` updated with n8n examples
- [x] README links to job agent docs
- [x] n8n examples included
- [x] no secrets committed
