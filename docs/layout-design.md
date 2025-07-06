# AWS ADFS GUI - Modern Layout Design

## Current vs Proposed Layout

### Proposed Modern Layout:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🌩️ AWS ADFS GUI                                              ⚙️ Settings │ Status: ● │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Command: [aws s3 ls                                    ] [▶️ Execute] [📋 History] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ ┌─ Dev Profiles ────────────────┐ ┌─ Profile Tabs ─────────────────────────────────┐ │
│ │ [🟢 aws-dev-eu    ] Connected │ │ [aws-dev-eu] [aws-dev-sg] [+]                  │ │
│ │ [🟢 aws-dev-sg    ] Connected │ │                                                │ │
│ │ [Select Dev] (highlighted)     │ │ ┌─ aws-dev-eu Results ─────────────────────────┐ │
│ └───────────────────────────────┘ │ │ $ aws s3 ls                                  │ │
│                                   │ │ 2024-01-15 10:30:00 bucket1                 │ │
│ ┌─ Other Profiles ──────────────┐ │ │ 2024-01-15 10:30:00 bucket2                 │ │
│ │ ☐ kds-ets-np                  │ │ │ 2024-01-15 10:30:00 bucket3                 │ │
│ │ ☐ kds-gps-np                  │ │ │                                              │ │
│ │ ☐ kds-iss-np                  │ │ │ Duration: 1.23s ✅ Success                   │ │
│ │ ☐ kds-ets-pd                  │ │ └──────────────────────────────────────────────┘ │
│ │ ☐ kds-gps-pd                  │ └─────────────────────────────────────────────────┘ │
│ │ ☐ kds-iss-pd                  │                                                     │
│ └───────────────────────────────┘                                                     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Connection Status Indicators:

- 🔴 **Red/Gray**: Disconnected
- 🟡 **Yellow**: Connecting...
- 🟢 **Green**: Connected

## Key Features:

### 1. Top Command Bar

- Single line command input at the top
- Execute button with play icon
- History button for quick access
- Settings gear icon (opens modal/page)

### 2. Left Panel - Profile Management

- **Dev Profiles Section**:
  - "Select Dev" button that highlights when active
  - Individual dev profiles with connection status
  - Auto-connect when "Select Dev" is clicked
- **Other Profiles Section**:
  - Individual checkboxes for manual selection
  - Connection status for each

### 3. Right Panel - Tabbed Results

- Dynamic tabs created when profiles connect
- Each tab shows profile name
- Real-time command output
- Success/error indicators
- Execution time display

### 4. Connection Flow

1. User clicks "Select Dev"
2. Button highlights (stays highlighted)
3. Connection initiated to aws-dev-eu and aws-dev-sg
4. Status changes: Gray → Yellow → Green
5. Tabs automatically created for connected profiles
6. Ready for command execution

### 5. Settings Modal

- Timeout configuration
- Export format selection
- Advanced options
- Profile management (add/remove)

## Technical Implementation:

- WebSocket for real-time connection status
- Dynamic tab creation
- Persistent button states
- Modern CSS with animations
- Responsive design
