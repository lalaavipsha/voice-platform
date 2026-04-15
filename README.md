# 🎤 AI Voice Platform

An AI-powered voice conversation platform. Speak to the AI, and it responds with voice — powered entirely by AWS AI services (Transcribe + Bedrock + Polly), deployed on AWS.

## Architecture

```
User → Next.js Frontend → FastAPI Backend → AWS AI Services
       (S3 + CloudFront)   (ECS/Fargate)    (Transcribe, Bedrock, Polly)
```

**Voice Flow:**
1. 🎙️ User speaks into microphone (browser captures audio)
2. 📡 Audio sent to backend API
3. 🔤 Amazon Transcribe converts speech → text
4. 🧠 Amazon Bedrock (Claude) generates a response
5. 🔊 Amazon Polly converts response → speech
6. 🎧 Audio response played back to user

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, React |
| Backend | Python 3.12, FastAPI |
| AI (STT) | Amazon Transcribe |
| AI (LLM) | Amazon Bedrock (Claude 3.5 Haiku) |
| AI (TTS) | Amazon Polly (Neural voices) |
| Infrastructure | AWS ECS Fargate, S3, CloudFront, DynamoDB |
| CI/CD | GitHub Actions |
| Containers | Docker (Colima on macOS) |
| IaC | CloudFormation |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- AWS Account with Bedrock, Transcribe, and Polly access
- AWS CLI configured (`aws configure`)
- (Optional) [Colima](https://github.com/abiosoft/colima) for Docker

### 1. Clone & Setup

```bash
git clone https://github.com/lalaavipsha/voice-platform.git
cd voice-platform
make setup
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — set your AWS_REGION and AWS_S3_BUCKET
```

### 3. AWS Setup

```bash
# Make sure AWS CLI is configured
aws configure
# Region: eu-west-2 (or your preferred region)

# Enable Bedrock model access (one-time):
# Go to AWS Console → Bedrock → Model access → Enable Claude 3 Haiku

# Create S3 bucket for audio processing:
aws s3 mb s3://voice-platform-dev-audio
```

### 4. Run Locally

**Terminal 1 — Backend:**
```bash
make backend
# API running at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
make frontend
# App running at http://localhost:3000
```

### 5. (Alternative) Run with Docker

```bash
# Start Colima (Docker runtime)
colima start

# Start all services
make docker-up
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API docs (Swagger) |
| POST | `/api/v1/voice/transcribe` | Audio → Text (Transcribe) |
| POST | `/api/v1/voice/chat` | Text → AI Response (Bedrock) |
| POST | `/api/v1/voice/speak` | Text → Audio (Polly) |
| POST | `/api/v1/voice/converse` | Audio → AI Audio (full pipeline) |

## Project Structure

```
voice-platform/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   │   ├── health.py   # Health check endpoint
│   │   │   └── voice.py    # Voice API endpoints
│   │   ├── services/
│   │   │   └── ai_service.py  # AWS AI integration (Transcribe, Bedrock, Polly)
│   │   ├── config.py       # App configuration
│   │   └── main.py         # FastAPI app entry point
│   ├── tests/              # Backend tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Next.js frontend
│   ├── src/app/
│   │   ├── layout.tsx      # App layout
│   │   └── page.tsx        # Main voice UI
│   ├── Dockerfile
│   └── package.json
├── infra/                   # AWS infrastructure
│   └── cloudformation/
│       └── ecs-stack.yml   # ECS + VPC + ALB stack
├── .github/workflows/       # CI/CD pipelines
│   ├── backend-ci.yml      # Backend test + deploy
│   └── frontend-ci.yml     # Frontend lint + build
├── docker-compose.yml       # Local multi-service setup
├── Makefile                 # Developer commands
└── README.md
```

## Available Commands

```bash
make help          # Show all commands
make setup         # First-time setup
make backend       # Start backend dev server
make frontend      # Start frontend dev server
make docker-up     # Start with Docker
make docker-down   # Stop Docker services
make test          # Run backend tests
make lint          # Check code quality
make format        # Auto-format code
make clean         # Remove build artifacts
```

## Deployment

### Backend (ECS Fargate)

The backend deploys automatically via GitHub Actions when you push to `main`:

1. Tests run
2. Docker image built and pushed to ECR
3. ECS service updated with new image

### Frontend (S3 + CloudFront)

The frontend is exported as a static site (`next export`) and hosted on S3 with CloudFront as the CDN. Deploy with:

```bash
cd frontend && npm run build
aws s3 sync out/ s3://voice-platform-frontend-<ACCOUNT_ID> --delete
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
```

### Infrastructure

Deploy the CloudFormation stack:

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/ecs-stack.yml \
  --stack-name voice-platform \
  --capabilities CAPABILITY_IAM
```

## AWS Services Used

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Amazon Transcribe | Speech-to-Text | 60 min/mo (12 months) |
| Amazon Bedrock (Claude) | AI Chat/LLM | Pay per token (~$0.25/1M input) |
| Amazon Polly | Text-to-Speech | 5M chars/mo (12 months) |
| ECS Fargate | Container hosting | None (use small tasks) |
| S3 | Audio + frontend hosting | 5GB free |
| CloudFront | CDN / frontend delivery | 1TB transfer/mo (12 months) |
| DynamoDB | Conversation storage | 25GB free |
| CloudWatch | Monitoring & logs | Basic free |

## Development Roadmap

- [x] Phase 1: Project structure & local dev
- [x] Phase 2: AI voice MVP (AWS AI integration)
- [x] Phase 3: Containerize & deploy to AWS
- [x] Phase 4: CI/CD pipeline
- [ ] Phase 5: Security & monitoring
- [ ] Phase 6: Scale & optimize

## License

MIT
