# Financial Multimodal RAG --- SEC Filings Intelligence

A financial-domain Retrieval-Augmented Generation (RAG) application
designed to help users search and analyze financial documents, including
SEC filings such as annual reports (10-K) and quarterly reports (10-Q).
The application combines a FastAPI backend, Streamlit interface, Qdrant
vector search, and Groq-powered answer generation.

> **Important:** Answers depend on successful document extraction,
> indexing, and retrieval. This project supports document review and is
> not investment, legal, or accounting advice.

## Key Features

-   Financial document question answering over uploaded filings.
-   Intended workflows for SEC Forms 10-K and 10-Q.
-   Multimodal ingestion where supported by configured processors.
-   Qdrant vector search for relevant document chunks.
-   Groq LLM integration using `openai/gpt-oss-120b`.
-   FastAPI backend for chat, ingestion, and document management.
-   Streamlit interface for uploads, categories, chat, and source
    display where supported.
-   Configurable Top-K, reranking, and citations where supported by the
    backend.

## Financial Use Cases

After relevant filings are successfully ingested and indexed, users can
ask:

-   What was the company's total revenue for fiscal year 2025?
-   How did revenue and operating income change year over year?
-   What risk factors did management disclose?
-   What does the filing report about operating cash flow and capital
    expenditures?
-   What debt obligations or liquidity concerns are described?

Answers depend on the content extracted and retrieved. Verify important
figures against the original filing.
<img width="1908" height="922" alt="Screenshot 2026-10-26 160121" src="https://github.com/user-attachments/assets/cf2c4e12-797d-4c13-baa3-3ecfd527fc50" />
<img width="1891" height="917" alt="Screenshot 2026-10-26 160252" src="https://github.com/user-attachments/assets/bd5750f1-6cf6-46d3-9967-2e7565e2f171" />


## Architecture

``` text
Streamlit UI
    |
    v
FastAPI Backend
    |
    +--> Document ingestion --> Text extraction --> Chunking --> Embeddings
    |                                                       |
    |                                                       v
    |                                                   Qdrant
    |
    +--> User question --> Query embedding --> Qdrant retrieval
                                             |
                                             v
                                     Retrieved context
                                             |
                                             v
                                  Groq: openai/gpt-oss-120b
                                             |
                                             v
                                      Answer + sources
```

## Technology Stack

  Component                 Technology
  ------------------------- -------------------------------------
  Domain                    Financial documents and SEC filings
  LLM inference             Groq API
  Configured LLM            `openai/gpt-oss-120b`
  Backend                   FastAPI
  Frontend                  Streamlit
  Vector database           Qdrant
  Runtime                   Python
  Optional infrastructure   Docker

Use the embedding model configured by the project consistently for both
ingestion and retrieval.

## Prerequisites

-   Python version compatible with `requirements.txt` (Python 3.10+ is a
    suggested baseline).
-   Git.
-   A Groq API key with access to the configured model.
-   Docker Desktop if running Qdrant locally.
-   Tesseract OCR and FFmpeg if required by the installed document
    processors.

## Environment Configuration

Create a `.env` file in the repository root. Confirm additional required
settings in `app/core/config.py` and your local configuration.

``` env
APP_NAME="Financial Multimodal RAG"
DEBUG=True
LOG_LEVEL=INFO

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
LLM_BASE_URL=https://api.groq.com/openai/v1

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=rag_collection
```

-   Replace `your_groq_api_key` with your own key.
-   Never commit the real `.env` file.
-   The collection name must match the collection used by both ingestion
    and retrieval.
-   Ensure the frontend and backend do not override the configured model
    with `gpt-3.5-turbo`.
-   The embedding model is separate from the LLM and must be compatible
    between indexing and querying.

## Installation

### 1. Clone the repository

``` bash
git clone https://github.com/shobanjatoth/Multimodal_Rag.git
cd Multimodal_Rag
```

### 2. Create and activate a virtual environment

Windows PowerShell:

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure `.env`

