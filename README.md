# GuardiumOne — AI Agent Risk Monitoring Dashboard

**Status:** Research Prototype / Controlled Testing  
**Project:** INSY 5379 Capstone Project — The University of Texas at Arlington

## Overview

GuardiumOne is an executive dashboard designed to make AI agent activity and potential risks easier to understand. It translates technical monitoring evidence into business-friendly explanations to support informed review and decision-making.

## Dashboard Features

- **Scenario Selection:** Explore controlled test scenarios through a consistent interface.
- **Level 1 — Executive Overview:** Understand expected versus observed behavior, risk status, potential business implications, key risk indicators, and the recommended next step.
- **Level 2 — Investigation:** Review relevant interaction graphs, supporting evidence, and available investigation findings.
- **Explainability:** Present technical measurements in plain language while retaining access to additional details for authorized reviewers.

The dashboard distinguishes observed evidence from unconfirmed outcomes and identifies unavailable measurements rather than estimating them.

## Getting Started

For authorized users with access to the required project files:

1. Open the project directory using Python 3.10 or later.
2. Install the required dependencies:

   pip install -r requirements.txt

3. Place the authorized `guardiumone_dashboard_data.json`
   file alongside the dashboard script.
4. Run the application:

   streamlit run guardiumone_dashboard.py

5. Open the local URL provided by Streamlit.

## Current Limitations

GuardiumOne is intended for controlled evaluation using
prepared test data. It is not a production monitoring
platform, does not independently perform risk analysis,
and does not automatically enforce policies or contain
AI agents.

## Confidentiality

This project is subject to a non-disclosure agreement (NDA).
Test evidence, internal architecture, proprietary implementation
details, and research materials are intentionally omitted
from this README. Access to and distribution of protected
project materials are limited to authorized individuals.
