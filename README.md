# Department Ease

**AI-Powered Department Administration System**

A comprehensive dual-interface system combining an AI chatbot for natural language administration and a feature-rich admin dashboard for department management.

## 🌟 Features

### AI Chat Interface
- Natural language processing with Google Gemini
- Conversational student management
- Context-aware responses
- Action confirmations and history

### Admin Dashboard
- Interactive analytics with Recharts
- Student management (CRUD, search, filters, pagination)
- Event calendar with FullCalendar
- PDF report generation (monthly, yearly, student lists)
- CSV import/export
- Modern, responsive UI with glass morphism

### Backend API
- FastAPI with async support
- MongoDB database
- JWT authentication
- LangChain AI orchestration
- Email notifications (SMTP)
- Background job processing

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (Tested with 3.13)
- Node.js 18+
- MongoDB
- Google Gemini API key

### Backend Setup

1. **Install Prerequisites**
   - Python 3.10+
   - Node.js 18+
   - [MongoDB Community Server](https://www.mongodb.com/try/download/community) (Required for database)

2. **Verify MongoDB is Running**
   Open PowerShell and run:
   ```powershell
   # Check if MongoDB service is running
   Get-Service -Name MongoDB
   # If stopped, start it:
   Start-Service -Name MongoDB
   ```

3. **Configure Environment**
   ```powershell
   cd backend
   Copy-Item .env.example .env
   # Edit .env with your API keys and credentials
   ```

4. **Run the Server**
   ```powershell
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Install Python dependencies
   pip install -r requirements.txt

   # Start the server
   python main.py
   ```

   The API will be available at `http://localhost:8001/docs`

### Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

App will be available at `http://localhost:3000`

## 📖 Documentation

- **Backend API**: See `backend/README.md`
- **Frontend**: See `frontend/README.md`
- **API Documentation**: http://localhost:8001/docs (when running)

## 🔑 First Time Setup

1. Start the backend server
2. Register an admin user via API or MongoDB:
   ```python
   POST /api/auth/register
   {
     "username": "admin",
     "email": "admin@example.com",
     "password": "your_password",
     "role": "admin"
   }
   ```
3. Login via frontend at http://localhost:3000/login
4. Start managing students via dashboard or AI chat!

## 💬 AI Chat Examples

- "Add a new student named John Doe with ID CS2024001"
- "Show me all Computer Science students"
- "Update student CS2024001 GPA to 3.8"
- "Delete student with ID CS2024002"
- "Give me student statistics"

## 📁 Project Structure

```
Department ease/
├── backend/           # FastAPI backend
│   ├── ai/           # LangChain + Gemini integration
│   ├── auth/         # JWT authentication
│   ├── models/       # MongoDB models
│   ├── routes/       # API endpoints
│   ├── services/     # PDF, email services
│   └── main.py       # Application entry
│
└── frontend/         # Next.js frontend
    ├── app/          # Pages and layouts
    ├── lib/          # API client and types
    └── components/   # React components
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- MongoDB (Motor/Beanie)
- LangChain + Google Gemini
- ReportLab (PDF generation)
- JWT Authentication
- Celery (Background jobs)

**Frontend:**
- Next.js 14 (React)
- TypeScript
- TailwindCSS
- Recharts
- FullCalendar
- Axios

## 📝 License

MIT


