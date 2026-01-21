# GreenGuard ESG Platform

<div align="center">
  <img src="999d46a1-7abf-4330-a3e7-548ea7a16ad0-removebg-preview.png" alt="GreenGuard Logo" width="200"/>
  
  **Intelligent ESG Compliance & Reporting Platform**
  
  [![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/greenguard)
  [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
  [![Tauri](https://img.shields.io/badge/Tauri-2.0-orange.svg)](https://tauri.app/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

**GreenGuard** is an advanced ESG (Environmental, Social, and Governance) compliance and reporting platform that leverages AI to automate the extraction, analysis, and benchmarking of sustainability data from corporate reports. Built for financial institutions, corporate sustainability teams, and ESG analysts, GreenGuard streamlines compliance with EU regulations (CSRD, EU Taxonomy) and global standards (SBTi, GRI).

### Key Capabilities

- 🤖 **AI-Powered Document Processing**: Automated extraction of ESG metrics from PDF reports
- 📊 **KPI Benchmarking**: Compare performance against industry peers and SBTi targets
- ✅ **Compliance Checking**: Automated validation against CSRD, EU Taxonomy, and sustainability-linked loan principles
- 💬 **Interactive Report Chat**: Query ESG reports using natural language with RAG technology
- 📈 **Visual Analytics**: Comprehensive dashboards and charts for ESG performance tracking
- 🔄 **Use of Proceeds Tracking**: Monitor green bond and sustainability-linked loan allocations

---

## ✨ Features

### 🔍 Intelligent Document Analysis
- **Multi-tier AI Agent System**: Hierarchical agent architecture for comprehensive ESG analysis
  - **Tier 1**: Document processing, chart understanding, baseline verification
  - **Tier 2**: KPI extraction, CapEx analysis, governance data extraction
  - **Tier 3**: Regulatory compliance analysis, industry benchmarking
  - **Tier 4**: Advanced analytics and trend analysis
  - **Tier 5**: Orchestration and decision-making
- **OCR Support**: Extract text from scanned documents and images
- **Table & Chart Recognition**: Intelligent extraction from visual data representations

### 📊 KPI Management & Benchmarking
- **Automated KPI Extraction**: Parse sustainability metrics from various report formats
- **Industry Benchmarking**: Compare against sector peers using Eurostat data
- **SBTi Target Validation**: Verify alignment with Science-Based Targets initiative
- **Custom KPI Tracking**: Define and monitor organization-specific metrics

### 🏛️ Regulatory Compliance
- **CSRD Compliance Analysis**: Automated checking against Corporate Sustainability Reporting Directive
- **EU Taxonomy Alignment**: Evaluate activities against sustainable finance taxonomy
- **Sustainability-Linked Loans**: Verify KPI targets and covenant compliance
- **Multi-Framework Support**: GRI, TCFD, SASB compatibility

### 💡 Advanced AI Features
- **RAG-Powered Chat**: Ask questions about your ESG reports and get contextual answers
- **Multi-Provider AI**: Support for Bytez, Perplexity, OpenRouter, and local Ollama models
- **Vector Embeddings**: Efficient semantic search using Voyage AI and Supabase
- **Memory-Augmented Processing**: Enhanced context retention across analysis sessions

### 📈 Analytics & Reporting
- **Interactive Dashboards**: Real-time visualization of ESG performance
- **Banker Report Generation**: Automated credibility assessments for financial institutions
- **Trend Analysis**: Historical tracking and forecasting
- **Export Capabilities**: Generate professional reports in multiple formats

---

## 🏗️ Architecture

GreenGuard employs a modern, scalable architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Desktop Client                      │
│              (React + TypeScript + Tailwind)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ REST API
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Multi-Tier AI Agent System                │   │
│  │  Tier 5: Orchestrator                                │   │
│  │  Tier 4: Analysis Agents                             │   │
│  │  Tier 3: Regulatory & Benchmark Agents               │   │
│  │  Tier 2: Extractor Agents (KPI, CapEx, Governance)  │   │
│  │  Tier 1: Document Processing & Verification          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  Services: ESG Mapping | Scoring | Compliance | Embeddings  │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼────┐ ┌─────▼──────────┐
│  PostgreSQL/ │ │   AI   │ │ External APIs  │
│   Supabase   │ │ Models │ │ (Eurostat,     │
│              │ │ (Bytez,│ │  Yahoo ESG,    │
│   Vector DB  │ │ etc.)  │ │  SBTi Data)    │
└──────────────┘ └────────┘ └────────────────┘
```

### Agent Hierarchy

The platform uses a sophisticated multi-tier agent system:

- **Tier 1 Agents**: Document ingestion, OCR, chart interpretation, baseline verification
- **Tier 2 Agents**: Specialized extraction (KPIs, CapEx, governance metrics)
- **Tier 3 Agents**: Regulatory analysis, industry benchmarking against SBTi/sector data
- **Tier 4 Agents**: Advanced analytics, trend analysis, predictive insights
- **Tier 5 Agents**: Orchestration, decision-making, workflow coordination

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL / Supabase (with vector extensions)
- **ORM**: SQLAlchemy 2.0 (async)
- **AI/ML**:
  - LangChain for orchestration
  - Bytez API (Primary AI provider)
  - Perplexity AI (Fallback)
  - OpenRouter (Secondary fallback)
  - Ollama (Local deployment option)
  - Voyage AI (Embeddings)
- **Document Processing**:
  - PDFPlumber (text extraction)
  - Tesseract OCR (image text extraction)
  - Pillow (image processing)
- **Data Processing**: Pandas, NumPy
- **External APIs**: Yahoo Finance (ESG data), Eurostat (industry benchmarks)

### Frontend
- **Framework**: React 18 + TypeScript
- **Desktop**: Tauri 2.0 (Rust-based native app)
- **Styling**: Tailwind CSS + Radix UI components
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Charts**: Recharts
- **Animations**: Framer Motion

### DevOps & Tools
- **Version Control**: Git
- **Package Management**: npm (frontend), pip (backend)
- **Environment**: .env configuration
- **API Documentation**: OpenAPI/Swagger (auto-generated)

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** and npm ([Download](https://nodejs.org/))
- **Rust** (for Tauri) ([Install](https://www.rust-lang.org/tools/install))
- **PostgreSQL** or **Supabase account** ([Supabase](https://supabase.com/))
- **Tesseract OCR** (optional, for image text extraction)
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/VinnuReddy18/lma-hackathon.git
   cd lma-hackathon
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys and database credentials:
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/greenguard
   # Or use SQLite for development:
   # DATABASE_URL=sqlite+aiosqlite:///./greenguard.db
   
   # AI Providers (at least one required)
   BYTEZ_API_KEY=your_bytez_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   
   # Embeddings
   VOYAGE_API_KEY=your_voyage_api_key
   
   # Supabase (for vector storage)
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   
   # JWT Secret
   JWT_SECRET=your_secure_random_secret_key
   
   # Optional: Tesseract path (if not in PATH)
   TESSERACT_CMD=tesseract
   ```

5. **Set up the database**
   ```bash
   # If using Supabase, run the setup SQL scripts in your Supabase SQL editor:
   # - supabase_setup.sql
   # - supabase_setup_kpi.sql
   # - supabase_setup_sbti.sql
   
   # If using local PostgreSQL with vector extension:
   psql -U postgres -d greenguard -f supabase_setup.sql
   ```

6. **Run the backend server**
   ```bash
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to the desktop app directory**
   ```bash
   cd greenguard-desktop
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure the API endpoint** (if needed)
   
   Update the API base URL in your frontend code if your backend is not on `localhost:8000`

4. **Run in development mode**
   ```bash
   # Run as web app
   npm run dev
   
   # Run as Tauri desktop app
   npm run tauri dev
   ```

5. **Build for production**
   ```bash
   # Build web app
   npm run build
   
   # Build desktop app
   npm run tauri build
   ```

---

## ⚙️ Configuration

### API Keys

GreenGuard requires at least one AI provider to function. Configure your preferred providers in the `.env` file:

| Provider | Purpose | Required? |
|----------|---------|-----------|
| Bytez | Primary AI model for analysis | Recommended |
| Perplexity | Fallback AI provider | Optional |
| OpenRouter | Secondary fallback | Optional |
| Ollama | Local model support | Optional |
| Voyage AI | Text embeddings for RAG | Required for chat |
| Supabase | Vector database | Required for chat |

### Database Options

- **Production**: PostgreSQL with pgvector extension (via Supabase or self-hosted)
- **Development**: SQLite (default, no setup required)

### File Upload Settings

Configure in `.env`:
```env
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
```

---

## 📖 Usage

### 1. **Upload ESG Reports**
   - Navigate to the Upload page
   - Drag and drop PDF reports or select files
   - The system automatically processes and extracts ESG data

### 2. **View Analytics Dashboard**
   - Monitor overall ESG performance
   - Track key metrics and trends
   - View compliance status

### 3. **KPI Benchmarking**
   - Access the KPI Benchmarking tool
   - Compare your metrics against industry standards
   - Validate against SBTi targets

### 4. **Compliance Checking**
   - Run CSRD compliance analysis
   - Check EU Taxonomy alignment
   - Verify sustainability-linked loan covenants

### 5. **Interactive Report Chat**
   - Open any processed report
   - Ask questions in natural language
   - Get AI-powered insights with source citations

### 6. **Use of Proceeds Tracking**
   - Monitor green bond allocations
   - Track eligible vs. ineligible expenses
   - Generate allocation reports

---

## 📚 API Documentation

The backend API is fully documented using OpenAPI/Swagger:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token

#### File Upload & Processing
- `POST /upload/` - Upload ESG report
- `GET /upload/reports` - List all reports
- `GET /upload/reports/{report_id}` - Get report details

#### ESG Extraction
- `POST /extract/esg` - Extract ESG data from report
- `POST /ai-extract/analyze` - AI-powered ESG analysis

#### KPI Management
- `POST /kpi/extract` - Extract KPIs from document
- `GET /kpi/benchmark` - Get industry benchmarks
- `POST /kpi-benchmark/evaluate` - Evaluate KPI performance

#### Compliance
- `POST /compliance/csrd` - CSRD compliance check
- `POST /compliance/taxonomy` - EU Taxonomy alignment check

#### Report Chat
- `POST /report-chat/conversations` - Create chat conversation
- `POST /report-chat/conversations/{id}/messages` - Send message
- `GET /report-chat/conversations/{id}/history` - Get chat history

---

## 📁 Project Structure

```
greenguard/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── agents/              # Multi-tier AI agent system
│   │   │   ├── tier1/           # Document processing agents
│   │   │   ├── tier2/           # Extraction agents
│   │   │   ├── tier3/           # Regulatory & benchmark agents
│   │   │   ├── tier4/           # Analysis agents
│   │   │   └── tier5/           # Orchestrator
│   │   ├── core/                # Core utilities (memory store)
│   │   ├── middleware/          # Request/response middleware
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/             # API endpoints
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── utils/               # Helper functions
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database connection
│   │   └── main.py              # Application entry point
│   ├── migrations/              # Database migrations
│   ├── resources/               # Regulatory documents & data
│   │   ├── EU Regulatories data/
│   │   └── SBT'is Data/
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment template
│   └── supabase_setup*.sql      # Database setup scripts
│
├── greenguard-desktop/          # Tauri desktop application
│   ├── src/
│   │   ├── app/                 # Application pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Upload.tsx
│   │   │   ├── Reports.tsx
│   │   │   ├── KPIBenchmarking.tsx
│   │   │   ├── KPITool.tsx
│   │   │   ├── UseOfProceeds.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/          # Reusable components
│   │   │   ├── ui/              # UI component library
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Layout.tsx
│   │   │   └── ReportChat.tsx
│   │   ├── store/               # State management
│   │   ├── App.tsx              # Main app component
│   │   └── main.tsx             # Entry point
│   ├── src-tauri/               # Rust backend for desktop
│   ├── public/                  # Static assets
│   ├── package.json
│   └── tauri.conf.json          # Tauri configuration
│
├── .gitignore
├── README.md                    # This file
└── 999d46a1-7abf-4330-a3e7-548ea7a16ad0-removebg-preview.png  # Logo
```

---

## 🤝 Contributing

We welcome contributions to GreenGuard! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Use TypeScript strict mode for frontend code
- Write descriptive commit messages
- Add tests for new features
- Update documentation as needed

### Reporting Issues

Found a bug or have a feature request? Please open an issue on GitHub with:
- Clear description of the problem/feature
- Steps to reproduce (for bugs)
- Expected vs. actual behavior
- Screenshots (if applicable)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **EU Regulations**: CSRD, EU Taxonomy documentation
- **SBTi**: Science Based Targets initiative data
- **GRI**: Global Reporting Initiative standards
- **Open Source Community**: All the amazing libraries and frameworks used

---


## 🗺️ Roadmap

### Upcoming Features
- [ ] Multi-language support (French, German, Spanish)
- [ ] Mobile app (iOS/Android)
- [ ] Real-time collaboration features
- [ ] Advanced ML models for predictive analytics
- [ ] Integration with more ESG data providers
- [ ] Automated report generation templates
- [ ] Enhanced visualization options
- [ ] API rate limiting and caching
- [ ] Bulk document processing
- [ ] Custom regulatory framework support

---

<div align="center">
  <p>Built with ❤️ for a sustainable future</p>
  <p>© 2026 GreenGuard ESG Platform</p>
</div>
