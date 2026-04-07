DocuScan

Full-stack application with a React + Vite frontend and a Node.js + Express backend (TypeScript).

# Project structure

.  
├── backend/ # Node.js + Express API (TypeScript)  
├── frontend/ # React + Vite app (TypeScript)  
├── .git/ # Git repository  
├── .gitignore  
└── Readme.md

# Requirements

- Git
- Node.js >= 18 (LTS recommended, e.g. Node 20)
- npm (comes with Node) or your preferred package manager (npm / pnpm / yarn).
  This README uses npm in the examples.

# Clone the repository

```bash
git clone https://github.pascsource.ent.cgi.com/InnoPush-WMK-GER-GFS/DocuScan.git
cd DocuScan
```

# Backend setup

Go to the backend folder and install dependencies:

```bash
cd backend
npm install
```

# Environment variables

The backend uses Azure and the official openai library.  
Fill out the following variables with the corresponding values (e.g. in a .env file):

AZURE_ENDPOINT=https://resource.cognitiveservices.azure.com  
AZURE_KEY=<your-azure-key>  
AZURE_API_VERSION=2024-11-30  
DI_MODEL_ID=prebuilt-layout  
OPENAI_API_KEY=<your-api-key-openai>  
PORT=4000

# Frontend setup:

Go to the frontend folder and install dependencies:

```bash
cd frontend
npm install
```

# Running frontend and backend together (development)

1. Open two terminals.
2. In the first one, start the backend:

```bash
   cd backend
   npm run dev
```

3. In the second one, start the frontend:

```bash
   cd frontend
   npm run dev
```

4. Open your browser at the URL shown by Vite (by default http://localhost:5173).

# Contributing

1. Fork the repository.
2. Create a feature branch: git checkout -b feat/my-new-feature
3. Make your changes and commit.
4. Open a Pull Request.
