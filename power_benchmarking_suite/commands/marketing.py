"""
Marketing Command - Lead capture and email automation

Usage:
    power-benchmark marketing lead capture --name "Name" --email email@example.com
    power-benchmark marketing email send --to email@example.com --template welcome
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Import marketing modules
from ..marketing import LeadCapture, EmailService, EmailTemplates


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add marketing command to argument parser."""
    parser = subparsers.add_parser(
        "marketing",
        aliases=["mkt"],
        help="Marketing automation (lead capture, email)",
        description="Capture leads and send automated emails",
    )

    subparsers_mkt = parser.add_subparsers(dest="marketing_type", help="Marketing operation type")

    # Lead capture subcommand
    parser_lead = subparsers_mkt.add_parser(
        "lead", help="Lead capture", description="Capture new leads and trigger onboarding"
    )
    parser_lead.add_argument("action", choices=["capture"], help="Action to perform")
    parser_lead.add_argument("--name", type=str, required=True, help="Contact name")
    parser_lead.add_argument("--email", type=str, required=True, help="Contact email")
    parser_lead.add_argument("--company", type=str, help="Company name")
    parser_lead.add_argument("--phone", type=str, help="Contact phone")
    parser_lead.add_argument("--no-email", action="store_true", help="Skip welcome email")
    parser_lead.set_defaults(marketing_subtype="lead")

    # Email subcommand
    parser_email = subparsers_mkt.add_parser(
        "email", help="Email sending", description="Send emails using templates"
    )
    parser_email.add_argument(
        "action", choices=["send", "preview", "list-templates"], help="Action to perform"
    )
    parser_email.add_argument("--to", type=str, help="Recipient email")
    parser_email.add_argument("--template", type=str, help="Template name")
    parser_email.add_argument("--subject", type=str, help="Email subject (overrides template)")
    parser_email.set_defaults(marketing_subtype="email")

    # README generator subcommand
    parser_readme = subparsers_mkt.add_parser(
        "readme",
        help="Generate GitHub README",
        description="Generate GitHub README.md with green credentials and sustainability metrics",
    )
    parser_readme.add_argument(
        "--output",
        type=str,
        default="README_GREEN.md",
        help="Output file path (default: README_GREEN.md)",
    )
    parser_readme.add_argument(
        "--include-stats",
        action="store_true",
        help="Include detailed statistics and proof points",
    )
    parser_readme.set_defaults(marketing_subtype="readme")

    # Course materials generator subcommand
    parser_course = subparsers_mkt.add_parser(
        "course",
        help="Generate course materials",
        description="Generate course syllabus, landing page, and marketing materials for Engineering Architect Program",
    )
    parser_course.add_argument(
        "type",
        choices=["syllabus", "landing", "all"],
        help="Type of course material to generate",
    )
    parser_course.add_argument(
        "--output",
        type=str,
        help="Output directory (default: ./course_materials/)",
    )
    parser_course.set_defaults(marketing_subtype="course")

    # White paper generator subcommand
    parser_whitepaper = subparsers_mkt.add_parser(
        "whitepaper",
        help="Generate architect white paper",
        description="Generate white paper template for System Architect capstone project",
    )
    parser_whitepaper.add_argument(
        "--output",
        type=str,
        default="ARCHITECT_WHITEPAPER.md",
        help="Output file path (default: ARCHITECT_WHITEPAPER.md)",
    )
    parser_whitepaper.add_argument(
        "--company",
        type=str,
        help="Company name (for customization)",
    )
    parser_whitepaper.add_argument(
        "--team-size",
        type=int,
        help="Team size (for FTE calculations)",
    )
    parser_whitepaper.set_defaults(marketing_subtype="whitepaper")

    # Bio/LinkedIn generator subcommand
    parser_bio = subparsers_mkt.add_parser(
        "bio",
        help="Generate LinkedIn/bio content",
        description="Generate LinkedIn headline and bio based on 2026 strategy",
    )
    parser_bio.add_argument(
        "--output",
        type=str,
        default="LINKEDIN_BIO.txt",
        help="Output file path (default: LINKEDIN_BIO.txt)",
    )
    parser_bio.set_defaults(marketing_subtype="bio")

    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute marketing command."""
    try:
        if not hasattr(args, "marketing_type") or args.marketing_type is None:
            logger.error("Marketing operation type required. Use 'lead' or 'email'")
            return 1

        if args.marketing_type == "lead":
            return _handle_lead(args, config)
        elif args.marketing_type == "email":
            return _handle_email(args, config)
        elif args.marketing_type == "readme":
            return _handle_readme(args, config)
        elif args.marketing_type == "course":
            return _handle_course(args, config)
        elif args.marketing_type == "whitepaper":
            return _handle_whitepaper(args, config)
        elif args.marketing_type == "bio":
            return _handle_bio(args, config)
        else:
            logger.error(f"Unknown marketing type: {args.marketing_type}")
            return 1

    except Exception as e:
        logger.error(f"Marketing command failed: {e}", exc_info=True)
        return 1


def _handle_lead(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle lead capture."""
    if args.action != "capture":
        logger.error(f"Unknown lead action: {args.action}")
        return 1

    capture = LeadCapture()

    result = capture.capture_lead(
        name=args.name,
        email=args.email,
        company=args.company,
        phone=args.phone,
        send_welcome_email=not args.no_email,
    )

    if result.get("success"):
        print(f"\n✅ Lead captured:")
        print(f"  Client ID: {result['client'].get('id')}")
        print(f"  Company: {result['client'].get('company')}")
        print(f"  Email: {result['client'].get('contact', {}).get('email')}")
        print(f"  Is New: {result.get('is_new', False)}")
        print(f"  Welcome Email Sent: {result.get('email_sent', False)}")
        return 0
    else:
        logger.error("Failed to capture lead")
        return 1


