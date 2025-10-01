"""
Sheets Update:
    - create 'Internship Tracker - Summer 2026'
    - insert new submitted applications
    - sort rows by status
    - within each statis, sort by date
"""
import os
import re
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

CREDS_PATH = "src/config/sheets_service.json"

SPREADSHEET_NAME = "Internship Tracker - Summer 2026"

HEADERS = [
    "Company",
    "Position",
    "Status",
    "Location",
    "Date Received",
    "Candidate Portal URL",
    "Compensation",
    "Notes",
]

STATUS_ORDER = {"Accepted": 1, "In Progress": 2, "Submitted": 3, "Rejected": 4}

def get_service():
    # connect to sheets api
    creds = Credentials.from_service_account_file(
        CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)


SPREADSHEET_ID = "1kBsUCDGPFvVL0tCnJqjAHLdc_H-5utkMCP7FeYhAeGc"

def format_date(date_str):
    """Convert email date to MM-DD-YYYY format."""
    if not date_str:
        return ""
    
    try:
        # Handle different email date formats
        if re.search(r'[+-]\d{4}', date_str):
            # Full email timestamp: "Wed, 3 Sep 2025 14:30:29 +0000" or "Thu, 11 Sep 2025 18:55:03 +0000 (UTC)"
            # Remove timezone info: everything after +/- timezone
            clean_date = re.sub(r'\s*[+-]\d{4}.*$', '', date_str).strip()
            dt = datetime.strptime(clean_date, "%a, %d %b %Y %H:%M:%S")
        elif any(tz in date_str.upper() for tz in ["GMT", "EDT", "EST", "UTC", "PST", "CST", "PDT"]):
            # Handle timezone abbreviations without +/- offset
            clean_date = re.sub(r'\s*\([A-Z]{3,4}\).*$', '', date_str).strip()  
            dt = datetime.strptime(clean_date, "%a, %d %b %Y %H:%M:%S")
        elif re.match(r'\w{3}, \d{1,2} \w{3} \d{4} \d{2}:\d{2}:\d{2}', date_str):
            # Standard email format without timezone: "Wed, 3 Sep 2025 14:30:29"
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
        elif "-" in date_str and ":" in date_str:
            # Parse format: "2025-09-12 21:32:56"
            dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        elif "-" in date_str and len(date_str) == 10:
            # Parse format: "2025-01-01" or "09-12-2025"
            if date_str.startswith('20'):
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return date_str  # Already in MM-DD-YYYY format
        else:
            return date_str  # Return as-is if can't parse
            
        return dt.strftime("%m-%d-%Y")
    except Exception as e:
        print(f"[DEBUG] Could not parse date '{date_str}': {e}")
        return date_str  # Return original if parsing fails

def setup_sheet_formatting(service, spreadsheet_id):
    """Set up headers, formatting, column widths, and data validation."""
    requests = []
    
    # Set headers (now includes Candidate Portal URL)
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A1:H1",
        valueInputOption="RAW",
        body={"values": [HEADERS]}
    ).execute()
    
    # Bold and freeze header row
    requests.extend([
        {
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold"
            }
        },
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "gridProperties": {"frozenRowCount": 1}
                },
                "fields": "gridProperties.frozenRowCount"
            }
        }
    ])
    
    # Set column widths (Company:200, Position:200, Status:120, Location:150, Date:120, Portal URL:180, Compensation:120, Notes:250)
    column_widths = [200, 200, 120, 150, 120, 180, 120, 250]
    for i, width in enumerate(column_widths):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": i,
                    "endIndex": i + 1
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })
    
    # Add status dropdown validation (column C = index 2)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 1,  # Start from row 2 (after headers)
                "startColumnIndex": 2,  # Status column
                "endColumnIndex": 3
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "Accepted"},
                        {"userEnteredValue": "In Progress"}, 
                        {"userEnteredValue": "Submitted"},
                        {"userEnteredValue": "Rejected"}
                    ]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    })
    
    # Dark grey background with white text for header row
    requests.append({
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.3, "green": 0.3, "blue": 0.3},
                    "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}
                }
            },
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.foregroundColor"
        }
    })

    # Add conditional formatting for status colors and placeholder text
    # Status colors: Submitted = light green, In Progress = light yellow, Rejected = light red, Accepted = light blue
    # Placeholder text: "[Please Enter]" = grey italic
    conditional_formatting_requests = [
        # Placeholder text formatting for all columns except Status
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [
                        {"sheetId": 0, "startRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 2},  # Company, Position
                        {"sheetId": 0, "startRowIndex": 1, "startColumnIndex": 3, "endColumnIndex": 8}   # Location through Notes
                    ],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "[Please Enter]"}]},
                        "format": {
                            "textFormat": {
                                "foregroundColor": {"red": 0.6, "green": 0.6, "blue": 0.6},
                                "italic": True
                            }
                        }
                    }
                },
                "index": 0
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 0, "startRowIndex": 1, "startColumnIndex": 2, "endColumnIndex": 3}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Submitted"}]},
                        "format": {"backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.85}}
                    }
                },
                "index": 1
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 0, "startRowIndex": 1, "startColumnIndex": 2, "endColumnIndex": 3}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "In Progress"}]},
                        "format": {"backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.8}}
                    }
                },
                "index": 2
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 0, "startRowIndex": 1, "startColumnIndex": 2, "endColumnIndex": 3}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Rejected"}]},
                        "format": {"backgroundColor": {"red": 0.95, "green": 0.8, "blue": 0.8}}
                    }
                },
                "index": 3
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 0, "startRowIndex": 1, "startColumnIndex": 2, "endColumnIndex": 3}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Accepted"}]},
                        "format": {"backgroundColor": {"red": 0.8, "green": 0.9, "blue": 1.0}}
                    }
                },
                "index": 4
            }
        }
    ]

    # Execute all formatting requests
    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

    # Execute conditional formatting separately
    if conditional_formatting_requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": conditional_formatting_requests}
        ).execute()

