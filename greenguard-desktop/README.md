# GreenGuard ESG Desktop

<p align="center">
  <img src="C:\Users\Vinayak Paka\Desktop\GreenGuard\lma-hackathon\999d46a1-7abf-4330-a3e7-548ea7a16ad0-removebg-preview.png" alt="GreenGuard Logo" width="200"/>
</p>

<p align="center">
  <strong>AI-Powered ESG Compliance & Sustainability Intelligence Platform</strong>
</p>

<p align="center">
  A cross-platform desktop application for comprehensive ESG (Environmental, Social, and Governance) analysis, compliance monitoring, and green finance management.
</p>

---

## 🌟 Overview

**GreenGuard ESG Desktop** is a sophisticated desktop application built with Tauri and React that leverages artificial intelligence to analyze ESG documents, monitor compliance scores, and manage green bond transactions. The application provides real-time insights into sustainability metrics, taxonomy alignment, and use-of-proceeds tracking for green finance instruments.

## ✨ Key Features

### 📊 **Dashboard & Analytics**
- **Real-time ESG Scoring**: Visual dashboard with comprehensive ESG compliance scores
- **Multi-dimensional Metrics**: Track carbon, energy efficiency, taxonomy alignment, water, and waste metrics
- **Interactive Charts**: Radar charts and bar graphs for score visualization
- **Compliance Alerts**: Automated notifications for pending reviews and verification status

### 🤖 **AI-Powered Document Analysis**
- **Intelligent Document Upload**: Support for PDF, DOCX, and XLSX formats
- **Automated ESG Evaluation**: AI-driven analysis of sustainability reports and documentation
- **Multi-model Support**: Integration with OpenAI GPT-4, Anthropic Claude, and Google Gemini
- **Natural Language Processing**: Extract insights from unstructured ESG data

### 💬 **Interactive Report Chat**
- **Conversational AI**: Ask questions about your ESG reports using natural language
- **Citation-backed Answers**: All responses include source references and evidence
- **Context-aware**: Chat understands your uploaded documents and report context
- **Session History**: Maintain conversation continuity across sessions

### 📈 **KPI Management & Benchmarking**
- **Custom KPI Configuration**: Define and track industry-specific ESG KPIs
- **Target Setting**: Set baseline and target values for performance metrics
- **Progress Tracking**: Monitor KPI achievement over time
- **Industry Benchmarking**: Compare performance against sector standards
- **Peer Analysis**: Evaluate positioning relative to competitors

### 💰 **Use of Proceeds Tracking**
- **Green Bond Management**: Track allocation of green finance proceeds
- **Transaction Monitoring**: Verify compliance of individual transactions
- **Category Classification**: Align spending with green taxonomy categories
- **Allocation Reports**: Generate detailed use-of-proceeds documentation
- **Real-time Compliance**: Monitor transaction-level taxonomy alignment

### 📝 **Report Management**
- **Comprehensive Report Library**: Store and manage all ESG evaluations
- **Detailed Analysis**: View in-depth compliance scores and recommendations
- **Export Capabilities**: Generate reports for stakeholders
- **Version History**: Track changes and improvements over time

### 🔐 **Security & Authentication**
- **Secure Login**: User authentication with JWT tokens
- **Role-based Access**: Protected routes and data isolation
- **Local Storage**: Secure credential management with Zustand

---

## 🏗️ System Architecture

### Technology Stack

#### **Frontend**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS with custom design system
- **UI Components**: Radix UI primitives
- **State Management**: Zustand for authentication, TanStack Query for server state
- **Routing**: React Router v6
- **Charts**: Recharts for data visualization
- **Markdown**: React Markdown for rich text rendering

#### **Desktop Framework**
- **Runtime**: Tauri 2.0 (Rust-based)
- **APIs**: File system access, native dialogs
- **Security**: Content Security Policy (CSP) enforcement
- **Platform**: Cross-platform (Windows, macOS, Linux)

