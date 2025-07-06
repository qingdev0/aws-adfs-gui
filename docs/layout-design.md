# AWS ADFS GUI Layout Design

This document describes the layout design for the AWS ADFS GUI application.

## Main Layout Structure

```html
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header │
├─────────────────────────────────────────────────────────────────────────────┤
│ Left Panel │ Center Panel │ Right Panel │ │ (Profiles) │ (Input/History) │
(Results/Tabs) │ │ │ │ │ │ ┌───────────┐ │ ┌─────────────────────────────┐ │
┌───────────────┐ │ │ │ Profile │ │ │ Command Input │ │ │ Result Tabs │ │ │ │
Groups: │ │ │ ┌─────────────────────────┐ │ │ │ ┌───────────┐ │ │ │ │ │ │ │ │
aws s3 ls │ │ │ │ │ Profile 1 │ │ │ │ │ ☐ Dev │ │ │ └─────────────────────────┘
│ │ │ │ Profile 2 │ │ │ │ │ ☐ Non-Prod│ │ │ │ │ │ │ Profile 3 │ │ │ │ │ ☐ Prod │
│ │ [Execute] [Clear] │ │ │ └───────────┘ │ │ │ │ │ │ │ │ │ │ │ │ │ │ History: │
│ │ Command History: │ │ │ Result Area: │ │ │ │ ┌───────┐ │ │ │
┌─────────────────────────┐ │ │ │ ┌───────────┐ │ │ │ │ │ Last │ │ │ │ │ aws s3
ls │ │ │ │ │ Command │ │ │ │ │ │ 10 │ │ │ │ │ aws ec2 describe-inst │ │ │ │ │
Output │ │ │ │ │ │ cmds │ │ │ │ │ aws iam list-users │ │ │ │ │ Here │ │ │ │ │
└───────┘ │ │ │ └─────────────────────────┘ │ │ │ └───────────┘ │ │ │
└───────────┘ │ └─────────────────────────────┘ │ └───────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Panel Descriptions

### Left Panel (Profile Selection)

- **Profile Groups**: Checkboxes for Dev, Non-Production, Production
- **Individual Profiles**: Expandable groups showing specific AWS profiles
- **Command History**: Last 10 executed commands for quick re-execution

### Center Panel (Command Input)

- **Command Input Field**: Text area for entering AWS CLI commands
- **Action Buttons**: Execute, Clear, and other command actions
- **Command History**: Scrollable list of previous commands

### Right Panel (Results Display)

- **Result Tabs**: One tab per selected profile showing execution results
- **Result Area**: Command output, errors, and execution status
- **Export Options**: Buttons to export results in different formats

## Responsive Design

The layout adapts to different screen sizes:

- **Desktop**: Three-column layout as shown above
- **Tablet**: Two-column layout (left panel collapses to dropdown)
- **Mobile**: Single column with expandable sections

## Color Scheme

- **Primary**: Blue (#007bff) for buttons and active elements
- **Secondary**: Gray (#6c757d) for secondary text and borders
- **Success**: Green (#28a745) for successful operations
- **Warning**: Yellow (#ffc107) for warnings
- **Error**: Red (#dc3545) for errors and failures
- **Background**: Light gray (#f8f9fa) for main background
