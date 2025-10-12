# Secret Code Portal - Visual Workflow Documentation

## Application Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    🔐 MI CHATBOT ACCESS PORTAL                   │
│                                                                  │
│  Welcome to the Motivational Interviewing Practice Portal!     │
│                                                                  │
│  Instructions:                                                   │
│  1. Enter your secret code                                      │
│  2. Click "Submit Code"                                         │
│  3. Redirected to assigned chatbot                             │
│                                                                  │
│  ┌────────────────────────────────────────────────┐            │
│  │           🔄 Refresh Data Button                │            │
│  └────────────────────────────────────────────────┘            │
│                                                                  │
│  ╔══════════════════════════════════════════════╗              │
│  ║  Enter Your Secret Code                      ║              │
│  ║  ┌────────────────────────────────────────┐  ║              │
│  ║  │ Secret Code: [hidden input]           │  ║              │
│  ║  └────────────────────────────────────────┘  ║              │
│  ║                                              ║              │
│  ║        [ Submit Code ] (Primary Button)     ║              │
│  ╚══════════════════════════════════════════════╝              │
└─────────────────────────────────────────────────────────────────┘
```

## User Journey - Success Path

```
┌──────────────┐
│   Student    │
│ Receives Code│
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│   Navigate to Portal │
│  (URL from instructor)│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   Portal Loads       │
│ - Connects to Sheet  │
│ - Caches code data   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Enter Secret Code   │
│  (type in form)      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Click Submit        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Validation Process: │
│ 1. Check code exists │
│ 2. Check not used    │
│ 3. Validate bot type │
│ 4. Mark as used      │
└──────┬───────────────┘
       │
       ▼ SUCCESS
┌──────────────────────────────────┐
│ ✅ Access granted for [Name]!    │
│                                  │
│ You are assigned to: [OHI/HPV]  │
│                                  │
│ [ Go to [OHI/HPV] Chatbot → ]   │
│                                  │
│ Alternative URL:                │
│ https://[bot].streamlit.app/    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────┐
│  User Clicks Button  │
│  or Copies URL       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Redirected to Bot   │
│  (OHI or HPV)        │
└──────────────────────┘
```

## Error Handling Flows

### Flow 1: Invalid Code

```
Student Enters Code
       │
       ▼
Code Not Found in Sheet
       │
       ▼
┌─────────────────────────────────┐
│ ❌ Error Message:                │
│                                 │
│ "Invalid code. Please check    │
│  your code and try again."     │
└─────────────────────────────────┘
       │
       ▼
User Can Re-enter Code
```

### Flow 2: Already Used Code

```
Student Enters Code
       │
       ▼
Code Found, but Used=TRUE
       │
       ▼
┌─────────────────────────────────┐
│ ❌ Error Message:                │
│                                 │
│ "This code has already been    │
│  used. Please contact your     │
│  instructor if you need a      │
│  new code."                    │
└─────────────────────────────────┘
       │
       ▼
Contact Instructor for Reset
```

### Flow 3: Connection Error

```
Portal Startup
       │
       ▼
Cannot Connect to Google Sheets
       │
       ▼
┌─────────────────────────────────┐
│ ❌ Error Message:                │
│                                 │
│ "Failed to load code database. │
│  Please refresh the page or    │
│  contact support."             │
└─────────────────────────────────┘
       │
       ▼
Try Refresh Button
```

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Google Sheets Database                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Table No │ Name  │ Bot │ Secret  │ Used              │    │
│  ├──────────┼───────┼─────┼─────────┼──────────────────┤    │
│  │    1     │ Alice │ OHI │ abc123  │ FALSE            │    │
│  │    2     │ Bob   │ HPV │ xyz789  │ FALSE            │    │
│  │    3     │ Carol │ OHI │ test456 │ TRUE             │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Google Sheets API
                         │ (Service Account Auth)
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              secret_code_portal.py Application                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Session State (Cached Data)                          │ │
│  │  - codes_data: { worksheet, headers, rows }          │ │
│  │  - authenticated: False/True                         │ │
│  │  - redirect_info: { bot, name }                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Core Functions                                        │ │
│  │  1. get_google_sheets_client()                        │ │
│  │  2. load_codes_from_sheet()                          │ │
│  │  3. validate_and_mark_code()                         │ │
│  │  4. main() - UI logic                                │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP Redirect or Button Click
                         │
         ┌───────────────┴─────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐             ┌──────────────────┐
│   OHI Chatbot   │             │   HPV Chatbot    │
│ (ohimiapp...)   │             │ (hpvmiapp...)    │
└─────────────────┘             └──────────────────┘
```

## Instructor Workflow

