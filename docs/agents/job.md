# Job Agent

## Purpose
Orchestrates career-related workflows including job parsing, CV knowledge ingestion, matching, generation, and rendering.

## PostgreSQL stores:
- **resume_profiles**: Candidate contact info, languages, and summary.
- **jobs**: Raw and parsed job descriptions and metadata.
- **job_matches**: Evidence classification, scores, and retrieved evidence.
- **cv_generation_runs**: Generated Typst data and strategy metadata.
- **artifacts**: References to generated PDF files.
- **cv_knowledge_items**: Canonical text version of career knowledge.

## Qdrant stores:
- **CV/career knowledge only**: Experience chunks, projects, skills, achievements, education, and certifications.
- **Collection Name**: Default is `cv_knowledge` (configurable).

**Important**: Qdrant must not store raw job descriptions or generated CVs.

---

## Workflows

### 1. `job_parse`
**Purpose**: Resolves and parses a job description into a structured format.
**SQL Tables**: `jobs`
**Qdrant**: None

#### Input
- `job_url`: (Optional) URL of the job posting.
- `job_content`: (Optional) Raw text of the job description.
- `allow_fetch`: (Optional, bool) Enable scraping if `job_url` is provided. Default `false`.

#### Example Request
```json
{
  "input_data": {
    "workflow": "job_parse",
    "job_url": "https://example.com/job",
    "job_content": "Senior embedded software engineer role requiring Linux, C++, Python and IP networking.",
    "source": "manual-test"
  },
  "client_request_id": "test-job-parse-001"
}
```

#### Successful Response
```json
{
  "execution_id": "...",
  "status": "succeeded",
  "result": {
    "job_id": "job_123",
    "parsed_job": {
      "title": "Senior Embedded Software Engineer",
      "company": "Example Tech",
      "tech_stack": ["Linux", "C++", "Python"],
      "responsibilities": ["..."],
      "..."
    }
  }
}
```

---

### 2. `cv_ingest`
**Purpose**: Extracts structured career knowledge from a CV and stores it in Qdrant and SQL.
**SQL Tables**: `cv_knowledge_items`
**Qdrant**: `cv_knowledge` collection

#### Input
- `resume_content`: (Optional) Raw text of the CV.
- `resume_id`: (Optional) ID of a document in the document store.
- `resume_profile_id`: (Default: `matteo-default`) Target profile.

#### Example Request
```json
{
  "input_data": {
    "workflow": "cv_ingest",
    "resume_content": "I worked at Google as a Software Engineer from 2020 to 2023...",
    "resume_profile_id": "matteo-default"
  },
  "client_request_id": "test-cv-ingest-001"
}
```

---

### 3. `cv_match`
**Purpose**: Retrieves evidence from Qdrant and evaluates it against job requirements.
**SQL Tables**: `job_matches`
**Qdrant**: Retrieval only

#### Input
- `job_id`: (Optional) ID of a previously parsed job.
- `parsed_job`: (Optional) Structured job data.
- `resume_profile_id`: (Default: `matteo-default`)

#### Example Request
```json
{
  "input_data": {
    "workflow": "cv_match",
    "job_id": "job_123",
    "resume_profile_id": "matteo-default"
  },
  "client_request_id": "test-cv-match-001"
}
```

---

### 4. `cv_generate`
**Purpose**: Generates a targeted CV strategy and Typst-compatible JSON data.
**SQL Tables**: `cv_generation_runs`, `job_matches` (if triggered internally)

#### Input
- `job_id`: ID of the job.
- `resume_profile_id`: (Default: `matteo-default`)
- `template_id`: (Default: `lavandula`)
- `language`: (Default: `en`)
- `target_pages`: (Default: `2`)

#### Example Request
```json
{
  "input_data": {
    "workflow": "cv_generate",
    "job_id": "job_123",
    "resume_profile_id": "matteo-default",
    "template_id": "lavandula",
    "language": "en",
    "target_pages": 2
  },
  "client_request_id": "test-cv-generate-001"
}
```