#### **Backend Integration**
- **API Client**: Axios with interceptors
- **State Caching**: TanStack Query with intelligent invalidation
- **Backend**: Python FastAPI (connected via HTTP)
- **AI Models**: OpenAI, Anthropic, Google Gemini integration

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GreenGuard Desktop App                   │
│                     (Tauri + React)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Dashboard   │  │   Upload     │  │   Reports    │     │
│  │   Module     │  │   Module     │  │   Module     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  KPI Tool    │  │ Use of       │  │  Settings    │     │
│  │   Module     │  │  Proceeds    │  │   Module     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│              State Management Layer                          │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │   Zustand Store      │  │  TanStack Query      │        │
│  │  (Auth, UI State)    │  │  (Server Cache)      │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│              Tauri Native Layer (Rust)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ File System  │  │    Dialog    │  │   Security   │     │
│  │   Plugin     │  │   Plugin     │  │     CSP      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
                    HTTP/HTTPS (REST API)
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              Backend API Server (FastAPI)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ESG Analysis │  │  Compliance  │  │   Chat/RAG   │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     KPI      │  │ Use of       │  │ Document     │     │
│  │   Service    │  │   Proceeds   │  │  Processing  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                   AI Integration Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  OpenAI GPT  │  │   Anthropic  │  │    Google    │     │
│  │     (4/4o)   │  │    Claude    │  │    Gemini    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│  ┌────────────────────────────────────────────────┐         │
│  │         Database (PostgreSQL/SQLite)           │         │
│  │  • User Data  • Reports  • KPIs  • Sessions   │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Upload**: User uploads ESG documents through the desktop app
2. **File Transfer**: Tauri's file system plugin securely transfers files to backend
3. **AI Processing**: Backend orchestrates AI model analysis of documents
4. **Report Generation**: System generates comprehensive compliance reports
5. **Storage**: Reports and metadata stored in database
6. **Caching**: TanStack Query caches data for optimal performance
7. **Visualization**: React components render insights and scores
8. **Interaction**: Users can chat with reports using RAG-based AI assistant

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18 or higher)
- **npm** or **yarn**
- **Rust** (for Tauri development)
- **Backend API** running on `http://localhost:8000`

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd greenguard-desktop
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure backend connection**
   
   Ensure your backend API is running on `http://localhost:8000`. The app connects to the following endpoints:
   - `/api/auth/*` - Authentication
   - `/api/esg/*` - ESG evaluations and reports
   - `/api/compliance/*` - Compliance scoring
   - `/api/kpi/*` - KPI management
   - `/api/proceeds/*` - Use of proceeds tracking
   - `/api/chat/*` - Report chat functionality

### Development

Run the application in development mode:

```bash
npm run tauri dev
```

This will:
- Start the Vite development server on `http://localhost:1420`
- Launch the Tauri application window
- Enable hot module replacement (HMR)

### Building

Build the production application:

```bash
npm run tauri build
```

This generates platform-specific installers in `src-tauri/target/release/bundle/`:
- **Windows**: `.msi` and `.exe` installers
- **macOS**: `.dmg` and `.app` bundle
- **Linux**: `.deb`, `.AppImage`, and `.rpm` packages

---

## 📁 Project Structure