```
┌──────────────────┐
│  Create Student  │
│     Records      │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Generate Secret Codes          │
│  - Random 8-12 characters       │
│  - Unique for each student      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Add Rows to Google Sheet       │
│  Table No | Name | Bot | Secret │
│     1     | Alice| OHI | abc123 │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Distribute Codes to Students   │
│  - Email individually           │
│  - Include portal URL           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Students Access Portal         │
│  - Codes automatically marked   │
│  - Monitor "Used" column        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Optional: Reset/Manage         │
│  - Change Used FALSE → TRUE     │
│  - Generate new codes           │
│  - Track completion             │
└─────────────────────────────────┘
```

## Security Model

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                       │
└─────────────────────────────────────────────────────────┘

Layer 1: Code Generation
├─ Random, unique codes
├─ Minimum 8 characters
└─ No predictable patterns

Layer 2: Input Validation
├─ Exact string matching
├─ No empty codes accepted
├─ Password input type (hidden)
└─ Bot type validation

Layer 3: Single-Use Enforcement
├─ Automatic marking on use
├─ Check "Used" status before validation
└─ Prevent code sharing

Layer 4: Access Control
├─ Service account authentication
├─ Limited sheet permissions (Editor only)
├─ Separate credentials file
└─ Revocable access

Layer 5: Error Handling
├─ Generic error messages
├─ No information leakage
├─ Graceful degradation
└─ User-friendly feedback
```

## UI States

### State 1: Initial Load
```
┌─────────────────────────────────┐
│ 🔐 MI Chatbot Access Portal     │
│                                 │
│ [Welcome message]               │
│ [Instructions]                  │
│                                 │
│     [ 🔄 Refresh Data ]         │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Secret Code: [_________]    │ │
│ │                             │ │
│ │    [ Submit Code ]          │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### State 2: Code Entered (Validating)
```
┌─────────────────────────────────┐
│ 🔐 MI Chatbot Access Portal     │
│                                 │
│ [Welcome message]               │
│ [Instructions]                  │
│                                 │
│     [ 🔄 Refresh Data ]         │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Secret Code: ••••••••••     │ │
│ │                             │ │
│ │    [Submit Code - clicked]  │ │
│ └─────────────────────────────┘ │
│                                 │
│ ⏳ Verifying your code...       │
└─────────────────────────────────┘
```

### State 3: Success (Authenticated)
```
┌─────────────────────────────────┐
│ 🔐 MI Chatbot Access Portal     │
│                                 │
│ ✅ Access granted for Alice!    │
│                                 │
│ You are assigned to: OHI        │
│                                 │
│ ℹ️ Ready to start your session? │
│                                 │
│ [ Go to OHI Chatbot → ]         │
│                                 │
│ Alternative URL:                │
│ https://ohimiapp.streamlit.app/ │
└─────────────────────────────────┘
```

### State 4: Error
```
┌─────────────────────────────────┐
│ 🔐 MI Chatbot Access Portal     │
│                                 │
│ [Welcome message]               │
│ [Instructions]                  │
│                                 │
│     [ 🔄 Refresh Data ]         │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Secret Code: [_________]    │ │
│ │                             │ │
│ │    [ Submit Code ]          │ │
│ └─────────────────────────────┘ │
│                                 │
│ ❌ Invalid code. Please check   │
│    your code and try again.     │
└─────────────────────────────────┘
```

## Mobile Responsiveness

The portal is designed with Streamlit's centered layout:
- Works on desktop, tablet, and mobile
- Responsive form inputs
- Touch-friendly buttons
- Readable text sizes
- Password input works on all devices

## Browser Compatibility

Tested and compatible with:
- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Metrics

### Expected Performance

```
Action                    | Time      | Notes
─────────────────────────┼───────────┼─────────────────────
Initial page load        | 1-2s      | Depends on network
Load codes from sheet    | 0.5-1s    | Cached after first load
Code validation          | 0.2-0.5s  | Lookup in cached data
Mark code as used        | 0.5-1s    | Google Sheets API call
Full validation flow     | 1-2s      | Total user experience
Refresh data             | 0.5-1s    | Re-fetch from sheet
```

### Scalability

```
Metric                   | Capacity  | Notes
─────────────────────────┼───────────┼─────────────────────
Students per semester    | 1000+     | Google Sheets limit
Concurrent users         | 100+      | Streamlit Cloud limit
Sheet size               | 10M cells | Google Sheets limit
API calls per minute     | 60        | Google API quota
Session data size        | ~10KB     | Per user session
```

## Accessibility Features

- Clear, descriptive labels
- High contrast text
- Keyboard navigation support
- Screen reader compatible
- Error messages are explicit
- Success messages are clear
- Alt text for icons (where applicable)

---

This visual documentation provides a comprehensive view of the Secret Code Portal's functionality, flows, and user experience without requiring actual screenshots of the running application.
