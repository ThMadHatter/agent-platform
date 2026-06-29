# Medical Agent

## Purpose
Extracts and normalizes medical information from documents (URLs or Google Drive).

## Input Schema
```json
{
  "patient_id": "string",
  "document_url": "string (optional)",
  "gdrive_file_id": "string (optional)",
  "extraction_type": "string (optional, default: 'general')"
}
```

## Output Schema
```json
{
  "success": "boolean",
  "data": {
    "ocr_text": "string",
    "extracted_data": "object",
    "normalized_data": "object"
  }
}
```

## Example Request
`POST /api/v1/agents/medical/run`
```json
{
  "patient_id": "P123",
  "document_url": "https://example.com/medical_report.pdf"
}
```

## Example Response
```json
{
  "execution_id": "exec_123",
  "agent_id": "medical",
  "status": "succeeded",
  "result": {
    "ocr_text": "...",
    "extracted_data": {...},
    "normalized_data": {...}
  },
  "error": null
}
```

## Required Services
- PostgreSQL (Metadata)
- Vector Store (Qdrant)
- Document Store (Google Drive)
- LiteLLM
- OCR Provider
