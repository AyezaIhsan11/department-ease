# Department Ease - Frontend

AI-Powered Department Administration System - Next.js Frontend

## Features

- 🎨 **Modern UI** - Beautiful design with glass morphism and gradients
- 🔐 **Authentication** - JWT-based secure login
- 💬 **AI Chat Interface** - Natural language student management
- 📊 **Analytics Dashboard** - Interactive charts and statistics
- 📅 **Event Calendar** - FullCalendar integration
- 👥 **Student Management** - CRUD operations with search and filters
- 📄 **PDF Reports** - Generate and download reports
- 📱 **Responsive Design** - Works on all devices

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first CSS framework
- **Recharts** - Data visualization
- **FullCalendar** - Event calendar
- **Axios** - HTTP client with JWT interceptors

## Setup

1. **Install Node.js 18+**

2. **Install dependencies**:
   ```powershell
   cd frontend
   npm install
   ```

3. **Configure environment**:
   - Update `.env.local` with your backend API URL
   - Default: `NEXT_PUBLIC_API_URL=http://localhost:8000`

4. **Run development server**:
   ```powershell
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

5. **Build for production**:
   ```powershell
   npm run build
   npm start
   ```

## Project Structure

```
frontend/
├── app/
│   ├── chat/page.tsx          # AI chat interface
│   ├── dashboard/
│   │   ├── page.tsx          # Main dashboard
│   │   ├── students/page.tsx # Student management
│   │   ├── calendar/page.tsx # Event calendar
│   │   └── reports/page.tsx  # PDF reports
│   ├── login/page.tsx        # Login page
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home redirect
│   └── globals.css          # Global styles
├── lib/
│   ├── api.ts               # Axios instance
│   └── types.ts             # TypeScript interfaces
├── components/              # Reusable components
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

## Pages

### Login (`/login`)
- Secure authentication with JWT
- Glass morphism design
- Error handling

### Dashboard (`/dashboard`)
- Statistics cards (total students, active, GPA, enrollments)
- Charts (department distribution, enrollment trends)
- Quick actions

### Chat (`/chat`)
- AI assistant interface
- Message history
- Natural language commands
- Action confirmations

### Students (`/dashboard/students`)
- Student table with pagination
- Search and filters
- Delete functionality
- CSV export

### Calendar (`/dashboard/calendar`)
- FullCalendar integration
- Color-coded event categories
- Month/week views

### Reports (`/dashboard/reports`)
- Monthly PDF reports
- Yearly PDF reports
- Student directory PDF

## Design System

The app uses a modern design system with:

- **Glass Morphism** - Translucent cards with blur effects
- **Gradients** - Vibrant color gradients
- **Animations** - Smooth transitions and micro-animations
- **Custom Colors** - Blue and purple primary palette
- **Inter Font** - Clean, modern typography

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Default Credentials

Use the credentials created during backend setup. If you haven't created a user yet, register through the backend API or create one in MongoDB.

## License

MIT