#### Successful Response
```json
{
  "execution_id": "...",
  "status": "succeeded",
  "result": {
    "job_id": "job_123",
    "cv_version_id": "cv_456",
    "match": {
      "score": 82,
      "strengths": ["..."],
      "gaps": ["..."],
      "justification": "...",
      "evidence_map": {}
    },
    "cv_strategy": {
      "positioning": "...",
      "selected_experiences": [],
      "selected_skills": [],
      "selected_achievements": [],
      "gaps_not_covered": []
    },
    "typst_data": {
      "layout": { "sidebar_position": "left" },
      "personal": { "name": "Matteo Zappia", "title": "...", "contacts": [] },
      "about_me": "...",
      "skills": [],
      "languages": [],
      "experience": [],
      "achievements": [],
      "education": []
    }
  }
}
```

---

### 5. `cv_render` (Optional)
**Purpose**: Compiles the Typst JSON data into a PDF artifact.
**SQL Tables**: `artifacts`

#### Input
- `resume_id`: (Required) The `cv_version_id` from a generation run.
- `resume_profile_id`: (Default: `matteo-default`)

#### Example Request
```json
{
  "input_data": {
    "workflow": "cv_render",
    "resume_id": "cv_456",
    "resume_profile_id": "matteo-default"
  },
  "client_request_id": "test-cv-render-001"
}
```

---

## Recommended n8n Flows

The old n8n LLM/Qdrant/CV writer flow is now replaced by the platform-side `cv_match` and `cv_generate` workflows.

### `JOB - Parse Job`
1. Acquire job content in n8n (webhook/Telegram/Scraping).
2. Call **CORE - Agent Platform - Run And Wait** with `workflow = job_parse`.
3. Store/display `job_id`.

### `CV - Ingest Knowledge`
1. Receive CV/work content.
2. Call **CORE - Agent Platform - Run And Wait** with `workflow = cv_ingest`.
3. Verify Qdrant ingestion count in response.

### `JOB - Match Candidate`
1. Trigger with `job_id`.
2. Call **CORE - Agent Platform - Run And Wait** with `workflow = cv_match`.
3. Display score, strengths, gaps, and evidence map to user.

### `JOB - Generate Optimized CV`
1. Trigger with `job_id`.
2. Call **CORE - Agent Platform - Run And Wait** with `workflow = cv_generate`.
3. Receive `typst_data`.
4. (Optional) Human approval of the generated data.
5. Either call `cv_render` OR let n8n write `data.json` and run `typst compile` locally.

### `JOB - Render Typst CV`
1. Trigger with `cv_version_id`.
2. Call **CORE - Agent Platform - Run And Wait** with `workflow = cv_render`.
3. Receive PDF artifact metadata and path.

---

## Calling through CORE n8n Workflow
When using the reusable n8n core workflow, use this payload:

```json
{
  "agent_id": "job",
  "client_request_id": "cv-generate-job-123-v1",
  "payload": {
    "workflow": "cv_generate",
    "job_id": "job_123",
    "resume_profile_id": "matteo-default",
    "template_id": "lavandula",
    "language": "en",
    "target_pages": 2,
    "render_pdf": false
  }
}
```

---

## Idempotency Guidance
Use descriptive `client_request_id` keys to ensure idempotency. If the payload changes meaningfully, increment the version suffix.

Examples:
- `job-parse-<normalized-job-url>-v1`
- `cv-ingest-<source-file-id>-v1`
- `cv-match-<job-id>-<resume-profile-id>-v1`
- `cv-generate-<job-id>-<resume-profile-id>-lavandula-v1`
- `cv-render-<cv-version-id>-v1`

---

## Validation & Error Responses

### `job_parse` without content
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "No job content provided. Need job_content, job_data.description, distilled_jd, or job_url with allow_fetch=true.",
    "details": {}
  }
}
```

### `cv_generate` before CV knowledge exists
```json
{
  "error": {
    "code": "CV_KNOWLEDGE_NOT_FOUND",
    "message": "Not enough CV knowledge found for resume_profile_id=matteo-default. Run cv_ingest first.",
    "details": {
      "resume_profile_id": "matteo-default"
    }
  }
}
```

---

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string.
- `QDRANT_URL`: Qdrant endpoint.
- `TYPST_ENABLED`: (Default `false`) Enable the renderer service.
- `TYPST_BINARY`: (Default `typst`) Path to typst binary.
- `TYPST_TEMPLATE_ROOT`: Root directory for templates.
