# 🚀 Smart Files: AI-Powered Document Intelligence System (MLOps Enabled)

## 📌 Overview

Smart Files is an AI-powered document management system that enables users to upload, search, and query documents using semantic search, Retrieval-Augmented Generation (RAG), and automated SQL generation.

The system is designed with **MLOps principles**, ensuring scalability, reproducibility, monitoring, and automation.

---

## 🎯 Problem Statement

Organizations deal with scattered unstructured and structured data (PDFs, CSVs, reports), making it difficult to search and extract insights efficiently.

This project solves this by:

* enabling semantic search across documents
* providing AI-powered Q&A (RAG)
* generating SQL queries for structured datasets

---

## 🧠 Key Features

* 📂 Multi-source file ingestion (local + AWS S3)
* 🔍 Semantic Search (Vector DB)
* 🤖 RAG-based Question Answering
* 🧾 SQL Query Generation from natural language
* ☁️ Cloud Storage using AWS S3
* 📊 MLflow for experiment tracking
* 📦 DVC for data versioning
* 🧪 Evaluation pipeline for model performance
* 📡 Logging and monitoring system
* 🔁 CI/CD integration (GitHub Actions)

---

## 🏗️ System Architecture

```
User (Streamlit UI)
        ↓
FastAPI Backend (Agent)
        ↓
-----------------------------------
|  Semantic Search | RAG | SQL Tool |
-----------------------------------
        ↓
Vector DB (Chroma)
        ↓
AWS S3 (Document Storage)
        ↓
MongoDB (Metadata)
        ↓
MLflow + Logging (Monitoring)
```

---

## ⚙️ Tech Stack

| Component           | Technology     |
| ------------------- | -------------- |
| Backend             | FastAPI        |
| Frontend            | Streamlit      |
| Storage             | AWS S3         |
| Database            | MongoDB        |
| Vector DB           | ChromaDB       |
| LLM                 | Ollama (Gemma) |
| Experiment Tracking | MLflow         |
| Data Versioning     | DVC            |
| CI/CD               | GitHub Actions |

---

## 🔄 MLOps Pipeline

1. File Upload → stored in S3
2. Metadata stored in MongoDB
3. Document processed (chunking + embedding)
4. Stored in Vector DB
5. Query → Agent decides:

   * Semantic Search
   * RAG
   * SQL generation
6. Results returned to user
7. MLflow logs metrics and performance

---

## 📊 Monitoring & Logging

* Tracks:
  * user queries
  * agent decisions
  * latency
  * errors
* Unified log directory (`logs/`):
  * `app_runtime.log`: System and application runtime logs (Rotating).
  * `api_performance.csv`: API latency and performance metrics.
* Experiment Tracking:
  * `models/mlflow.db`: SQLite backend for MLflow tracking.

---

## 📦 Data Versioning (DVC)

* Tracks:

  * document dataset (`data/documents/`)
* Ensures:

  * reproducibility
  * version comparison

---

## 🧪 Experiment Tracking (MLflow)

Tracks:

* retrieval accuracy
* response quality
* latency
* agent tool usage

---

## 🚀 Setup Instructions

### 1. Clone Repository

```bash
git clone <repo-url>
cd smart_files
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Setup Environment Variables

Create `.env` file:

```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=your_region
AWS_BUCKET_NAME=your_bucket

MONGO_URI=your_mongo_uri
```

---

### 4. Run Backend (FastAPI)

```bash
uvicorn app.main:app --reload
```

---

### 5. Run Frontend (Streamlit)

```bash
streamlit run app.py
```

---

## 🔁 CI/CD Pipeline

GitHub Actions is used for automated validation:
* **Linting**: flake8 checks for code quality.
* **Core Module Tests**: Validates imports and basic functionality.
* **MLflow Tracking Test**: Verifies experiment logging integration.
* **Evaluation Pipeline**: Runs automated evaluation scripts.
* **Artifact Management**: Stores logs and performance metrics from each run.

---

## 🎯 Deployment Strategy

* Real-time API using FastAPI
* Frontend via Streamlit
* Cloud storage via AWS S3

---

## 🎤 Key MLOps Concepts Covered

* Data Versioning (DVC)
* Experiment Tracking (MLflow)
* Monitoring & Logging
* Modular Pipeline Design
* CI/CD Automation
* Cloud Integration

---

## 🚀 Future Improvements

* Real-time pipeline automation
* Model fine-tuning
* Advanced evaluation metrics
* Full cloud deployment (VM/Kubernetes)

---


