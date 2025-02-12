# InvestHub - Startup Investment Matching Platform

InvestHub is a modern web application that helps startups connect with potential investors by analyzing their business profile and providing tailored investor recommendations. The platform uses advanced matching algorithms to suggest the most suitable investors based on various parameters like industry, funding requirements, and business stage.

## 🚀 Features

- **Smart Investor Matching**: Advanced algorithm to match startups with relevant investors
- **Real-time Analysis**: Stream-based response system for immediate feedback
- **Professional Form Interface**: Comprehensive startup profile collection including:
  - Company Information
  - Industry Classification
  - Funding Requirements
  - Equity Offering
  - Investment Timeline
  - Fund Utilization Plans

## 🛠️ Tech Stack

### Frontend
- React with TypeScript
- Material-UI (MUI) for UI components
- Vite as build tool
- Markdown parsing for formatted responses

### Backend
- FastAPI (Python)
- Streaming response capability
- AI-powered analysis

## 🏗️ Project Structure

```
investHub/
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx         # Main application component
│   │   ├── main.tsx        # Entry point
│   │   └── utils/          # Utility functions
│   ├── package.json
│   └── vite.config.ts
│
└── backend/                 # FastAPI backend
    ├── main.py             # API endpoints
    └── models.py           # Data models
```

## 🚦 Getting Started

### Prerequisites
- Node.js (v14 or higher)
- Python 3.11 or higher
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shubham-petwal/InvestHub.git
   cd investHub
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   The backend will be available at `http://localhost:8000`

2. **Start the Frontend Development Server**
   ```bash
   cd frontend
   npm run dev
   ```
   The application will be available at `http://localhost:5173`

## 💡 Usage

1. Fill in the startup details in the form:
   - Company name and basic information
   - Select your industry and company stage
   - Specify funding requirements and equity offering
   - Choose funding timeline and primary use of funds
   - Provide a detailed description of your business

2. Submit the form to receive AI-powered investor recommendations

3. Review the detailed analysis and investor matches in real-time

## 🎨 UI Features

- Clean and professional interface
- Responsive design
- Real-time loading indicators
- Markdown-formatted responses
- Easy navigation between form and results
- Success notifications and error handling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is not licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Material-UI for the beautiful component library
- FastAPI for the efficient backend framework
- All contributors who have helped shape this project

---

For support or questions, please open an issue in the repository. 