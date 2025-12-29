# DevOps Productivity Suite Integration Plan

## Overview

This document outlines the integration of the DevOps Productivity Suite business automation features into the Power Benchmarking Suite. The goal is to add client management, email automation, lead capture, and business workflow capabilities to the power benchmarking project.

## Integration Strategy

### Phase 1: Core Business Automation (Python Implementation)
- **Client Management**: Python API for client CRUD operations
- **Email Service**: Python wrapper for Resend API
- **Document Generation**: PDF generation for reports and invoices
- **Workflow Automation**: Python-based workflow triggers

### Phase 2: Marketing & Lead Capture
- **Lead Capture API**: Form submission handling
- **Email Sequences**: Automated email campaigns
- **Presentation Tools**: Interactive presentation generation
- **Landing Page**: Marketing landing page integration

### Phase 3: Advanced Features
- **HubSpot Integration**: CRM synchronization
- **Support Tickets**: Ticket management system
- **Onboarding Automation**: Client onboarding workflows
- **Monthly Check-ins**: Automated check-in reminders

## Architecture

### New Directory Structure

```
power-benchmarking-week2/
├── power_benchmarking_suite/
│   ├── business/              # NEW: Business automation features
│   │   ├── __init__.py
│   │   ├── clients.py         # Client management
│   │   ├── invoices.py        # Invoice generation
│   │   ├── checkins.py        # Monthly check-ins
│   │   ├── onboarding.py      # Onboarding workflows
│   │   └── workflows.py       # Workflow automation
│   ├── marketing/             # NEW: Marketing features
│   │   ├── __init__.py
│   │   ├── lead_capture.py    # Lead capture API
│   │   ├── email_service.py   # Email automation
│   │   ├── email_templates.py # Email templates
│   │   └── presentations.py   # Presentation generation
│   ├── services/              # NEW: Shared services
│   │   ├── __init__.py
│   │   ├── storage.py         # Data storage (JSON/DB)
│   │   ├── pdf_generator.py   # PDF generation
│   │   └── document_generator.py # Document generation
│   └── commands/              # Extend existing commands
│       ├── business.py        # NEW: Business automation CLI
│       └── marketing.py       # NEW: Marketing CLI
├── scripts/
│   └── devops/                # NEW: DevOps suite scripts
│       ├── generate_pdf.py
│       └── email_test.py
└── docs/
    └── DEVOPS_INTEGRATION_PLAN.md  # This file
```

## Implementation Details

### 1. Client Management (`business/clients.py`)

**Features:**
- CRUD operations for clients
- Client status tracking (prospect, active, inactive)
- Email-based client lookup
- JSON-based storage (can upgrade to database later)

**CLI Commands:**
```bash
power-benchmark business clients list
power-benchmark business clients get --email client@example.com
power-benchmark business clients create --name "Client Name" --email client@example.com
power-benchmark business clients update --id xxx --status active
power-benchmark business clients delete --id xxx
```

### 2. Email Service (`marketing/email_service.py`)

**Features:**
- Resend API integration
- Email template system
- Scheduled email queue
- Email preferences management

**Dependencies:**
- `resend` Python SDK (or direct API calls)
- Template engine (Jinja2)

**CLI Commands:**
```bash
power-benchmark marketing email send --to client@example.com --template welcome
power-benchmark marketing email preview --template welcome
power-benchmark marketing email queue --list
```

### 3. Lead Capture (`marketing/lead_capture.py`)

**Features:**
- Form submission handling
- Automatic client creation
- Email sequence triggering
- HubSpot webhook integration (optional)

**CLI Commands:**
```bash
power-benchmark marketing lead capture --name "Name" --email email@example.com
power-benchmark marketing lead capture --from-file leads.csv
```

### 4. Invoice Generation (`business/invoices.py`)

**Features:**
- PDF invoice generation
- Template-based invoices
- Client association
- Payment tracking

**CLI Commands:**
```bash
power-benchmark business invoices create --client-id xxx --amount 199.00
power-benchmark business invoices list
power-benchmark business invoices generate-pdf --id xxx
```

### 5. Workflow Automation (`business/workflows.py`)

**Features:**
- Automated check-in reminders
- Onboarding progress tracking
- Email sequence triggers
- Scheduled task execution

**CLI Commands:**
```bash
power-benchmark business workflows run-checkins
power-benchmark business workflows run-reminders
power-benchmark business workflows schedule --workflow checkins --cron "0 9 * * *"
```

## Data Storage

### Initial Implementation: JSON Files
- `data/clients.json` - Client data
- `data/invoices.json` - Invoice records
- `data/checkins.json` - Check-in history
- `data/email_queue.json` - Scheduled emails
- `data/onboarding.json` - Onboarding progress

### Future: Database Migration
- SQLite for local development
- PostgreSQL for production
- Migration scripts provided

## Configuration

### New Configuration Section

