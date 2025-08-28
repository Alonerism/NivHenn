# Insurance Master

A comprehensive local Tkinter application for managing building insurance policies with an agent-to-building table view, editing capabilities, LLM Q&A, and email alerts.

## 🚀 Features

### Core Functionality
- **Data Management**: SQLite backend with agents, buildings, and policies
- **Table View**: Agent-to-building table with dark theme using ttkbootstrap
- **Policy Parsing**: PDF upload and text extraction using PyPDF2/pdfplumber
- **AI Q&A**: Local RAG system with OpenAI API for policy questions
- **Email Alerts**: Automated notifications for expiring policies
- **File Management**: Local storage of policy PDFs

### Advanced Features
- **Smart Text Extraction**: Automatic parsing of policy documents
- **Knowledge Base**: Local vector storage with ChromaDB for fast retrieval
- **Policy Comparison**: Compare multiple policies side-by-side
- **Expiration Tracking**: Visual indicators for policies expiring soon
- **Multi-format Support**: Handles various PDF formats and date formats

## 📋 Requirements

- Python 3.8 or higher
- OpenAI API key (for Q&A functionality)
- Email account with SMTP access (for alerts)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Insurance-Master
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration (Gmail recommended)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Alert Recipients
ALERT_EMAIL_1=recipient1@example.com
ALERT_EMAIL_2=recipient2@example.com
```

**Note for Gmail Users:**
- Use an App Password, not your regular password
- Enable 2-factor authentication first
- Generate an App Password in Google Account settings

## 🚀 Running the Application

### Option 1: Direct Python Execution
```bash
python src/main.py
```

### Option 2: Using the Launcher Script
```bash
python run.py
```

### Option 3: Module Execution
```bash
cd src
python -m main
```

## 📖 Usage Guide

### 1. Policy Management Tab
- **View Policies**: Main table shows agents and their assigned buildings
- **Select Buildings**: Click on any building cell to select it
- **Edit Assignments**: Use the "Edit Assignment" button to move buildings between agents
- **Add New Items**: Use the "Add New" button to create agents, buildings, or policies

### 2. Policy Q&A Tab
- **Ask Questions**: Type natural language questions about your policies
- **Sample Questions**: Use the "Sample Questions" button for ideas
- **View Sources**: See which policies were used to answer your questions
- **Export Chat**: Save conversation history for reference

### 3. Upload Policies Tab
- **Select PDF**: Choose a policy document to upload
- **Assign Building/Agent**: Link the policy to a specific building and agent
- **Automatic Parsing**: The system extracts key information automatically
- **Review & Save**: Verify extracted data before saving

### 4. Alerts & Notifications Tab
- **System Status**: Check email configuration and alert system health
- **Test Emails**: Send test emails to verify configuration
- **Manual Checks**: Trigger policy expiration checks manually
- **Configuration Help**: View setup instructions and troubleshooting tips

## 🏗️ Project Structure

```
Insurance-Master/
├── src/                          # Source code
│   ├── main.py                   # Main application entry point
│   ├── ui/                       # User interface components
│   │   ├── policy_table.py       # Main policy table widget
│   │   ├── dialogs.py            # Dialog windows
│   │   └── chat_panel.py         # Q&A chat interface
│   ├── db/                       # Database operations
│   │   └── database.py           # SQLite database management
│   ├── parsing/                  # PDF parsing utilities
│   │   └── pdf_parser.py         # PDF text extraction
│   ├── rag/                      # RAG system for Q&A
│   │   └── rag_system.py         # OpenAI integration & vector search
│   └── alerts/                   # Email alert system
│       └── email_alerts.py       # SMTP email notifications
├── data/                         # Data storage
│   ├── policies/                 # Policy PDF storage
│   ├── insurance.db              # SQLite database
│   └── chroma_db/                # Vector database for RAG
├── requirements.txt               # Python dependencies
├── env.example                   # Environment configuration template
├── run.py                        # Application launcher
└── README.md                     # This file
```

## 🔧 Configuration

### Database
- SQLite database is automatically created in `data/insurance.db`
- Initial data includes 8 sample agents and 27 sample buildings
- Policies are randomly assigned to agents on first run

### PDF Parsing
- Supports both PyPDF2 and pdfplumber for maximum compatibility
- Automatically extracts: carrier, policy number, dates, premium, coverage
- Validates extraction quality and provides confidence scores

### RAG System
- Uses ChromaDB for local vector storage
- OpenAI GPT-3.5-turbo for answer generation
- Configurable chunk size and overlap for text processing

### Email Alerts
- Daily checks for expiring policies (9:00 AM)
- Configurable thresholds (default: 60 and 30 days)
- SMTP support for Gmail, Outlook, and other providers

## 🐛 Troubleshooting

### Common Issues

**1. OpenAI API Errors**
```
Error: OPENAI_API_KEY not found in environment variables
```
- Ensure `.env` file exists and contains your API key
- Verify the API key is valid and has sufficient credits

**2. Email Configuration Issues**
```
Warning: Email configuration incomplete. Alerts will not be sent.
```
- Check all required email variables in `.env`
- For Gmail, use App Password, not regular password
- Verify SMTP settings and port numbers

**3. PDF Parsing Failures**
```
Error: Could not extract text from PDF
```
- Ensure PDF is not password-protected
- Try with different PDF formats
- Check if PDF contains actual text (not just images)

**4. Database Errors**
```
Error: Failed to initialize database
```
- Check file permissions for `data/` directory
- Ensure SQLite is available in your Python environment
- Verify disk space availability

### Performance Tips

- **Large PDFs**: Break into smaller documents for better parsing
- **Vector Database**: ChromaDB files are stored in `data/chroma_db/`
- **Memory Usage**: Application uses ~200-500MB RAM depending on data size
- **Startup Time**: First run may take longer due to database initialization

## 📦 Building Executable

### Windows (.exe)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Insurance Master" src/main.py
```

### macOS (.app)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Insurance Master" src/main.py
```

### Linux
```bash
pip install pyinstaller
pyinstaller --onefile --name "insurance-master" src/main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the error logs in the console
3. Ensure all dependencies are properly installed
4. Verify environment configuration

## 🔄 Updates

- **v1.0**: Initial release with core functionality
- Future versions will include:
  - Enhanced PDF parsing
  - Additional export formats
  - Advanced reporting features
  - Mobile-friendly interface

---

**Insurance Master** - Making insurance policy management simple and intelligent.
