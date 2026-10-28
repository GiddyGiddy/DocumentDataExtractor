# DocuScan — AI-Powered Document Data Extractor

DocuScan is a full-stack application that extracts structured data from legal PDF documents. It combines a locally-hosted **Azure Document Intelligence** container for OCR with a **local LLM (Phi-3.5-mini via AI Foundry Local)** for intelligent entity extraction, and presents results through a modern **React** frontend.

All document processing happens on-premises — no raw document content is sent to external cloud services at runtime.

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Component Setup](#component-setup)
   - [Azure Document Intelligence Container](#1-azure-document-intelligence-container)
   - [NER Container (Optional)](#2-ner-container-optional)
   - [Local LLM — AI Foundry Local](#3-local-llm--ai-foundry-local)
   - [Backend — Flask API](#4-backend--flask-api)
   - [Frontend — React + Vite](#5-frontend--react--vite)
5. [Environment Variables](#environment-variables)
6. [Running the Full Stack](#running-the-full-stack)
7. [API Reference](#api-reference)
8. [Project Structure](#project-structure)

---

## Features

- **PDF Upload** — drag-and-drop or file-picker upload of German legal/notarial PDFs.
- **OCR via Azure Document Intelligence** — runs in a local Docker container using the `prebuilt-layout` model to extract text, key-value pairs, and tables in Markdown format.
- **Intelligent Entity Extraction** — a Phi-3.5-mini LLM agent (served locally by AI Foundry Local) extracts structured entities including:
  - Names and addresses of contracting parties
  - Notary name and address
  - Purchase date (*Kaufdatum*)
  - Notarial deed number (*UVZ-Nr*)
  - Property area (*Fläche* in m²)
  - Postal receipt date (*Posteingangsdatum*)
- **Structured JSON Output** — extracted data is returned as a clean JSON object, displayed in the UI with a one-click copy button.
- **Real-time Status** — Socket.IO WebSocket connection provides live processing status updates.
- **Azure Key Vault Integration** — secrets (API keys, endpoints) are retrieved securely at runtime using `DefaultAzureCredential`.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                          │
│   React + Vite Frontend  (port 5173)                            │
│   • PDF drag-and-drop upload                                    │
│   • Real-time status via Socket.IO                              │
│   • JSON result display                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP POST /api/process-pdf
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Flask Backend  (port 8080)                         │
│   ApiServer.py                                                  │
│   • Receives PDF via multipart/form-data                        │
│   • Calls Azure Document Intelligence container for OCR         │
│   • Passes OCR text to AI Foundry Local agent                   │
│   • Returns extracted JSON                                      │
└──────┬──────────────────────────────────────┬───────────────────┘
       │                                      │
       ▼                                      ▼
┌─────────────────────┐         ┌─────────────────────────────────┐
│ Azure Document       │         │  AI Foundry Local               │
│ Intelligence         │         │  Phi-3.5-mini LLM               │
│ Container            │         │  (started automatically by SDK) │
│ (Docker, port 5010)  │         │  • Named entity extraction      │
│ prebuilt-layout model│         │  • Returns structured JSON      │
└─────────────────────┘         └─────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ (LTS recommended) |
| Docker Desktop | Required for Azure Cognitive Services containers |
| Azure Subscription | Required to obtain billing endpoint & API key for the Document Intelligence container |
| AI Foundry Local | Installed on the host machine — [download here](https://aka.ms/foundry-local) |
| Azure CLI | Required for `DefaultAzureCredential` / Key Vault access |

---

## Component Setup

### 1. Azure Document Intelligence Container

The backend talks to a **locally running** Azure Document Intelligence container. This container requires a valid Azure billing endpoint and API key.

#### Pull and run with Docker Compose

The `DocuScan/docker-compose.yml` file defines both the Document Intelligence and the NER containers.

Before starting, create a `.env` file (or set the variables directly) with your Azure credentials — **do not hard-code keys in `docker-compose.yml`**:

```yaml
# docker-compose.yml (excerpt — use environment variables for secrets)
services:
  forms:
    image: "mcr.microsoft.com/azure-cognitive-services/form-recognizer/layout-4.0"
    environment:
      eula: accept
      billing: ${DOC_INTELLIGENCE_ENDPOINT}
      apikey: ${DOC_INTELLIGENCE_KEY}
      FormRecognizer__ComputerVisionApiKey: ${DOC_INTELLIGENCE_KEY}
      FormRecognizer__ComputerVisionEndpointUri: ${DOC_INTELLIGENCE_ENDPOINT}
    volumes:
      - type: bind
        source: C:\Azure_AI\output
        target: /output
      - type: bind
        source: C:\Azure_AI\input
        target: /input
    ports:
      - "5010:5000"
```

Start the container:

```bash
cd DocuScan
docker-compose up -d forms
```

The container will be available at `http://localhost:5010`. The backend connects to this endpoint automatically.

> **Important:** The output and input bind-mount directories (`C:\Azure_AI\output` and `C:\Azure_AI\input`) must exist on the host before starting the container.

```bash
mkdir C:\Azure_AI\output
mkdir C:\Azure_AI\input
```

---

### 2. NER Container (Optional)

A Named Entity Recognition container is also defined in `docker-compose.yml` for additional text analysis:

```bash
docker-compose up -d ner
```

This container runs on port `5021`.

---

### 3. Local LLM — AI Foundry Local

DocuScan uses **AI Foundry Local** to serve the `phi-3.5-mini` model on the host machine. The Python SDK (`foundry_local` and `agent_framework_foundry_local`) starts the service and downloads the model automatically on first run.

#### Install AI Foundry Local

Download and install the Foundry Local runtime from:  
[https://aka.ms/foundry-local](https://aka.ms/foundry-local)

The backend will automatically:
1. Start the Foundry Local service (if not already running).
2. Download `phi-3.5-mini` to the local device on first use.
3. Create a `Data Extraction Agent` with German-language extraction instructions.
4. Stream the response and parse the returned JSON.

No additional configuration is required for the LLM component beyond having Foundry Local installed.

---

### 4. Backend — Flask API

#### Install dependencies

```bash
# From the workspace root
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

#### Key Python packages

| Package | Purpose |
|---|---|
| `flask` + `flask-cors` | HTTP API server |
| `flask-socketio` | WebSocket support for real-time status |
| `azure-ai-documentintelligence` | Azure Document Intelligence SDK |
| `azure-ai-textanalytics` | Azure Text Analytics SDK |
| `semantic-kernel` | Agent orchestration framework |
| `foundry_local` | AI Foundry Local model manager |
| `agent_framework_foundry_local` | Foundry Local agent client |
| `azure-keyvault-secrets` | Azure Key Vault secret retrieval |
| `azure-identity` | `DefaultAzureCredential` for Key Vault |

#### Configure environment variables

```bash
# Windows PowerShell
$env:KEY_VAULT_NAME = "your-keyvault-name"
$env:FLASK_APP = "DocuScan\backend\ApiServer.py"
```

Or create a `.env` file in the project root (and use `python-dotenv` to load it):

```
KEY_VAULT_NAME=your-keyvault-name
```

The backend retrieves the Document Intelligence API key from Key Vault under the secret name `DocIntellKey`. Ensure this secret exists in your vault before running.

#### Run the backend

```bash
cd DocuScan/backend
python ApiServer.py
```

The server starts on **port 8080** and also listens for Socket.IO connections.

Alternatively, run with Flask CLI:

```bash
flask run --host 0.0.0.0 --port 8080
```

#### Docker (backend only)

```bash
# From workspace root
docker build -t docuscan:latest .
docker run -p 8080:8080 -e KEY_VAULT_NAME=your-keyvault-name docuscan:latest
```

---

### 5. Frontend — React + Vite

#### Install dependencies

```bash
cd DocuScan/frontend
npm install
```

#### Configure the backend URL

Create a `.env` file in `DocuScan/frontend/`:

```
VITE_BACKEND_URL=http://localhost:8080/api/process-pdf
```

#### Run the development server

```bash
npm run dev
```

The frontend is served at **http://localhost:5173**.

#### Build for production

```bash
npm run build
```

Static output is written to `DocuScan/frontend/dist/`.

---

## Environment Variables

| Variable | Component | Description |
|---|---|---|
| `KEY_VAULT_NAME` | Backend | Name of the Azure Key Vault containing secrets |
| `VITE_BACKEND_URL` | Frontend | Full URL of the backend `process-pdf` endpoint |
| `DOC_INTELLIGENCE_ENDPOINT` | Docker Compose | Azure Document Intelligence billing endpoint |
| `DOC_INTELLIGENCE_KEY` | Docker Compose | Azure Document Intelligence API key |

> **Security note:** Never commit API keys or secrets to source control. Use environment variables, `.env` files (added to `.gitignore`), or Azure Key Vault.

---

## Running the Full Stack

Start all components in this order:

```bash
# 1. Start the Azure Document Intelligence container
cd DocuScan
docker-compose up -d forms

# 2. Start the Flask backend (in a separate terminal)
cd ..
.venv\Scripts\activate
python DocuScan/backend/ApiServer.py

# 3. Start the React frontend (in a separate terminal)
cd DocuScan/frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## API Reference

### `POST /api/process-pdf`

Accepts a PDF file, runs OCR via the local Document Intelligence container, and extracts structured entities using the local LLM agent.

**Request**

| Field | Type | Description |
|---|---|---|
| `file` | `multipart/form-data` | The PDF document to process |

**Response** — `200 OK`

```json
{
  "Name der Vertragsparteien-beteiligte": "Max Mustermann und Erika Musterfrau",
  "Name der Notar": "Dr. Manuel Ladiges",
  "Adresse der Vertragsparteien-beteiligte": "Musterstraße 1, 12345 Musterstadt",
  "Adresse der Notar": "Notarstraße 2, 54321 Notarstadt",
  "Kaufdatum": "01.12.2025",
  "UVZ-Nr": "1465/2025",
  "Fläche": "150",
  "Posteingangsdatum": "16.12.2025"
}
```

### WebSocket — Socket.IO

| Event | Direction | Description |
|---|---|---|
| `data` | server → client | Broadcasts processing status messages |
| `connect` | server → client | Emitted when a client connects |

---

## Project Structure

```
Docuscan/
├── Dockerfile                        # Backend container image
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── DocuScan/
    ├── docker-compose.yml            # Azure Cognitive Services containers
    ├── backend/
    │   ├── ApiServer.py              # Flask app — main entry point
    │   ├── AzServiceApiLogic.py      # Standalone OCR helper class
    │   ├── foundryLocal.py           # Foundry Local LLM test script
    │   ├── contracts/
    │   │   └── vollmacht.json        # Sample contract JSON schema
    │   └── prompts/
    │       └── system_contract_extractor.md  # LLM system prompt
    └── frontend/
        ├── package.json
        ├── vite.config.ts
        └── src/
            ├── App.tsx
            ├── components/
            │   ├── ContentArea/      # Main layout wrapper
            │   │   └── components/
            │   │       ├── UploadArea/   # PDF drag-and-drop upload
            │   │       ├── ResultArea/   # JSON result display
            │   │       └── WorkPanel/    # Orchestrates upload + result
            │   ├── Header/           # App header
            │   ├── ErrorAlert/       # Error message component
            │   └── StatusAlert/      # Processing status component
            └── utils/
                ├── getFileSizeInMB.ts
                └── isPdf.ts
```
