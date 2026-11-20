# GuardiumOne — AI Agent Risk Monitoring Dashboard

**Status:** Research Prototype / Testing  
**Project:** INSY 5379 Capstone Project — The University of Texas at Arlington  
**Industry Collaboration:** GuardiumAI

## 1. Project Overview

GuardiumOne is an executive dashboard designed to help business leaders understand potential risks associated with AI agents.

AI agents can perform tasks, access information, and interact with systems with limited human involvement. While this improves efficiency, organizations need visibility into what agents are doing and whether their activities remain within approved boundaries.

The dashboard helps answer four questions:

1. What was the AI agent supposed to do?
2. What did the agent actually do?
3. Was any unusual or potentially risky activity detected?
4. What evidence is available to support further investigation?

**Current data source:** The dashboard uses validated live sandbox evidence processed by the ML team. It does not monitor production environments or independently perform machine-learning analysis.

## 2. Current Scenarios

The sidebar allows users to switch between three validated scenarios.

| Scenario | Description |
|---|---|
| **1. Live Rejected Interaction** | A customer-service AI agent attempted a payout approval action outside its assigned responsibilities. |
| **2. Live Graph Boundary Anomaly** | A claims-processing agent connected to an unapproved AI model, while two expected tool connections were missing from the same activity trace. |
| **3. Live Velocity Anomaly** | A claims-processing agent showed unusually frequent interactions compared with its normal activity level. |

Selecting a scenario updates the dashboard's risk indicators, graphs, and supporting evidence.

## 3. Dashboard Walkthrough

The dashboard has two levels to help users move from a quick overview to a more detailed investigation.

### Level 1 — Executive Overview

Level 1 helps business leaders understand the main concern quickly.

**Incident Summary**

Displays a short description of the selected activity and explains why it may require attention.

**Three Executive Key Risk Indicators (KRIs)**

A KRI is a measurement used to identify or monitor potential risk.

| KRI | What It Means |
|---|---|
| **Blast Radius** | Measures the number of agents and targets associated with newly observed connections outside the approved network. |
| **Boundary Drift** | Identifies differences between expected and observed system connections, including new or missing relationships. |
| **Token Velocity** | Measures how quickly an AI workflow consumes text-processing tokens over time. |

The three cards use consistent titles, definitions, and formatting across scenarios and between Level 1 and Level 2. Only the evidence-based values change.

When a measurement is unavailable, the dashboard displays **Not measured** rather than estimating a value.

Users can expand **What do these measurements mean?** for additional explanations.

**Approved vs. Observed Interaction Graph**

The full interaction graph displays the approved network and selected validated abnormalities.

It helps users distinguish normal connections from activities requiring further review, including rejected actions, unapproved connections, and expected connections that were not observed.

The graph includes labels and a legend explaining the connection types.

**Supporting Context**

The right panel explains why the selected activity matters and what information remains unknown. Additional event identifiers and backend evidence are available in expandable sections.

Users can select **Investigate this event** to open Level 2.

### Level 2 — Connection Investigation

Level 2 provides more detail about the selected activity without repeating the entire network overview.

**Selected Event Connection**

Displays a smaller graph focused on the relevant AI agent and its connections. Users can expand the connection details to view full technical names and evidence labels.

**Event Evidence Trail**

Explains the validated observations and backend processing steps.

Depending on the scenario, this may include an attempted tool action, a newly observed connection, missing expected connections, or unusual interaction activity.

**Investigation Findings**

Summarizes what the ML backend determined, including whether unusual activity was detected, whether a policy issue was flagged, and the status of further analysis.

It also identifies information that has not been confirmed or assessed.

**Technical Evidence**

Provides expandable records containing event identifiers, backend findings, and supporting JSON information.

Users can download the selected event evidence for further review.

## 4. Data Integration

GuardiumOne uses a JSON handoff provided by the ML team.

The current application reads:

`nghi_dashboard_handoff_1118.json`

The general data flow is:

**Agent activity → DE2 detection → ML validation and risk analysis → JSON handoff → GuardiumOne dashboard**

The ML backend provides the evidence and available measurements. The Streamlit dashboard organizes that information into a manager-friendly interface.

The application preserves the reported measurements and does not automatically calculate missing values or assume that unusual activity caused confirmed harm.

## 5. How to Run the Dashboard

**Requirements:** Python 3.10 or later and the dependencies listed in `requirements.txt`.

1. Clone or download the repository.
2. Open a terminal in the project directory.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the dashboard:

```bash
streamlit run guardiumone_dashboard.py
```

5. Open the local URL provided by Streamlit.

Keep `guardiumone_dashboard.py` and `nghi_dashboard_handoff_1118.json` in the same directory.

## 6. Current Limitations

GuardiumOne is a research prototype and is not connected to real-time production monitoring.

- **File-based integration:** The current version reads a validated JSON handoff rather than continuously receiving new ML events.
- **Scenario compatibility:** New event types or changes to the JSON structure may require dashboard code updates.
- **Evidence coverage:** The graph and reported measurements represent the selected validated evidence package, not every interaction in the underlying monitoring system.
- **Unavailable measurements:** Some outcomes, including downstream impact and containment information, have not been confirmed or measured.
- **No automated response:** The dashboard supports investigation and understanding; it does not independently block, revoke, or contain AI agents.
- **Research use:** The dashboard is intended for controlled testing and evaluation before broader deployment.

## 7. Future Improvements

Potential improvements include uploading new ML JSON handoffs through the dashboard, automatically recognizing additional scenarios, strengthening data validation, and supporting more automated backend integration.

These features are planned possibilities and are **not part of the current implementation**.

---

**GuardiumOne aims to make AI agent behavior easier to understand by translating technical monitoring evidence into clear, useful information for business decision-makers.**