def get_or_create_sheet(service):
    """Get existing sheet and set up formatting."""
    setup_sheet_formatting(service, SPREADSHEET_ID)
    return SPREADSHEET_ID


def append_rows(service, spreadsheet_id, rows):
    # insert new rows under headers
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()

def apply_sort(service, spreadsheet_id):
    """Sort by Status priority, then by Date Received (newest first)."""
    requests = [
        {
            "sortRange": {
                "range": {"sheetId": 0, "startRowIndex": 1},  # Skip header row
                "sortSpecs": [
                    {"dimensionIndex": 3, "sortOrder": "ASCENDING"},   # Status column (D)
                    {"dimensionIndex": 4, "sortOrder": "DESCENDING"},  # Date Received column (E), newest first
                ]
            }
        }
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()

def reapply_status_validation(service, spreadsheet_id):
    # get current data to determine range
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A:A"
    ).execute()
    values = result.get('values', [])
    last_row = len(values)
    
    if last_row <= 1:  # only headers or empty sheet
        return
    
    # apply dropdown validation to status column (column D) for all data rows
    request = {
        "setDataValidation": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 1,  # start from row 2 (after headers)
                "endRowIndex": last_row,  # through last row with data
                "startColumnIndex": 2,  # status column (C)
                "endColumnIndex": 3
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "Accepted"},
                        {"userEnteredValue": "In Progress"}, 
                        {"userEnteredValue": "Submitted"},
                        {"userEnteredValue": "Rejected"}
                    ]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    }
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [request]}
    ).execute()


def update_sheet(new_apps):
    service = get_service()
    spreadsheet_id = get_or_create_sheet(service)
    rows = []
    for app in new_apps:
        # New column order: Company, Position, Status, Location, Date Received, Candidate Portal URL, Compensation, Notes
        rows.append(
            [
                app.get("company", "") or "[Please Enter]",
                app.get("position", "") or "[Please Enter]",
                "Submitted",  # status (default)
                app.get("location", "") or "[Please Enter]",  # location (AI extracted, can be manually edited)
                format_date(app.get("date", "")) or "[Please Enter]",  # date received (formatted)
                app.get("candidate_portal_url", "") or "[Please Enter]",  # candidate portal URL (AI extracted)
                "[Please Enter]",  # compensation (manual)
                "[Please Enter]",  # notes (manual)
            ]
        )

    append_rows(service, spreadsheet_id, rows)
    
    # reapply dropdown validation after data insertion (fixes validation override issue)
    reapply_status_validation(service, spreadsheet_id)
    
    apply_sort(service, spreadsheet_id)
    print(f"[INFO] added {len(rows)} rows and applied sort")

if __name__ == "__main__":
    # Test with dummy data
    test_apps = [{"date": "2025-01-01", "company": "Test Co", "position": "Test Role", "candidate_portal_url": "https://example.com/portal"}]
    update_sheet(test_apps)