```yaml
# ~/.power_benchmarking/config.yaml
business:
  storage_path: ~/.power_benchmarking/data
  invoice_template: templates/invoice.html
  checkin_reminder_days: 30

marketing:
  email:
    provider: resend
    api_key: ${RESEND_API_KEY}
    from_email: onboarding@resend.dev
    from_name: Power Benchmarking Suite
  templates:
    welcome: templates/emails/welcome.html
    checkin: templates/emails/checkin.html
  hubspot:
    enabled: false
    api_key: ${HUBSPOT_API_KEY}
```

## Environment Variables

```bash
# Email Service
RESEND_API_KEY=re_xxxxxxxxxxxxx
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=Power Benchmarking Suite

# HubSpot (optional)
HUBSPOT_API_KEY=your-hubspot-api-key

# Security
PREVIEW_SECRET=your-secret-token-here
CRON_SECRET=your-cron-secret-here
```

## Integration with Power Benchmarking

### Use Cases

1. **Client Reporting**: Generate power analysis reports for clients
2. **Automated Follow-ups**: Send power optimization recommendations via email
3. **Lead Nurturing**: Capture leads interested in power optimization services
4. **Client Onboarding**: Automated onboarding for new power benchmarking clients
5. **Monthly Check-ins**: Automated reminders for client power reviews

### Example Workflow

```python
# Automated client power report
from power_benchmarking_suite.business import clients
from power_benchmarking_suite.marketing import email_service
from power_benchmarking_suite.services import pdf_generator

# 1. Get client
client = clients.get_client(email="client@example.com")

# 2. Run power analysis
# (existing power benchmarking code)

# 3. Generate PDF report
report_pdf = pdf_generator.generate_power_report(
    client_id=client['id'],
    power_data=csv_file,
    recommendations=analysis_results
)

# 4. Send email with report
email_service.send_email(
    to=client['email'],
    template='power_report',
    attachments=[report_pdf],
    context={'client_name': client['name']}
)

# 5. Schedule follow-up check-in
workflows.schedule_checkin(client_id=client['id'], days=30)
```

## Migration from TypeScript

### Key Differences

1. **Language**: TypeScript → Python
2. **Runtime**: Vercel Serverless → Python CLI/API
3. **Storage**: Vercel KV → JSON files / SQLite / PostgreSQL
4. **Email**: Resend SDK (TypeScript) → Resend SDK (Python) or direct API
5. **PDF Generation**: Puppeteer → ReportLab or WeasyPrint

### Porting Strategy

1. **API Endpoints** → CLI Commands + Python Functions
2. **TypeScript Services** → Python Modules
3. **Vercel Cron** → Python `schedule` library or system cron
4. **Serverless Functions** → Python scripts with CLI interface

## Dependencies

### New Python Packages

```txt
# Business automation
resend>=2.0.0              # Email service
reportlab>=4.0.0           # PDF generation
weasyprint>=60.0           # HTML to PDF (alternative)
jinja2>=3.1.0              # Template engine
schedule>=1.2.0            # Task scheduling

# Optional
psycopg2-binary>=2.9.0    # PostgreSQL (future)
sqlalchemy>=2.0.0         # Database ORM (future)
```

## Testing Strategy

1. **Unit Tests**: Test individual business logic functions
2. **Integration Tests**: Test CLI commands end-to-end
3. **Email Tests**: Test email sending with Resend test API
4. **PDF Tests**: Verify PDF generation output
5. **Workflow Tests**: Test automated workflows

## Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **Data Storage**: Encrypt sensitive client data
3. **Email Validation**: Validate email addresses before sending
4. **Rate Limiting**: Implement rate limits for email sending
5. **Access Control**: Add authentication for sensitive operations

## Timeline

### Phase 1 (Week 1): Core Infrastructure
- [ ] Client management module
- [ ] Email service integration
- [ ] Basic storage system
- [ ] CLI command structure

### Phase 2 (Week 2): Business Features
- [ ] Invoice generation
- [ ] Check-in automation
- [ ] Onboarding workflows
- [ ] PDF generation

### Phase 3 (Week 3): Marketing Features
- [ ] Lead capture
- [ ] Email templates
- [ ] Email sequences
- [ ] Presentation tools

### Phase 4 (Week 4): Integration & Polish
- [ ] Integration with power benchmarking workflows
- [ ] Documentation
- [ ] Testing
- [ ] Deployment guides

## Success Metrics

1. **Functionality**: All DevOps suite features available via CLI
2. **Integration**: Seamless integration with power benchmarking workflows
3. **Usability**: Clear CLI interface with helpful error messages
4. **Documentation**: Complete documentation for all features
5. **Testing**: >80% test coverage for business logic

## Next Steps

1. Review and approve this integration plan
2. Set up development environment with new dependencies
3. Create initial module structure
4. Implement Phase 1 features
5. Test and iterate


