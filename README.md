# 📧 Internship Tracker

Automatically detect and track internship/job application confirmations from Gmail and record them into Google Sheets.

## Overview

This tool uses a **pre-trained machine learning model** to classify emails as internship application confirmations and automatically exports them to a structured Google Sheet. No more manual tracking of where you've applied!

### Key Features

- 🤖 **Ready to use** - Pre-trained model works out of the box
- 📊 **Google Sheets integration** - Automatically creates and updates tracking spreadsheets
- 🔍 **Smart information extraction** - Uses LLM to extract company, position, and other details
- 🚫 **Duplicate prevention** - Avoids re-adding the same applications
- ✏️ **Preserves manual edits** - Leaves your notes and custom fields untouched
- 📅 **Season separation** - Organizes applications by internship year (Summer 2025, 2026, etc.)

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd InternshipTracker

# Install dependencies
pip install -r requirements.txt

# First-time setup (authentication only)
python run.py --setup
```

### 2. Regular Use

```bash
# Update your tracker with new applications
python run.py --update
```

That's it! The script will:
- Fetch new emails from Gmail
- Classify potential application confirmations using the pre-trained model
- Extract company and position information
- Update your Google Sheet with new applications

## Commands

| Command | Description |
|---------|-------------|
| `python run.py --setup` | First-time setup: authenticate Gmail/Sheets |
| `python run.py --update` | Regular update: fetch new emails, classify, and update Google Sheets |
| `python run.py --retrain` | Optional: retrain model with your own starred emails for better accuracy |
| `python run.py --help` | Show help and usage examples |

## How It Works

The tool uses a **pre-trained machine learning model** that's already been trained on thousands of internship application emails. The model looks at:

- **Email subject lines** - Keywords like "Application Received", "Thank you for applying"
- **Email body content** - Confirmation language and application details
- **Sender domains** - Company email patterns and recruiting platforms

### Data Flow
1. **Gmail API** fetches emails for the current application season
2. **Pre-trained ML model** classifies emails as "Submitted" vs "Not Submitted"
3. **LLM extraction** pulls company name, position, and other details
4. **Google Sheets API** updates your tracking spreadsheet
5. **Deduplication** prevents duplicate entries using message IDs

## Google Sheet Template

Your tracking sheet includes these columns:

| Column | Description | Filled By |
|--------|-------------|-----------|
| Date Received | Email timestamp | Automatic |
| Company | Organization name | AI extraction |
| Position | Job/internship title | AI extraction |
| Internship Year | Summer 2025, 2026, etc. | Automatic |
| Location | Office location | Manual |
| Compensation | Salary/stipend info | Manual |
| Status | Application status | Automatic (Submitted) |
| Notes | Your custom notes | Manual |

## Project Structure

```
InternshipTracker/
├── src/
│   ├── scraping/          # Gmail authentication & email fetching
│   │   ├── authenticate_gmail.py
│   │   ├── scrape_starred.py
│   │   ├── scrape_recent.py
│   │   └── generate_synthetic.py
│   ├── preprocessing/     # Text cleaning & dataset building
│   │   ├── clean_text.py
│   │   └── build_dataset.py
│   ├── prediction/        # Classification & Google Sheets updates
│   │   ├── predict.py
│   │   └── update_sheets.py
│   ├── ai_extraction/     # LLM-based information extraction
│   │   └── extract_info.py
│   ├── training/          # Model training & evaluation
│   │   ├── train.py
│   │   └── evaluate.py
│   └── config/            # Database utilities & configurations
│       └── db_utils.py
├── models/                # Pre-trained ML models (included)
│   ├── log_reg.pkl        # Logistic regression classifier
│   ├── tfidf_subject.pkl  # Subject line vectorizer
│   ├── tfidf_body.pkl     # Email body vectorizer
│   └── domain_encoder.pkl # Sender domain encoder
├── data/                  # Training/validation datasets
│   ├── train.csv
│   ├── val.csv
│   ├── test.csv
│   ├── raw/               # Raw email data
│   ├── processed/         # Cleaned datasets
│   └── datasets/          # Additional datasets
├── db/                    # SQLite database files
│   └── schema.sql         # Database schema
├── notebooks/             # Jupyter notebooks for analysis
│   ├── eda.ipynb          # Exploratory data analysis
│   └── model_prototyping.ipynb
├── tests/                 # Unit tests
│   ├── test_preprocessing.py
│   ├── test_scraping.py
│   └── test_training.py
├── run.py                 # Main CLI entry point
├── requirements.txt       # Python dependencies
├── CLAUDE.md              # Project instructions & goals
└── README.md              # This file
```

## Customization (Optional)

The pre-trained model works well for most users, but you can optionally improve accuracy for your specific email patterns:

### Method 1: Star your confirmations
1. Go through your Gmail and star past application confirmation emails
2. Run `python run.py --retrain` to create a personalized model
3. The model will learn your specific email patterns

### Method 2: Use as-is
- The pre-trained model already handles most common confirmation email patterns
- Works immediately without any training data

## Privacy & Security

This tool is designed with privacy in mind:

- **Local execution**: All processing happens on your machine
- **OAuth authentication**: Secure, token-based API access
- **No data sharing**: Your emails and applications stay private
- **Gitignored sensitive files**: Credentials and personal data excluded from version control

### Files Kept Private
- `.env` - Environment variables and API keys
- `data/` - Your personal email data
- `*.db` - Application databases
- `logs/` - Debug logs
- OAuth tokens and credentials

## Troubleshooting

### Common Issues

**Authentication errors**: Re-run setup to refresh OAuth tokens
```bash
python run.py --setup
```

**Low accuracy**: Optionally retrain with your starred emails
```bash
python run.py --retrain
```

**Google Sheets not updating**: Verify Sheets API permissions in Google Cloud Console

### Support
- Check existing issues in the repository
- Create a new issue with error details and logs
- Include your Python version and OS information

## License

This project is for personal use. See LICENSE file for details.

---

**Happy job hunting!** 🎯