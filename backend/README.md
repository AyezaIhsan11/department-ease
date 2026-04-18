# Department Ease - Backend API

AI-Powered Department Administration System built with FastAPI, MongoDB, and LangChain/Gemini.

## Features

- 🔐 **JWT Authentication** - Secure token-based authentication
- 👥 **Student Management** - Complete CRUD operations for student records
- 🤖 **AI Chat Assistant** - Natural language interface powered by Gemini
- 📊 **Analytics Dashboard** - Statistics and data visualization
- 📅 **Event Calendar** - Manage department events
- 📄 **PDF Reports** - Generate monthly and yearly reports
- 📧 **Email Notifications** - SMTP email service
- 📤 **CSV Import/Export** - Bulk operations support

## Tech Stack

- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database with Motor async driver
- **Beanie** - ODN for MongoDB
- **LangChain** - AI orchestration framework
- **Google Gemini** - LLM for natural language processing
- **ReportLab** - PDF generation
- **JWT** - Authentication tokens

## Setup

1. **Install Python 3.10+**

2. **Install MongoDB** and start the service

3. **Copy environment variables**:
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Update `.env` with your credentials**:
   - MongoDB connection string
   - JWT secret key
   - Google Gemini API key
   - SMTP credentials

5. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

6. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

7. **Run the application**:
   ```powershell
   python main.py
   ```

   The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register admin user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Students
- `GET /api/students` - List students (with pagination/filters)
- `GET /api/students/{id}` - Get student details
- `POST /api/students` - Create student
- `PUT /api/students/{id}` - Update student
- `DELETE /api/students/{id}` - Delete student
- `POST /api/students/bulk/delete` - Bulk delete
- `POST /api/students/upload/csv` - CSV upload
- `GET /api/students/export/csv` - CSV export

### Events
- `GET /api/events` - List events
- `POST /api/events` - Create event
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event

### Analytics
- `GET /api/analytics/overview` - Dashboard statistics
- `GET /api/analytics/department-distribution` - Students by department
- `GET /api/analytics/enrollment-trends` - Enrollment trends
- `GET /api/analytics/gpa-distribution` - GPA statistics

### Reports
- `GET /api/reports/monthly` - Generate monthly PDF
- `GET /api/reports/yearly` - Generate yearly PDF
- `GET /api/reports/student-list` - Generate student list PDF

### AI Chat
- `POST /api/chat` - Send message to AI assistant
- `GET /api/chat/history/{conversation_id}` - Get chat history
- `GET /api/chat/conversations` - List conversations

## AI Chat Commands

The AI assistant understands natural language commands like:

- "Add a new student named John Doe with ID CS2024001"
- "Show me all students in Computer Science department"
- "Update student CS2024001 GPA to 3.8"
- "Delete student with ID CS2024002"
- "Give me statistics about all students"
- "Find students with GPA above 3.5"

## Project Structure

```
backend/
├── ai/                 # AI integration
│   ├── agent.py       # LangChain agent
│   ├── tools.py       # AI tools for CRUD
│   └── langchain_setup.py
├── auth/              # Authentication
│   ├── jwt.py         # JWT utils
│   └── dependencies.py
├── models/            # Database models
│   ├── student.py
│   ├── user.py
│   ├── event.py
│   └── chat_history.py
├── routes/            # API endpoints
│   ├── auth.py
│   ├── students.py
│   ├── events.py
│   ├── analytics.py
│   ├── reports.py
│   └── chat.py
├── schemas/           # Pydantic schemas
├── services/          # Business logic
│   ├── pdf_generator.py
│   └── email_service.py
├── config.py          # Configuration
├── database.py        # DB connection
└── main.py           # Application entry
```

## Environment Variables

See `.env.example` for all required environment variables.

## License

MIT