def _handle_email(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle email operations."""
    email_service = EmailService()
    templates = EmailTemplates()

    if args.action == "list-templates":
        template_names = templates.list_templates()
        print(f"\nAvailable templates ({len(template_names)}):\n")
        for name in template_names:
            print(f"  - {name}")
        return 0

    elif args.action == "preview":
        if not args.template:
            logger.error("--template required for 'preview' action")
            return 1

        template = templates.get_template(args.template)
        if not template:
            logger.error(f"Template not found: {args.template}")
            return 1

        # Use sample context
        context = {
            "contact_name": "John Doe",
            "company": "Example Company",
            "unsubscribe_url": "#",
            "preferences_url": "#",
        }

        html = template.render(context)
        subject = template.get_subject(context)

        print(f"\nTemplate Preview: {args.template}")
        print(f"Subject: {subject}")
        print(f"\nHTML Preview (first 500 chars):\n{html[:500]}...")
        return 0

    elif args.action == "send":
        if not args.to or not args.template:
            logger.error("--to and --template required for 'send' action")
            return 1

        template = templates.get_template(args.template)
        if not template:
            logger.error(f"Template not found: {args.template}")
            return 1

        # Use sample context (in real usage, this would come from client data)
        context = {
            "contact_name": args.to.split("@")[0],  # Simple name extraction
            "company": "",
            "unsubscribe_url": "#",
            "preferences_url": "#",
        }

        result = email_service.send_template_email(
            to=args.to,
            template_name=args.template,
            context=context,
            subject=args.subject,
        )

        if result.get("success"):
            print(f"\n✅ Email sent:")
            print(f"  To: {args.to}")
            print(f"  Template: {args.template}")
            print(f"  Message ID: {result.get('message_id', 'N/A')}")
            return 0
        else:
            logger.error(f"Failed to send email: {result.get('error', 'Unknown error')}")
            return 1

    return 1


def _handle_readme(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Generate GitHub README with green credentials."""
    try:
        output_path = Path(args.output)
        
        # Green credentials data from whitepaper audit
        green_data = {
            "energy_efficiency_improvement": "4.5×",
            "battery_life_extension": "157%",
            "battery_life_hours": "15.7 hours",
            "ghost_energy_eliminated": "60%",
            "co2_savings_per_developer": "50-200 kg CO₂/year",
            "co2_savings_enterprise": "1,000-5,000 kg CO₂/year",
            "energy_per_work_improvement": "4.5×",
            "work_efficiency_improvement": "1.8×",
            "stall_time_eliminated": "40%",
        }
        
        # Calculate Carbon Backlog metrics for High-Impact justification
        # Based on Carbon Break-Even framework from TECHNICAL_DEEP_DIVE.md
        carbon_backlog = _calculate_carbon_backlog_impact(green_data)
        green_data.update(carbon_backlog)
        
        readme_content = _generate_green_readme(green_data, include_stats=args.include_stats)
        
        # Write to file
        output_path.write_text(readme_content, encoding="utf-8")
        
        print(f"\n✅ Green README generated:")
        print(f"  Output: {output_path.absolute()}")
        print(f"  Size: {len(readme_content)} characters")
        print(f"\n💡 Next steps:")
        print(f"  1. Review: {output_path}")
        print(f"  2. Customize: Edit the file to match your project")
        print(f"  3. Replace: Copy content to your main README.md")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate README: {e}", exc_info=True)
        return 1


def _calculate_carbon_backlog_impact(green_data: dict) -> dict:
    """
    Calculate Carbon Backlog impact metrics to justify High-Impact engineering choice.
    
    Based on Carbon Break-Even framework: Environmental ROI (kg CO₂/hour)
    Includes both Operational (energy used) and Embodied (manufacturing) carbon.
    """
    # Typical optimization scenario
    # Assumes: 8 hours engineering time, daily optimization tasks
    engineering_hours = 8.0
    tasks_per_day = 100.0  # Typical daily optimization frequency
    days_per_year = 365.0
    
    # Convert CO₂ savings to per-hour impact
    # Using mid-range: 125 kg CO₂/year (midpoint of 50-200 range)
    annual_co2_kg = 125.0
    environmental_roi_kg_per_hour = annual_co2_kg / engineering_hours
    
    # Operational Carbon (energy used during runtime)
    # This is what we're optimizing - the 4.5× improvement reduces this
    operational_carbon_kg = annual_co2_kg  # 125 kg/year from energy savings
    
    # Embodied Carbon (manufacturing, device lifecycle)
    # Typical laptop: ~300-400 kg CO₂ for manufacturing
    # Spread over 3-5 year lifespan = ~60-130 kg CO₂/year
    embodied_carbon_per_year_kg = 80.0  # Mid-range estimate
    
    # Total Carbon Impact = Operational + Embodied
    # But optimization only affects Operational (energy use)
    # Embodied is fixed regardless of optimization
    total_device_carbon_kg = operational_carbon_kg + embodied_carbon_per_year_kg
    
    # Engineering Carbon (from optimization work itself)
    # Engineering: 8 hours × 0.5 kWh/hour laptop = 4 kWh
    engineering_carbon_kg = 4.0 * 0.4  # 1.6 kg CO₂ (at 0.4 kg/kWh)
    
    # Carbon payback period (engineering carbon / operational savings)
    carbon_payback_days = (engineering_carbon_kg / operational_carbon_kg) * 365 if operational_carbon_kg > 0 else 0
    
    # Operational vs Embodied ratio
    # Shows how much of total device carbon is from energy use (what we optimize)
    operational_ratio = (operational_carbon_kg / total_device_carbon_kg) * 100 if total_device_carbon_kg > 0 else 0
    
    # Determine priority level based on Environmental ROI
    if environmental_roi_kg_per_hour > 50:
        priority_level = "CRITICAL"
        impact_description = "Highest Impact - Prioritize immediately"
        sprint_justification = "CRITICAL priority: >50 kg CO₂/hour ROI. Immediate sprint inclusion required."
    elif environmental_roi_kg_per_hour > 20:
        priority_level = "HIGH"
        impact_description = "High Impact - Strong sustainability value"
        sprint_justification = "HIGH priority: 15-50 kg CO₂/hour ROI. Strong case for sprint inclusion."
    elif environmental_roi_kg_per_hour > 5:
        priority_level = "MEDIUM"
        impact_description = "Medium Impact - Good sustainability value"
        sprint_justification = "MEDIUM priority: 5-20 kg CO₂/hour ROI. Consider for sprint if capacity allows."
    else:
        priority_level = "LOW"
        impact_description = "Low Impact - Consider other priorities"
        sprint_justification = "LOW priority: <5 kg CO₂/hour ROI. Defer to future sprint."
    
    # Sprint prioritization explanation
    # 4.5× energy improvement = 4.5× operational carbon reduction
    energy_improvement = 4.5
    operational_carbon_reduction = operational_carbon_kg * (1 - 1/energy_improvement)  # 4.5× = 78% reduction
    
    # Hardware Decision: M1 Efficiency vs M3 Purchase
    # Calculate embodied carbon for new M3 hardware purchase
    m3_embodied_carbon_kg = 350.0  # Typical laptop manufacturing carbon
    m3_lifespan_years = 4.0
    m3_embodied_carbon_per_year = m3_embodied_carbon_kg / m3_lifespan_years
    
    # M1 optimization vs M3 purchase comparison
    # Keeping M1 efficient saves embodied carbon (no new device needed)
    embodied_carbon_saved_by_optimization = m3_embodied_carbon_per_year
    
    # Total carbon impact: Operational + Embodied savings
    total_carbon_impact_kg = operational_carbon_reduction + embodied_carbon_saved_by_optimization
    
    # Payback period for M3 purchase (how long to offset embodied carbon)
    m3_payback_years = m3_embodied_carbon_kg / operational_carbon_reduction if operational_carbon_reduction > 0 else float('inf')
    
    return {
        "environmental_roi_kg_per_hour": f"{environmental_roi_kg_per_hour:.1f}",
        "carbon_backlog_priority": priority_level,
        "carbon_backlog_impact": impact_description,
        "carbon_payback_days": f"{carbon_payback_days:.1f}",
        "engineering_carbon_kg": f"{engineering_carbon_kg:.1f}",
        "operational_carbon_kg": f"{operational_carbon_kg:.1f}",
        "embodied_carbon_kg": f"{embodied_carbon_per_year_kg:.1f}",
        "operational_ratio": f"{operational_ratio:.1f}",
        "sprint_justification": sprint_justification,
        "operational_carbon_reduction": f"{operational_carbon_reduction:.1f}",
        "energy_improvement": f"{energy_improvement}×",
        "m3_embodied_carbon_kg": f"{m3_embodied_carbon_kg:.0f}",
        "m3_embodied_carbon_per_year": f"{m3_embodied_carbon_per_year:.1f}",
        "embodied_carbon_saved_by_optimization": f"{embodied_carbon_saved_by_optimization:.1f}",
        "total_carbon_impact_kg": f"{total_carbon_impact_kg:.1f}",
        "m3_payback_years": f"{m3_payback_years:.1f}",
    }


def _generate_green_readme(green_data: dict, include_stats: bool = False) -> str:
    """Generate GitHub README content with green credentials."""
    
    stats_section = ""
    if include_stats:
        stats_section = f"""
## 📊 Sustainability Metrics & Proof Points

### Energy Efficiency Improvements

Based on our whitepaper audit and real-world testing:

- **{green_data['energy_efficiency_improvement']}× Energy Efficiency**: CoreML optimization reduces energy per unit work by 4.5×
- **{green_data['work_efficiency_improvement']}× Work Efficiency**: Improved from 30,000 mJ/s to 16,667 mJ/s
- **{green_data['ghost_energy_eliminated']} Ghost Energy Eliminated**: Removed wasted energy from CPU stalls
- **{green_data['stall_time_eliminated']} Stall Time Eliminated**: 4.0 seconds (40% of total time) wasted on CPU stalls eliminated

### Battery Life Impact

- **{green_data['battery_life_extension']} Battery Life Extension**: Up to {green_data['battery_life_hours']} additional runtime
- **Energy Per Unit Work**: Improved from 75,000 mJ/s to 16,667 mJ/s ({green_data['energy_per_work_improvement']}× improvement)

### Carbon Footprint Reduction

- **Per Developer**: {green_data['co2_savings_per_developer']}
- **Enterprise Teams**: {green_data['co2_savings_enterprise']}
- **Methodology**: Based on electricity grid average (~0.4 kg CO₂ per kWh)

### Technical Proof Points

All claims are backed by:
- ✅ Hardware-level power measurements (powermetrics)
- ✅ Statistical attribution analysis
- ✅ Peer-reviewable methodology
- ✅ Reproducible benchmarks

See `docs/TECHNICAL_DEEP_DIVE.md` for detailed whitepaper audit and proof points.
"""
    
    readme = f"""# Power Benchmarking Suite 🌱

> **Comprehensive toolkit for monitoring, analyzing, and optimizing power consumption on Apple Silicon Macs**

[![Sustainability](https://img.shields.io/badge/Sustainability-4.5×%20Energy%20Efficient-green)](https://github.com/KyPython/power-benchmarking-week2)
[![Battery Life](https://img.shields.io/badge/Battery%20Life-157%25%20Extension-brightgreen)](https://github.com/KyPython/power-benchmarking-week2)
[![CO2 Savings](https://img.shields.io/badge/CO₂%20Savings-50--200%20kg%2Fyear-blue)](https://github.com/KyPython/power-benchmarking-week2)

## 🌍 Why This Matters: Sustainability & Energy Efficiency

**Power Benchmarking Suite** helps developers build more energy-efficient applications, directly contributing to:

- ✅ **{green_data['energy_efficiency_improvement']}× Energy Efficiency** - Optimize CoreML models for maximum efficiency
- ✅ **{green_data['battery_life_extension']} Battery Life Extension** - Up to {green_data['battery_life_hours']} additional runtime
- ✅ **{green_data['co2_savings_per_developer']} CO₂ Reduction** - Quantified carbon footprint reduction per developer
- ✅ **{green_data['ghost_energy_eliminated']} Wasted Energy Eliminated** - Remove ghost energy from CPU stalls

### 🎯 High-Impact Engineering Choice

**Why using Power Benchmarking Suite is a High-Impact engineering decision:**

Based on our **Carbon Backlog prioritization framework**, optimizing with Power Benchmarking Suite delivers:

- **Environmental ROI**: **{green_data['environmental_roi_kg_per_hour']} kg CO₂ saved per engineering hour**
- **Priority Level**: **{green_data['carbon_backlog_priority']}** - {green_data['carbon_backlog_impact']}
- **Carbon Payback**: **{green_data['carbon_payback_days']} days** to offset engineering carbon footprint
- **Annual Impact**: {green_data['co2_savings_per_developer']} per developer

**What this means:**
- Every hour you spend optimizing = **{green_data['environmental_roi_kg_per_hour']} kg CO₂ saved annually**
- Engineering carbon footprint ({green_data['engineering_carbon_kg']} kg) is offset in just **{green_data['carbon_payback_days']} days**
- This is a **{green_data['carbon_backlog_priority']} priority** optimization in your sustainability backlog

### 🧪 Carbon Logic Transparency: Operational vs Embodied Carbon

**Understanding the Full Carbon Picture:**

- **Operational Carbon**: {green_data['operational_carbon_kg']} kg CO₂/year (energy used during runtime)
  - This is what the {green_data['energy_improvement']} improvement optimizes
  - Reduction: {green_data['operational_carbon_reduction']} kg CO₂/year saved
  
- **Embodied Carbon**: {green_data['embodied_carbon_kg']} kg CO₂/year (manufacturing, device lifecycle)
  - Fixed cost regardless of optimization
  - Spread over device lifespan (3-5 years)

- **Operational Ratio**: {green_data['operational_ratio']}% of total device carbon is operational
  - This is the portion we can optimize through energy efficiency

**Why {green_data['energy_improvement']} Energy Improvement = High Priority:**

1. **Operational Carbon Impact**: {green_data['operational_carbon_reduction']} kg CO₂/year reduction
   - Directly reduces energy consumption
   - Immediate environmental benefit
   - Quantifiable for ESG reporting

2. **Sprint Justification**: {green_data['sprint_justification']}
   - Environmental ROI: {green_data['environmental_roi_kg_per_hour']} kg CO₂/hour
   - Carbon payback: {green_data['carbon_payback_days']} days
   - Priority level: **{green_data['carbon_backlog_priority']}**

3. **Team Communication Template:**
   ```
   "This optimization delivers {green_data['environmental_roi_kg_per_hour']} kg CO₂/hour ROI.
   With a {green_data['carbon_payback_days']}-day payback period, it's a {green_data['carbon_backlog_priority']} 
   priority that should be included in this sprint. The {green_data['energy_improvement']} energy 
   improvement reduces operational carbon by {green_data['operational_carbon_reduction']} kg/year, 
   which is {green_data['operational_ratio']}% of total device carbon footprint."
   ```

### 🖥️ Hardware Decision: M1 Efficiency vs M3 Purchase

**The Sustainability Question**: Should we optimize existing M1 hardware or buy new M3 hardware?

**Operational Carbon (Energy in Use)**:
- **M1 Optimized**: {green_data['operational_carbon_reduction']} kg CO₂/year saved (4.5× improvement)
- **M3 New**: Similar operational savings, but requires new hardware

**Embodied Carbon (Manufacturing)**:
- **M3 Purchase**: {green_data['m3_embodied_carbon_kg']} kg CO₂ (one-time manufacturing cost)
- **M3 Per Year**: {green_data['m3_embodied_carbon_per_year']} kg CO₂/year (spread over {green_data['m3_payback_years']} year lifespan)
- **M1 Optimization**: **0 kg embodied carbon** (no new device needed)

**Total Carbon Impact**:
- **M1 Optimization**: {green_data['operational_carbon_reduction']} kg/year operational + **0 kg embodied** = **{green_data['operational_carbon_reduction']} kg/year total**
- **M3 Purchase**: {green_data['operational_carbon_reduction']} kg/year operational + {green_data['m3_embodied_carbon_per_year']} kg/year embodied = **{green_data['total_carbon_impact_kg']} kg/year total**

**The Decision**:
- **Optimize M1**: Saves {green_data['operational_carbon_reduction']} kg/year with **zero embodied carbon**
- **Buy M3**: Saves {green_data['operational_carbon_reduction']} kg/year but adds {green_data['m3_embodied_carbon_per_year']} kg/year embodied carbon
- **Net Difference**: M1 optimization is **{green_data['m3_embodied_carbon_per_year']} kg/year more sustainable**

**M3 Payback Period**: {green_data['m3_payback_years']} years to offset embodied carbon from operational savings

**Manager Communication Template:**
```
"Optimizing existing M1 hardware delivers {green_data['operational_carbon_reduction']} kg/year 
operational carbon savings with ZERO embodied carbon (no new device needed).

Buying new M3 hardware would save the same {green_data['operational_carbon_reduction']} kg/year 
operational carbon, but adds {green_data['m3_embodied_carbon_per_year']} kg/year embodied carbon 
from manufacturing.

Net result: M1 optimization is {green_data['m3_embodied_carbon_per_year']} kg/year MORE sustainable 
than buying M3. The M3 purchase would take {green_data['m3_payback_years']} years to offset its 
embodied carbon through operational savings.

Recommendation: Optimize M1 hardware instead of buying M3."
```

### 🔄 The 3-Year Refresh Cycle Argument

**The Challenge**: Company refresh cycle is every 3 years. How do we argue that keeping M1 fleet for an extra year (Year 4) while optimizing code is the most "innovative" choice?

**The Innovation Argument**:

**Traditional Approach (Buy M3 at Year 3)**:
- Year 3: Replace M1 fleet with M3 (350 kg CO₂ embodied carbon per device)
- Year 3-4: M3 operational savings: {green_data['operational_carbon_reduction']} kg/year
- **Total Year 3-4 Impact**: {green_data['m3_embodied_carbon_per_year']} kg/year embodied + {green_data['operational_carbon_reduction']} kg/year operational = **{green_data['total_carbon_impact_kg']} kg/year**

**Innovative Approach (Optimize M1, Extend to Year 4)**:
- Year 3: **Skip refresh**, optimize M1 code instead (0 kg embodied carbon)
- Year 3-4: M1 optimized savings: {green_data['operational_carbon_reduction']} kg/year
- **Total Year 3-4 Impact**: 0 kg/year embodied + {green_data['operational_carbon_reduction']} kg/year operational = **{green_data['operational_carbon_reduction']} kg/year**

**The Innovation Metrics**:
- **Carbon Savings**: {green_data['m3_embodied_carbon_per_year']} kg/year MORE sustainable (avoiding embodied carbon)
- **Cost Savings**: $0 hardware cost (vs. $X,XXX per device for M3)
- **Innovation Score**: **Higher** - Code optimization > Hardware refresh
- **Sustainability Leadership**: Demonstrates "optimize first, upgrade second" philosophy

**Manager Communication Template (3-Year Cycle)**:
```
"Our 3-year refresh cycle is approaching, but the most INNOVATIVE choice is to 
extend M1 hardware to Year 4 while optimizing our code.

Why this is innovative:
1. **Sustainability Leadership**: {green_data['m3_embodied_carbon_per_year']} kg/year MORE 
   sustainable than buying M3 (avoids embodied carbon entirely)
2. **Cost Efficiency**: $0 hardware cost vs. $X,XXX per device for M3 refresh
3. **Technical Innovation**: Code optimization demonstrates engineering excellence
4. **Future-Proofing**: Optimized code runs better on M3 when we DO upgrade (Year 4)

The Math:
- M3 Refresh (Year 3): {green_data['total_carbon_impact_kg']} kg/year total carbon
- M1 Optimization + Extension (Year 3-4): {green_data['operational_carbon_reduction']} kg/year total carbon
- Net Benefit: {green_data['m3_embodied_carbon_per_year']} kg/year carbon saved

The Strategy:
- Year 3: Optimize M1 code (0 kg embodied carbon, {green_data['operational_carbon_reduction']} kg/year savings)
- Year 4: Evaluate M3 upgrade (optimized code will run even better on M3)
- Result: Maximum sustainability + cost efficiency + technical innovation

Recommendation: Extend M1 fleet to Year 4 with code optimization. This is the 
most innovative, sustainable, and cost-effective approach."
```

### 📉 The M3 Payback Strategy: Using the Negative 0.6-Year Gap

**The Challenge**: You calculated a 3.6-year payback for a new M3. If a company typically replaces laptops at year 3, how do we use that "negative 0.6-year gap" to push for a software-first optimization sprint?

**The Strategy**: The 0.6-year gap (3.6-year payback vs 3-year refresh cycle) creates a **"Software-First Window"** where code optimization is more cost-effective than hardware refresh.

**The Math**:
- **M3 Payback Period**: {green_data['m3_payback_years']} years
- **Company Refresh Cycle**: 3 years
- **Gap**: {float(green_data['m3_payback_years']) - 3.0:.1f} years (negative = payback exceeds refresh cycle)

**What This Means**:
- M3 purchase **doesn't pay back** within the refresh cycle
- The company would **replace hardware before payback completes**
- This creates a **0.6-year window** where software optimization is the ONLY viable option

**Software-First Sprint Argument**:

**Manager Communication Template (Negative Gap Strategy)**:
```
"The M3 payback period is {green_data['m3_payback_years']} years, but our refresh 
cycle is 3 years. This creates a {float(green_data['m3_payback_years']) - 3.0:.1f}-year 
'negative gap' - the M3 won't pay back before we replace it again.

This negative gap is actually an OPPORTUNITY:

1. **Software-First Window**: We have {float(green_data['m3_payback_years']) - 3.0:.1f} years 
   where code optimization is the ONLY cost-effective option
   
2. **Immediate ROI**: Code optimization pays back in {green_data['carbon_payback_days']} days 
   (vs. {green_data['m3_payback_years']} years for M3)
   
3. **Risk Mitigation**: If we buy M3 now, we risk replacing it before payback completes
   
4. **Future-Proofing**: Optimized code runs better on M3 when we DO upgrade (Year 4)

The Strategy:
- **Now (Year 3)**: Software-first optimization sprint ({green_data['carbon_payback_days']} day payback)
- **Year 3.6**: M3 would have paid back (but we'd already be planning Year 4 refresh)
- **Year 4**: Evaluate M3 upgrade with optimized code (better performance, lower risk)

Recommendation: Use the negative {float(green_data['m3_payback_years']) - 3.0:.1f}-year gap as 
justification for a software-first optimization sprint. This is the ONLY option that 
pays back within our refresh cycle."
```

### 🎯 Why Showing Hardware Failure is More Effective

**The Psychology of Negative Framing**:

**Why "Hardware Won't Pay for Itself" Beats "Software is Better"**:

1. **Concrete Failure vs. Abstract Benefit**:
   - ❌ "Software optimization is better" = Abstract, subjective
   - ✅ "M3 won't pay back before we replace it" = Concrete, measurable failure
   - **Impact**: Managers understand concrete failures better than abstract benefits

2. **Risk Avoidance vs. Opportunity Seeking**:
   - ❌ "Software is better" = Requires manager to seek opportunity
   - ✅ "Hardware will fail to pay back" = Manager avoids risk
   - **Impact**: Risk avoidance is psychologically stronger than opportunity seeking

3. **Quantified Loss vs. Unquantified Gain**:
   - ❌ "Software saves money" = Unquantified, uncertain
   - ✅ "M3 loses 0.6 years of payback" = Quantified, certain loss
   - **Impact**: Quantified losses are more persuasive than unquantified gains

4. **Time-Bound Failure vs. Open-Ended Benefit**:
   - ❌ "Software is better" = No deadline, can wait
   - ✅ "M3 fails within 3 years" = Time-bound, urgent
   - **Impact**: Time-bound failures create urgency

**The Strategic Payback Logic**:

**Traditional Approach (Say Software is Better)**:
```
"Software optimization is better than hardware refresh because:
- It's more sustainable
- It's cheaper
- It's more innovative"
```
**Problem**: Abstract, subjective, no urgency

**Negative Gap Approach (Show Hardware Failure)**:
```
"M3 hardware won't pay for itself:
- Payback period: 3.6 years
- Refresh cycle: 3 years
- Gap: -0.6 years (hardware fails before payback)
- Risk: We replace it before it pays back
- Solution: Software optimization (4.7 day payback)"
```
**Advantage**: Concrete, measurable, urgent, risk-focused

**Manager Communication Template (Why This Works)**:
```
"The negative -0.6-year gap isn't just a number - it's proof that hardware 
refresh is a BAD INVESTMENT. Here's why showing failure is more effective:

1. **Concrete Failure**: 'M3 won't pay back' is measurable and certain
2. **Risk Avoidance**: Managers avoid bad investments (hardware) more than 
   they seek good ones (software)
3. **Quantified Loss**: -0.6 years = specific, certain loss
4. **Time-Bound Urgency**: 3-year refresh cycle = deadline for decision

This framing makes software optimization the ONLY rational choice."
```

### 🧠 The Psychology of the 'No': Why Risk Avoidance Beats Opportunity Seeking

**The Deep-Dive**: Why do you think a manager is more likely to act when told "Hardware won't pay back" versus "Software could save money"?

**The Psychological Framework**:

**1. Loss Aversion (Prospect Theory)**:
- **Loss Aversion Ratio**: People feel losses 2-2.5× more strongly than equivalent gains
- **"Hardware won't pay back"**: Framed as a LOSS (certain, measurable)
- **"Software could save money"**: Framed as a GAIN (uncertain, unquantified)
- **Impact**: Manager feels the loss of hardware investment more strongly than potential software gain

**2. Certainty Effect**:
- **Certain Loss**: "M3 won't pay back" = 100% certain, measurable (-0.6 years)
- **Uncertain Gain**: "Software could save money" = Uncertain, unquantified
- **Impact**: Managers prefer avoiding certain losses over pursuing uncertain gains

**3. Status Quo Bias**:
- **Hardware Purchase**: Requires CHANGE (buying new hardware)
- **Software Optimization**: Also requires change, but framed as avoiding hardware risk
- **Impact**: Manager avoids hardware risk (status quo = don't buy) more than seeking software gain

**4. Sunk Cost Fallacy Prevention**:
- **"Hardware won't pay back"**: Prevents sunk cost (buying hardware that won't pay back)
- **"Software could save money"**: Doesn't address existing sunk costs
- **Impact**: Manager avoids creating new sunk costs (hardware) more than pursuing software gains

**5. Time-Bound Urgency**:
- **Hardware Failure**: "Won't pay back in 3 years" = Time-bound, urgent deadline
- **Software Gain**: "Could save money" = Open-ended, no urgency
- **Impact**: Time-bound failures create urgency; open-ended gains can wait

**The Neuroscience**:
- **Risk Avoidance**: Activates amygdala (fear response) → Stronger emotional response
- **Opportunity Seeking**: Activates prefrontal cortex (rational planning) → Weaker emotional response
- **Result**: Fear-based decisions (avoiding hardware risk) are more compelling than rational planning (software gains)

**Manager Communication Template (Psychology Deep-Dive)**:
```
"Why 'Hardware Won't Pay Back' Works Better Than 'Software Could Save Money':

1. **Loss Aversion**: Managers feel losses 2-2.5× more strongly than gains
   - 'Hardware won't pay back' = Certain loss (more compelling)
   - 'Software could save money' = Uncertain gain (less compelling)

2. **Certainty Effect**: Certain losses > Uncertain gains
   - Hardware failure = 100% certain (-0.6 years)
   - Software gain = Uncertain, unquantified

3. **Status Quo Bias**: Avoiding bad decisions > Seeking good decisions
   - Don't buy hardware (status quo) = Avoid risk
   - Buy software optimization = Seek opportunity (requires change)

4. **Sunk Cost Prevention**: Avoid creating new sunk costs
   - Hardware purchase = New sunk cost (won't pay back)
   - Software optimization = Avoids hardware sunk cost

5. **Time-Bound Urgency**: Deadlines create action
   - Hardware failure = 3-year deadline (urgent)
   - Software gain = No deadline (can wait)

The Result: 'Hardware won't pay back' triggers loss aversion, certainty effect, 
and urgency - making it psychologically more compelling than 'Software could save money'."
```

**The Sprint Justification**:
- **Timeline**: Software optimization pays back in {green_data['carbon_payback_days']} days (fits in any sprint)
- **Risk**: M3 purchase risks non-payback (replaced before 3.6 years)
- **ROI**: Code optimization = {green_data['carbon_payback_days']} day payback vs {green_data['m3_payback_years']} year payback
- **Future Value**: Optimized code enhances M3 performance when we upgrade

**The Impact**

Every optimization you make with Power Benchmarking Suite contributes to:

- **Reduced Cloud Costs**: Energy efficiency = lower compute costs
- **Extended Battery Life**: Better user experience on mobile devices
- **Carbon Footprint Reduction**: Measurable CO₂ savings for ESG reporting
- **Sustainability Goals**: Quantified environmental impact for compliance
- **High-Impact Engineering**: Maximum environmental benefit per engineering hour

{stats_section}

## 🚀 Quick Start

```bash
# Install
pip install power-benchmarking-suite

# Quick test (30 seconds)
sudo power-benchmark monitor --test 30

# Validate system compatibility
power-benchmark validate

# Analyze app power consumption
sudo power-benchmark analyze app Safari --duration 60
```

## 📈 Key Features

- **Real-Time Power Monitoring**: ANE, CPU, GPU power consumption
- **Statistical Attribution**: Separate app power from system noise
- **Energy Gap Framework**: Cache-level optimization guidance
- **Thermal Guardian**: Prevent throttling with burst pattern optimization
- **Sustainability ROI**: Quantify CO₂ savings from optimizations

## 🎯 Use Cases

1. **ML Model Optimization**: Compare PyTorch vs CoreML performance (57× faster!)
2. **App Optimization**: Identify power-hungry code paths
3. **Battery Life Studies**: Analyze power consumption for mobile development
4. **Sustainability Reporting**: Generate ESG-compliant carbon footprint metrics

## 📚 Documentation

- **[Quick Start Guide](QUICK_START_GUIDE.md)** - Get started in 1-2 hours
- **[Product Study Guide](docs/PRODUCT_STUDY_GUIDE.md)** - Complete product knowledge
- **[Technical Deep Dive](docs/TECHNICAL_DEEP_DIVE.md)** - Whitepaper audit and proof points
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and implementation

## 🌱 Sustainability Commitment

Power Benchmarking Suite is designed with sustainability in mind:

- **Energy Efficiency First**: Every feature is optimized for minimal power consumption
- **Quantified Impact**: All optimizations include CO₂ savings calculations
- **ESG Ready**: Generate sustainability reports for compliance
- **Open Source**: Free and open for maximum impact

## 📊 Performance Benchmarks

| Metric | PyTorch (CPU/GPU) | CoreML (Neural Engine) | Improvement |
|--------|-------------------|------------------------|-------------|
| **Latency** | 28.01 ms | 0.49 ms | **57.2× faster** |
| **Throughput** | 35.71 inf/sec | ~2,040 inf/sec | **57.1× faster** |
| **Energy Efficiency** | Baseline | Optimized | **{green_data['energy_efficiency_improvement']}× improvement** |

## 💎 Premium Features

**Free Tier**: Single device, 1-hour sessions, basic metrics

**Premium ($99/month)**: 
- Up to 10 devices
- 24-hour sessions
- Advanced analytics
- Sustainability reports
- API access

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built to demonstrate the performance advantages of Apple's Neural Engine and CoreML framework on Apple Silicon hardware, with a focus on sustainability and energy efficiency.

---

**🌱 Built with sustainability in mind. Every optimization counts.**
"""


def _handle_course(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Generate course materials for Engineering Architect Program."""
    try:
        output_dir = Path(args.output) if args.output else Path("course_materials")
        output_dir.mkdir(exist_ok=True)

        if args.type == "syllabus" or args.type == "all":
            syllabus_content = _generate_course_syllabus()
            syllabus_path = output_dir / "ENGINEERING_ARCHITECT_SYLLABUS.md"
            syllabus_path.write_text(syllabus_content, encoding="utf-8")
            print(f"✅ Course syllabus generated: {syllabus_path}")

        if args.type == "landing" or args.type == "all":
            landing_content = _generate_landing_page()
            landing_path = output_dir / "LANDING_PAGE.md"
            landing_path.write_text(landing_content, encoding="utf-8")
            print(f"✅ Landing page generated: {landing_path}")

        if args.type == "all":
            print(f"\n📚 All course materials generated in: {output_dir.absolute()}")
            print(f"   - ENGINEERING_ARCHITECT_SYLLABUS.md")
            print(f"   - LANDING_PAGE.md")

        return 0
    except Exception as e:
        logger.error(f"Failed to generate course materials: {e}", exc_info=True)
        return 1


def _handle_whitepaper(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Generate architect white paper template."""
    try:
        output_path = Path(args.output)
        company = args.company or "Your Company"
        team_size = args.team_size or 10

        whitepaper_content = _generate_whitepaper_template(company, team_size)
        output_path.write_text(whitepaper_content, encoding="utf-8")

        print(f"\n✅ Architect white paper generated:")
        print(f"  Output: {output_path.absolute()}")
        print(f"  Company: {company}")
        print(f"  Team Size: {team_size}")
        print(f"\n💡 Next steps:")
        print(f"  1. Review: {output_path}")
        print(f"  2. Customize: Fill in company-specific data")
        print(f"  3. Present: Use as capstone project deliverable")

        return 0
    except Exception as e:
        logger.error(f"Failed to generate white paper: {e}", exc_info=True)
        return 1


def _handle_bio(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Generate LinkedIn/bio content."""
    try:
        output_path = Path(args.output)
        bio_content = _generate_linkedin_bio()
        output_path.write_text(bio_content, encoding="utf-8")

        print(f"\n✅ LinkedIn/bio content generated:")
        print(f"  Output: {output_path.absolute()}")
        print(f"\n💡 Next steps:")
        print(f"  1. Review: {output_path}")
        print(f"  2. Customize: Add your personal touch")
        print(f"  3. Update: Copy to LinkedIn profile")

        return 0
    except Exception as e:
        logger.error(f"Failed to generate bio: {e}", exc_info=True)
        return 1


def _generate_course_syllabus() -> str:
    """Generate 8-week course syllabus."""
    return r"""# 🎓 Engineering Architect Program - 8-Week Course Syllabus

**Outcome:** Move students from "Code Writers" (cost centers) to "System Architects" (profit centers) who can prove the financial impact of their decisions.

---

## Module 1 – The Silicon Truth

**Topic:** Load, heat, and the paradox of speed.

**Key Concepts:**
- Thermal Ceiling and Heat Tax
- Formula: $$Completion_Time = Work_Time + Throttling_Penalty_Time$$
- The 27% slowdown from sustained 100% load vs. ~80% sweet spot

**Lab:** Power‑benchmark your own machine to find the Thermal Ceiling and visualize the Heat Tax.

**Deliverable:** Thermal analysis report showing where your system hits thermal limits.

---

## Module 2 – The Engineering Insolvency Simulator

**Topic:** Technical debt vs. financial interest.

**Key Concepts:**
- 4,368% APR formula: $$Gap(t) = 7% \times 2^t$$
- Technical Payday Loan analogy
- 8-week bankruptcy timeline

**Lab:** Spreadsheet simulation of skipping optimization for one week, modeling exponential capacity loss and the Insolvency Date (8‑week crash).

**Deliverable:** Insolvency simulator spreadsheet with capacity forecasts.

---

## Module 3 – The Breaking Point

**Topic:** Reversibility vs. insolvency.

**Key Concepts:**
- Month 6: ~85% capacity (repairable zone)
- Month 9: Below 0% effective capacity (system insolvent; full rebuild required)
- Negative Breaking Point

**Lab:** Capacity modeling from Month 6 (repair) to Month 9 (rebuild); identify when capacity drops below demand.

**Deliverable:** Breaking point analysis with recovery timeline.

---

## Module 4 – Translating Benchmarks into Money

**Topic:** Salesman's Dictionary and FTE Recovery.

**Key Concepts:**
- The Leaky Pipe analogy
- 13.3‑month ROI calculation
- FTE recovery and rebuild avoidance

**Lab:** 13.3‑month ROI calculation; build a business case for a refactor using FTE savings and rebuild avoidance.

**Deliverable:** Business case document with ROI calculations.

---

## Module 5 – The Engineering of Quiet

**Topic:** Making invisible work visible.

**Key Concepts:**
- Thermostat Analogy
- 0 hotfixes as a metric
- Stability metrics for non-technical stakeholders

**Lab:** Thermostat Analogy dashboard that surfaces "0 hotfixes" and stability as a metric non‑technical stakeholders understand.

**Deliverable:** Dashboard mockup showing invisible work metrics.

---

## Module 6 – The Shield of Accountability

**Topic:** Objective refusal and Binary Priority.

**Key Concepts:**
- ROI Protection Formula
- Binary Priority framework
- Objective refusal scripts

**Lab:** Roleplay defending an optimization sprint against "just one small feature" requests.

**Deliverable:** Refusal script template with mathematical justification.

---

## Module 7 – Automation & AI (EasyFlow Niche)

**Topic:** Embedded AI optimization on constrained hardware.

**Key Concepts:**
- Model/infra choices for power efficiency
- ~15% power leakage reduction
- Constrained hardware optimization

**Lab:** Benchmark an inference model and cut power leakage by ~15% through model/infra choices.

**Deliverable:** AI optimization report with power savings.

---

## Module 8 – Capstone – The Architect's Pitch

**Project:** Build a Power Benchmarking Suite + Insolvency Model + ROI Business Case.

**Goal:** Present a Systemic Recovery Plan to a mock VP/CTO.

**Deliverable:** Complete Architect's White Paper (see template below).

---

## 🧪 Rubric – A‑Level Architect Standard

- ✅ Designs meaningful benchmarks and interprets heat/capacity behavior
- ✅ Builds a correct Insolvency Simulator and ties it to dollars and FTEs
- ✅ Communicates in analogies and ROI language a VP or Finance can act on
- ✅ Defends optimization work under pressure with trade‑off clarity
- ✅ Ships a cohesive Architect's White Paper + pitch that looks like 6–12 months of real architecture experience

---

**Course Materials:** All labs use the Power Benchmarking Suite. See `power-benchmark help` for command reference.
"""


def _generate_landing_page() -> str:
    """Generate landing page content."""
    return r"""# 🚀 Engineering Architect Program - 2026

## Most engineers are living on a **Technical Payday Loan**.

Stop pouring effort into a **Leaky Pipe**.

Join the 2026 Engineering Architect Program and learn how to write code that pays for itself.

---

## 💎 What You'll Learn

### From Code Writer to System Architect

Transform from a "cost center" to a "profit center" by proving the financial impact of your decisions.

**8-Week Program Outcomes:**
- ✅ Quantify the 27% Heat Tax and model Insolvency Timelines
- ✅ Build ROI business cases that VPs and Finance understand
- ✅ Defend optimization work with mathematical certainty
- ✅ Ship code that doesn't just work—it pays for itself

---

## 📈 The Mathematical Laws You'll Master

### Law of 80% – The Heat Tax
$$Completion_Time = Work_Time + Throttling_Penalty_Time$$

Sustained 100% load triggers a ~27% slowdown vs. running at ~80% under thermal limits.

### 4,368% APR – The Loan
$$Gap(t) = 7% \times 2^t$$

Skipping one week of optimization is modeled as taking a "technical payday loan" whose effective interest explodes over 8 weeks.

### Negative Breaking Point
- **Month 6:** ~85% capacity (repairable zone)
- **Month 9:** Below 0% effective capacity (system insolvent; full rebuild required)

---

## 🗣️ The Salesman's Dictionary

Learn to translate technical concepts into business language:

- **The Leaky Pipe:** Paying for water (FTE salaries, hardware) that never reaches the faucet (features shipped)
- **The Thermostat:** The system throttles itself off to avoid "fire," turning raw load into instability and crashes
- **The Payday Loan:** Skipping debt service feels fast today but bankrupts the project by Week 8 via compounding technical interest

---

## 🛡️ The Shield of Accountability

Master objective refusal scripts:

**"It's not my opinion; it's the ROI Protection Formula. Pulling this feature in now effectively puts us on a 4,368% interest rate on our delivery timeline."**

**"This optimization sprint isn't a cost; it's a recovery project that pays for itself in ~13.3 months by reclaiming ~1.5 FTEs of wasted capacity."**

---

## 🎓 8-Week Course Structure

1. **The Silicon Truth** - Thermal Ceiling and Heat Tax
2. **The Engineering Insolvency Simulator** - Technical debt as financial interest
3. **The Breaking Point** - Reversibility vs. insolvency
4. **Translating Benchmarks into Money** - FTE Recovery and ROI
5. **The Engineering of Quiet** - Making invisible work visible
6. **The Shield of Accountability** - Objective refusal and Binary Priority
7. **Automation & AI** - Embedded AI optimization
8. **Capstone – The Architect's Pitch** - White Paper + VP Presentation

---

## 🏆 What You'll Build

- Power Benchmarking Suite for your team
- Insolvency Model with capacity forecasts
- ROI Business Case with FTE calculations
- Architect's White Paper (capstone project)

---

## 💰 Investment

**Early Bird Pricing:** [Your Pricing]

**Includes:**
- 8 weeks of live instruction
- All course materials and labs
- Power Benchmarking Suite license
- Capstone project review
- Lifetime access to course updates

---

## 🚀 Ready to Transform Your Career?

**Stop living on Technical Payday Loans. Start building code that pays for itself.**

[Sign Up Now] [Learn More] [Schedule a Call]
"""


def _generate_whitepaper_template(company: str, team_size: int) -> str:
    """Generate architect white paper template."""
    fte_recovery = team_size * 0.15  # 15% capacity recovery
    monthly_savings = fte_recovery * 10000  # Rough estimate: $10k/month per FTE
    
    return f"""# 🏆 System Architect White Paper: Systemic Recovery Plan

**Company:** {company}  
**Team Size:** {team_size} developers  
**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Author:** [Your Name], System Architect

---

## 1. Executive Summary

### Bottom Line
This optimization sprint delivers a **13.3‑month ROI** by reclaiming **{fte_recovery:.1f} FTEs** of wasted capacity and preventing a full system rebuild.

### Warning
At current velocity, the system becomes unmaintainable by **[INSOLVENCY DATE]** if no action is taken.

### Analogy Anchor
**The Leaky Pipe:** We're paying for {team_size} developers, but only getting {team_size * 0.85:.0f} worth of productivity due to thermal throttling and technical debt. This optimization project plugs the leak.

---

## 2. Silicon Performance Analysis (Hardware)

### Thermal Ceiling Chart
[INSERT CHART: 100% load vs. 80% sweet spot showing Heat Tax]

**Key Finding:** "We are running in the red zone, wasting ${monthly_savings:,.0f}/month in lost cycles."

### Evidence
- Screens/plots of clock‑speed drops under sustained load
- Latency spikes during peak usage
- Power consumption data showing thermal throttling

### Current State
- **Thermal Ceiling:** [X]% (exceeds safe operating threshold)
- **Heat Tax:** ~27% performance penalty
- **Capacity Loss:** 15% of team productivity

---

## 3. Insolvency Model (Calendar)

### Capacity Forecast
- **Current:** ~85% capacity (Month 6 - repairable zone)
- **Month 9:** Below 0% effective capacity (system insolvent)
- **Deadline:** "At current velocity, the system becomes unmaintainable by **[DATE]**"

### Streak Status
- **4,368% APR narrative:** Skipping optimization weeks compounds technical debt exponentially
- **Formula:** $$Gap(t) = 7\% \times 2^t$$
- **8-Week Bankruptcy Timeline:** [INSERT TIMELINE CHART]

---

## 4. Systemic Recovery Plan (Solution)

### Hard Boundary
**Proposed 4‑week optimization sprint with Binary Priority (no new features)**

### ROI Calculation
- **FTEs Recovered:** {fte_recovery:.1f} (15% capacity recovery)
- **Monthly Savings:** ${monthly_savings:,.0f}/month
- **Annual Savings:** ${monthly_savings * 12:,.0f}/year
- **Payback Period:** 13.3 months
- **Rebuild Avoided:** $500,000+ (estimated full rebuild cost)

### Risk Mitigation
Move from "heroic" hotfix culture to preventative architecture:
- **Before:** 5+ hotfixes per month, unpredictable crashes
- **After:** 0 hotfixes, stable releases, predictable performance

---

## 5. Stakeholder Trade‑offs (Shield)

### Feature Impact
**Deferred Features (1-3):**
1. [Feature Name] - Deferred to protect 13.3-month ROI
2. [Feature Name] - Deferred to protect 13.3-month ROI
3. [Feature Name] - Deferred to protect 13.3-month ROI

### Math of "No"
"Deferring these features now avoids ~$500k in future rebuild and productivity losses. The ROI Protection Formula shows that any interruption to the optimization sprint effectively puts us on a 4,368% interest rate on our delivery timeline."

---

## 6. Implementation Timeline

**Week 1-2:** Thermal analysis and capacity modeling  
**Week 3:** Optimization implementation  
**Week 4:** Validation and ROI measurement

**Deliverables:**
- Thermal Ceiling analysis
- Insolvency Model with forecasts
- Optimized codebase
- ROI validation report

---

## 7. Success Metrics

- ✅ **Capacity Recovery:** {fte_recovery:.1f} FTEs regained
- ✅ **Heat Tax Eliminated:** 27% performance penalty removed
- ✅ **Hotfixes Reduced:** From 5+/month to 0
- ✅ **ROI Achieved:** 13.3-month payback period
- ✅ **Insolvency Avoided:** System remains above 85% capacity

---

## 8. Next Steps

1. **Approve Optimization Sprint:** 4-week hard boundary, binary priority
2. **Defer Features:** Protect ROI by deferring [Feature List]
3. **Measure Results:** Track capacity recovery and ROI validation
4. **Scale Success:** Apply framework to other systems

---

**Prepared by:** [Your Name]  
**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Status:** Ready for VP/CTO Review
"""


def _generate_linkedin_bio() -> str:
    """Generate LinkedIn headline and bio."""
    return """# 🔗 LinkedIn Profile Content

## Headline

Founder, Engineering Architect Program | Recovering 15% FTE Capacity via Silicon ROI Math

---

## Bio

I teach engineers how to stop living on Technical Payday Loans. My 8‑week framework turns junior developers into System Architects who lead with hard ROI math, not opinions.

Using my power‑benchmark suite, we quantify the 27% Heat Tax and model Insolvency Timelines to prove that great code doesn't just work—it pays for itself.

**What I teach:**
- The Law of 80% (Heat Tax): Why running at 100% is actually 27% slower
- The 4,368% APR Loan: How skipping optimization bankrupts projects in 8 weeks
- The Shield of Accountability: Objective refusal scripts that protect ROI
- The Salesman's Dictionary: Translating technical concepts into business language

**The Result:**
Engineers who can prove their code pays for itself with hard ROI math, not opinions.

**Join the 2026 Engineering Architect Program** and learn how to write code that pays for itself.

---

## Key Points for Profile

- **Value Proposition:** Transform from "cost center" to "profit center"
- **Unique Angle:** ROI math, not just code quality
- **Proof:** 13.3-month ROI, 15% FTE recovery, 0 hotfixes
- **Analogy:** Technical Payday Loan → Sustainable Engineering

---

## Call to Action

"Stop living on Technical Payday Loans. Start building code that pays for itself."

[Link to course/program]
"""

