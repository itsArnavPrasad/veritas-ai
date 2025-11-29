# Veritas AI

<div align="center">

**Multimodal Truth Engine for Misinformation Detection**

*Verify text, images, and video simultaneously with advanced AI-powered fact-checking*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-1.19-orange.svg)](https://github.com/google/adk)

</div>

---

## 🌟 Overview

**Veritas AI** is a comprehensive, multimodal misinformation detection system that combines cutting-edge AI technologies to verify claims across text, images, and video content. Built with a sophisticated agent-based architecture using Google's Agent Development Kit (ADK), the system provides real-time fact-checking capabilities with cross-modal fusion analysis.

### Key Capabilities

- ✅ **Multimodal Verification**: Simultaneously analyze text, images, and video
- ✅ **Cross-Modal Fusion**: Intelligently combine evidence from multiple modalities
- ✅ **Real-Time Twitter Monitoring**: Stream and visualize tweets on an interactive map
- ✅ **Advanced AI Agents**: Sophisticated agent pipeline for claim extraction and verification
- ✅ **Deepfake Detection**: Detect AI-generated content and manipulation artifacts
- ✅ **Comprehensive Evidence Retrieval**: Multi-source evidence gathering from web, Twitter, and Instagram
- ✅ **Beautiful Modern UI**: Immersive 3D interface with real-time pipeline visualization

---

## 🏗️ Architecture

Veritas AI consists of three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Veritas AI System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │◄──►│   Backend   │◄──►│     ADK     │  │
│  │   (React)    │    │  (FastAPI)   │    │   (Agents)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                      │         │
│         └───────────────────┴──────────────────────┘         │
│                            │                                  │
│                   ┌─────────┴─────────┐                      │
│                   │                   │                       │
│            ┌──────▼──────┐    ┌──────▼──────┐                │
│            │   Gemini    │    │  Pathway    │                │
│            │     VLM     │    │  Streaming  │                │
│            └─────────────┘    └─────────────┘                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. **veritas-ai-frontend** (React + TypeScript)
- Modern, responsive UI with 3D effects and animations
- Real-time pipeline visualization
- Interactive Twitter map with location-based clustering
- Multimodal input handling (text, image, video)
- Results visualization with detailed analysis

#### 2. **veritas-ai-backend** (FastAPI + Python)
- RESTful API for verification requests
- Multimodal analysis services (text, image, video)
- Cross-modal fusion engine
- Real-time streaming via Server-Sent Events (SSE)
- Twitter scraping and geocoding services
- Pathway integration for real-time data processing
- PostgreSQL database for verification tracking

#### 3. **veritas-ai-adk** (Google ADK Agents)
- Coordinator agent orchestrating the verification pipeline
- Claim extraction and preprocessing
- Question generation (6 queries in 3 chains)
- Web search and evidence retrieval
- Verifier ensemble with multiple analysis signals
- Natural Language Inference (NLI) analysis
- Source credibility assessment

---

## 🚀 Features

### 📝 Text Verification

The text verification pipeline uses a sophisticated multi-agent system:

1. **Preprocessing Agent**: Cleans and structures raw text, extracts metadata
2. **Claim Extraction Agent**: Identifies exactly 3 most important, verifiable claims
3. **Severity/Source Suggester**: Analyzes claim severity and recommends trusted sources
4. **Question Generation Agent**: Generates 6 strategic queries across 3 chains:
   - Chain 1: Direct verification queries
   - Chain 2: Context/detail queries
   - Chain 3: Disambiguation queries
5. **Web Search Answer Agent**: Retrieves evidence from:
   - Web search (Google)
   - Twitter/X (via Nitter)
   - Instagram
   - Answer synthesis per query
6. **Comprehensive Answer Synthesis**: Merges all evidence into detailed answers
7. **Verifier Ensemble**: Final verification using:
   - Natural Language Inference (NLI)
   - Stance detection
   - Source credibility scoring
   - Temporal alignment checks

### 🖼️ Image Analysis

Powered by Google Gemini Vision Language Model (VLM):

- **Detailed Image Description**: Comprehensive factual description of visual content
- **Object Detection**: Identifies objects, people, actions, and environment
- **OCR Capabilities**: Extracts visible text from images
- **AI Artifact Detection**: Identifies AI-generated content indicators:
  - Extra or missing fingers
  - Distorted hands or limbs
  - Unnatural textures
  - Inconsistent lighting
  - Warped reflections
  - Anatomically impossible shapes

### 🎥 Video Analysis

Comprehensive video verification with multiple authenticity checks:

- **Video Description**: Combined audio and visual analysis
- **Transcription**: Full spoken text transcription with timestamps
- **Entity Extraction**: People, organizations, locations, dates
- **Deepfake Detection**: 
  - Facial analysis for unnatural movements
  - Lighting and shadow inconsistencies
  - Generation artifacts
  - Movement pattern analysis
- **Audio-Visual Sync Analysis**: Lip-sync and action-audio alignment
- **Caption Sync Analysis**: Verification of caption accuracy
- **Technical Artifacts Detection**: Compression, frame inconsistencies, edit traces
- **Claim Extraction**: Extracts 3 most important claims from video content

### 🔄 Cross-Modal Fusion

Intelligently combines evidence from all modalities:

- **Content Relevance Check**: Determines if image/video relates to text claims
- **Calibrated Verdict**: Unified verdict accounting for all evidence
- **Modality Agreement Analysis**: Identifies conflicts or agreements between sources
- **Unified Confidence Scoring**: Weighted confidence based on all modalities

### 🗺️ Real-Time Twitter Monitoring

Interactive map visualization of Twitter content:

- **Real-Time Streaming**: Live tweet monitoring using Pathway framework
- **Location Extraction**: Automatic geocoding of tweet locations
- **Topic Clustering**: Groups related tweets by topic
- **Interactive Map**: Visualize tweets on a world map with clustering
- **Nitter Integration**: Scrapes Twitter/X content without API requirements
- **Geographic Analysis**: Location-based misinformation tracking

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Google Gemini API Key
- Google ADK Server (for agent execution)

### Backend Setup

```bash
cd veritas-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add:
# - POSTGRES_URL=postgresql://user:password@localhost:5432/veritas_ai
# - GEMINI_API_KEY=your_gemini_api_key
# - ADK_SERVER_URL=http://localhost:5010

# Initialize database
createdb veritas_ai
# Tables will be auto-created on first run

# Run the server
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### ADK Setup

```bash
cd veritas-ai-adk

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GEMINI_API_KEY=your_gemini_api_key
export ADK_SERVER_URL=http://localhost:5010

# Start ADK server (if not already running)
# Follow Google ADK documentation for server setup
```

### Frontend Setup

```bash
cd veritas-ai-frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local and add:
# VITE_API_URL=http://localhost:8000

# Run development server
npm run dev
```

---


### Frontend Usage

1. Navigate to the landing page
2. Add inputs (text, image, or video)
3. Click "Analyze All"
4. Watch real-time pipeline progress
5. View comprehensive results with evidence

---

## 🧪 Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **PostgreSQL**: Relational database
- **SQLAlchemy**: ORM for database operations
- **Google Gemini API**: Vision Language Model for image/video analysis
- **Pathway**: Real-time data processing framework
- **Nitter**: Twitter scraping service
- **Selenium**: Web scraping capabilities
- **Sentence Transformers**: Embedding models

### Frontend
- **React 19**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool and dev server
- **Framer Motion**: Animation library
- **Three.js**: 3D graphics
- **Mapbox GL**: Interactive maps
- **Deck.gl**: WebGL-powered visualization
- **Tailwind CSS**: Utility-first CSS framework

### AI/ML
- **Google ADK**: Agent Development Kit
- **Google Gemini 2.5 Pro/Flash**: Large Language Models
- **Natural Language Inference**: Claim-evidence matching
- **Stance Detection**: Support/oppose/neutral classification
- **Source Credibility Scoring**: Domain trustworthiness assessment

---

## 📊 Verification Pipeline Flow

```
Input (Text/Image/Video)
    │
    ├─► Text Analysis
    │   ├─► Preprocessing
    │   ├─► Claim Extraction (3 claims)
    │   ├─► Question Generation (6 queries)
    │   ├─► Evidence Retrieval (Web/Twitter/Instagram)
    │   └─► Verifier Ensemble (NLI/Stance/Credibility/Temporal)
    │
    ├─► Image Analysis
    │   ├─► VLM Description
    │   └─► AI Artifact Detection
    │
    ├─► Video Analysis
    │   ├─► Comprehensive Video Description
    │   ├─► Deepfake Detection
    │   ├─► Audio-Visual Sync
    │   ├─► Caption Sync
    │   ├─► Technical Artifacts
    │   └─► Claim Extraction
    │
    └─► Cross-Modal Fusion
        ├─► Content Relevance Check
        ├─► Calibrated Verdict
        └─► Unified Results
```

---

## 🗂️ Project Structure

```
veritas-ai/
├── veritas-ai-backend/          # FastAPI backend
│   ├── main.py                  # Application entry point
│   ├── config.py                # Configuration
│   ├── models/                  # Database models
│   ├── routers/                 # API route handlers
│   ├── services/                # Business logic
│   │   ├── adk_service.py       # ADK agent integration
│   │   ├── image_analysis.py    # Image VLM analysis
│   │   ├── video_analysis.py    # Video analysis
│   │   ├── cross_modal_fusion.py # Fusion engine
│   │   ├── nitter_scraper.py    # Twitter scraping
│   │   ├── pathway_stream.py    # Real-time streaming
│   │   └── ...
│   └── storage/                 # File storage
│
├── veritas-ai-adk/              # Google ADK agents
│   ├── coordinator/             # Main orchestrator
│   ├── raw_text_preprocess/     # Text preprocessing
│   ├── claim_extraction/        # Claim extraction
│   ├── question_generation/     # Query generation
│   ├── web_search_answer/       # Evidence retrieval
│   ├── verifier_ensemble/       # Final verification
│   └── ...
│
└── veritas-ai-frontend/          # React frontend
    ├── src/
    │   ├── pages/               # Page components
    │   ├── components/          # UI components
    │   │   ├── ui/              # Reusable UI elements
    │   │   └── layout/          # Layout components
    │   └── lib/                 # Utilities
    └── public/                  # Static assets
```

---

## 🔐 Environment Variables

### Backend (.env)
```bash
POSTGRES_URL=postgresql://user:password@localhost:5432/veritas_ai
GEMINI_API_KEY=your_gemini_api_key
ADK_SERVER_URL=http://localhost:5010
```

### Frontend (.env.local)
```bash
VITE_API_URL=http://localhost:8000
```

### ADK
```bash
GEMINI_API_KEY=your_gemini_api_key
ADK_SERVER_URL=http://localhost:5010
```

---

## 🧩 Key Components

### Coordinator Agent
The main orchestrator that manages the entire text verification pipeline:
- Sequential agent workflow
- State management across agents
- Final verdict generation

### Verifier Ensemble
Multi-signal verification system:
- **Evidence Analyzer**: Analyzes evidence using 4 signals
- **Final Verifier**: Combines signals with weighted scoring
- **Source Comparison**: Strong source credibility weighting

### Cross-Modal Fusion
Intelligent combination of text, image, and video evidence:
- Relevance scoring
- Conflict detection
- Unified confidence calculation

### Twitter Map Visualization
Real-time geographic visualization:
- Location extraction and geocoding
- Topic-based clustering
- Interactive map with Deck.gl

---

## 📈 Performance & Scalability

- **Async Processing**: Background task processing for long-running verifications
- **Streaming**: Real-time progress updates via SSE
- **Database Optimization**: Efficient querying with SQLAlchemy
- **File Storage**: Organized storage structure per verification
- **Caching**: Strategic caching of analysis results

---

## 🛠️ Development

### Running in Development Mode

**Backend:**
```bash
cd veritas-ai-backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd veritas-ai-frontend
npm run dev
```

**ADK Server:**
```bash
# Follow Google ADK documentation
# Typically runs on port 5010
```

### Testing

```bash
# Backend tests
cd veritas-ai-backend
pytest

# Frontend tests
cd veritas-ai-frontend
npm test
```

---

## 📝 API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Google ADK**: Agent Development Kit for sophisticated agent workflows
- **Google Gemini**: Vision Language Models for multimodal analysis
- **Pathway**: Real-time data processing framework
- **FastAPI**: Modern Python web framework
- **React**: UI framework
- **Mapbox**: Mapping and geocoding services

---

## 📧 Contact & Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Contact the development team

---

## 🎯 Roadmap

- [ ] Enhanced deepfake detection models
- [ ] Additional social media platform support
- [ ] Multi-language verification support
- [ ] Advanced clustering algorithms
- [ ] Real-time collaboration features
- [ ] Mobile app development
- [ ] API rate limiting and quotas
- [ ] Advanced analytics dashboard

---

<div align="center">

**Built with ❤️ for Truth and Accuracy**

*Veritas AI - Multimodal Truth Engine*

</div>