Add your Groq API key and verify the model and Qdrant settings.

### 5. Start Qdrant

``` powershell
docker run -d --name rag-qdrant -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest
```

If a Qdrant container is already running, start that container instead
of creating a duplicate.

Dashboard: http://localhost:6333/dashboard

## Run Locally

Run the backend and frontend in separate terminals from the repository
root.

### FastAPI backend

``` bash
uvicorn app.main:app --reload --port 8000
```

API documentation: http://localhost:8000/docs

Health endpoint, if registered: http://localhost:8000/health

### Streamlit frontend

If your frontend is `ui/app.py`:

``` bash
streamlit run ui/app.py --server.port 8501
```

If you are using `enterprise_rag_ui_interactive.py` in the repository
root:

``` bash
streamlit run enterprise_rag_ui_interactive.py --server.port 8501
```

Use the command matching the frontend file in your checkout.

Open: http://localhost:8501

## How to Use

1.  Start Qdrant, FastAPI, and Streamlit.
2.  Open the Streamlit UI.
3.  Select or create a category such as `Financial` or `SEC Filings`.
4.  Upload a supported financial filing.
5.  Confirm ingestion succeeded and the document is available in the
    knowledge base.
6.  Ask a question about the uploaded filing.
7.  Review the answer and source details when returned by the backend.

## API Documentation

Use the live Swagger UI at http://localhost:8000/docs for the exact
routes and request schemas registered by your application. Depending on
router configuration, routes may cover chat, streaming chat,
conversation history, ingestion, document listing, and deletion.

## Representative Project Structure

Actual paths may differ in your checkout.

``` text
Multimodal_Rag/
├── app/
│   ├── main.py
│   ├── api/v1/endpoints/
│   ├── core/config.py
│   ├── ingestion/
│   ├── llm/
│   │   ├── gateway.py
│   │   ├── conversation_service.py
│   │   ├── memory/
│   │   └── providers/
│   └── retrieval/
├── ui/
│   └── app.py
├── api_client.py
├── config.py
├── requirements.txt
├── .env                 # Local only; do not commit
├── .gitignore
└── README.md
```

## Troubleshooting

### Groq returns `model_not_found`

Check:

``` env
GROQ_MODEL=openai/gpt-oss-120b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

Search for outdated defaults in PowerShell:

``` powershell
Get-ChildItem -Recurse -File -Include *.py,*.env |
  Select-String -Pattern "gpt-3.5-turbo"
```

Update active code paths that override the model, then restart FastAPI.
A commented-out default may not affect runtime behavior, so check which
setting the gateway actually uses.

### Document listing returns HTTP 500

Inspect the FastAPI traceback and endpoint response body. An empty
Qdrant collection alone should not normally cause document listing to
fail; fix the actual backend exception.

### Qdrant contains zero points after upload

Check the ingestion pipeline in order:

1.  Was the file accepted?
2.  Was its content extracted?
3.  Were chunks created?
4.  Did embedding generation succeed?
5.  Were points inserted into the expected Qdrant collection?

Ensure ingestion and retrieval use the same collection and compatible
embedding settings.

### No relevant financial information is retrieved

Verify the filing contains the requested year and metric, that relevant
chunks were indexed, and that filters, Top-K, score thresholds, and
reranking are not excluding them.

## Security Notes

-   Keep API keys in environment variables; never commit `.env`.
-   Add `.env`, virtual environments, local databases, and secrets to
    `.gitignore`.
-   Follow your organization's data-handling policies for confidential
    financial information.
-   Verify important financial figures against the original filing.

## Contributing

1.  Fork the repository.
2.  Create a feature branch, for example `feature/financial-retrieval`.
3.  Make focused changes and test the affected workflows.
4.  Open a pull request with a clear description and relevant test
    results.

## License

No license has been specified here. Add a `LICENSE` file if you intend
to grant reuse, modification, or redistribution permissions.

## Contact

Repository: https://github.com/shobanjatoth/Multimodal_Rag