```
greenguard-desktop/
├── src/
│   ├── app/                    # Main application pages
│   │   ├── Dashboard.tsx       # Overview dashboard
│   │   ├── Upload.tsx          # Document upload & AI analysis
│   │   ├── Reports.tsx         # Report listing
│   │   ├── ReportDetail.tsx    # Detailed report view
│   │   ├── KPITool.tsx         # KPI management
│   │   ├── KPIBenchmarking.tsx # Industry benchmarking
│   │   ├── UseOfProceeds.tsx   # Green bond tracking
│   │   ├── Settings.tsx        # App settings
│   │   ├── Login.tsx           # Authentication
│   │   └── Register.tsx        # User registration
│   │
│   ├── components/             # Reusable React components
│   │   ├── Layout.tsx          # App layout wrapper
│   │   ├── Header.tsx          # Top navigation
│   │   ├── Sidebar.tsx         # Side navigation
│   │   ├── ProtectedRoute.tsx  # Auth guard
│   │   ├── ReportChat.tsx      # AI chat interface
│   │   ├── ESGMetricChart.tsx  # Chart components
│   │   ├── ScoreGauge.tsx      # Score visualization
│   │   └── FilePicker.tsx      # File upload component
│   │
│   ├── store/                  # State management
│   │   └── authStore.ts        # Authentication state
│   │
│   ├── App.tsx                 # Root component
│   ├── main.tsx                # Application entry point
│   └── index.css               # Global styles
│
├── src-tauri/
│   ├── src/
│   │   └── main.rs             # Tauri entry point
│   ├── Cargo.toml              # Rust dependencies
│   ├── tauri.conf.json         # Tauri configuration
│   └── build.rs                # Build script
│
├── package.json                # Node dependencies
├── tsconfig.json               # TypeScript config
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind CSS config
└── postcss.config.js           # PostCSS config
```

---

## 🎨 Features in Detail

### Document Upload & AI Analysis

The upload module supports:
- **Multi-file Upload**: Upload multiple documents simultaneously
- **Format Support**: PDF, DOCX, XLSX files
- **AI Model Selection**: Choose from GPT-4, Claude, or Gemini
- **Real-time Processing**: Live progress indicators
- **Automatic Extraction**: AI extracts ESG metrics and compliance data

### ESG Scoring Algorithm

The application calculates scores across multiple dimensions:
- **Carbon Emissions**: Scope 1, 2, 3 emissions tracking
- **Energy Efficiency**: Renewable energy usage and efficiency metrics
- **Taxonomy Alignment**: EU Taxonomy and other framework compliance
- **Water Management**: Water usage and conservation metrics
- **Waste Management**: Circular economy and waste reduction

### KPI Benchmarking

Compare your performance against:
- **Industry Averages**: Sector-specific benchmarks
- **Peer Companies**: Direct competitor analysis
- **Historical Trends**: Track improvement over time
- **Best Practices**: Top performer comparisons

### Use of Proceeds Verification

For green bonds and sustainable finance:
- **Transaction Validation**: Ensure spending aligns with green categories
- **Allocation Tracking**: Monitor fund distribution
- **Reporting**: Generate investor-ready allocation reports
- **Compliance Checks**: Verify taxonomy alignment

---

## 🔧 Configuration

### Tauri Configuration

Edit `src-tauri/tauri.conf.json` to customize:
- Window dimensions and behavior
- Application identifier
- Security policies (CSP)
- Bundle settings and icons

### Backend API URL

Update the API base URL in your environment or API configuration file if your backend runs on a different port or domain.

---

## 🔐 Security

- **Content Security Policy**: Strict CSP to prevent XSS attacks
- **Secure Communication**: HTTPS support for production
- **Token-based Auth**: JWT authentication with secure storage
- **Input Validation**: Client-side and server-side validation
- **File Upload Restrictions**: Type and size validation

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Tauri Team**: For the excellent cross-platform framework
- **OpenAI, Anthropic, Google**: For AI model APIs
- **Radix UI**: For accessible component primitives
- **TailwindCSS**: For the utility-first CSS framework

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

---

## 🗺️ Roadmap

### Upcoming Features
- [ ] Real-time collaboration
- [ ] Advanced data export options (Excel, PowerPoint)
- [ ] Mobile companion app
- [ ] Blockchain-based verification
- [ ] Machine learning model training on custom data
- [ ] Multi-language support
- [ ] Offline mode with sync
- [ ] Integration with major ESG frameworks (GRI, SASB, TCFD)

---

<p align="center">
  Made with 💚 for a sustainable future
</p>
