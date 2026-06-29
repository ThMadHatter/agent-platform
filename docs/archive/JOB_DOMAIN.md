# Job Domain - Agent Platform

## Overview
The Job Domain handles all AI-assisted tasks related to career management, including job scraping, resume optimization, and application tracking.

## Architecture
The Job Domain follows a service-oriented architecture within the `JobAgent`.

### JobAgent
The orchestrator responsible for managing different workflows:
- `linkedin_ingestion`: Scrapes and parses job postings.
- `resume_optimization`: Tailors a resume for a specific job description.
- `resume_ingestion`: Extracts experience from a resume to build a user profile.

### Internal Services
- **LinkedInJobIngestionService**: Simulates scraping of LinkedIn job pages.
- **JobDescriptionParser**: Uses LLMs to extract structured requirements from raw job text.
- **ResumeOptimizer**: Uses LLMs to align resume content with job requirements.
- **ApplicationTracker**: Manages the status of job applications.

## Workflows

### 1. Job Ingestion
Scrape URL → Parse Description → Store in Vector Database.

### 2. Resume Optimization
Fetch Resume → Fetch Job Description → LLM Optimization → Track Application.

### 3. Knowledge Extraction
Parse Resume → Extract Experience → Store in User Profile Vector Collection.

## Extension Points
- **New Ingestion Services**: Add `IndeedIngestionService` or `GitHubJobsIngestionService`.
- **Export Services**: Implement `PDFGeneratorService` (e.g., using Typst) for final resume export.
- **Auto-Apply**: Add a service to integrate with browser automation for job applications.
