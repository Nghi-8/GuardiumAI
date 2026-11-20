"""GuardiumOne | approved executive layout + validated November 18 ML scenarios.

Run: streamlit run guardiumone_dashboard.py
Data: nghi_dashboard_handoff_1118.json (same directory).
No direct DE2 reads, inference, or fabricated KRI measurements.
"""
import html as html_lib
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
st.set_page_config(page_title='GuardiumOne | Executive Risk Console', layout='wide', page_icon='🛡️')
st.markdown('''<style>
.stApp{background:#07090e;color:#f1f1ef}
[data-testid="stSidebar"]{background:#10141c}
div[data-testid="stMetric"]{background:#10141c;border:1px solid #303139;padding:14px;border-radius:9px;min-height:120px;overflow:hidden}
div[data-testid="stMetricValue"]{color:#edcd8c;font-family:monospace;font-size:clamp(.9rem,1.4vw,1.3rem);line-height:1.3}
div[data-testid="stMetricValue"] *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}
h1,h2,h3{letter-spacing:-.025em}
/* Larger essential copy; keep detailed help in tooltips/expanders. */
[data-testid="stMarkdownContainer"] p {font-size:1.02rem;line-height:1.65}
[data-testid="stCaptionContainer"] p {font-size:.91rem;line-height:1.48}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {font-size:.83rem}
.summary-lead{font-size:1.17rem;line-height:1.55;color:#f1f1ef;margin:0 0 .65rem 0}
.status-line{padding:.65rem .9rem;background:#171d24;border-left:4px solid #ff951f;border-radius:6px;font-size:1.02rem}
.focus-note{font-size:1.03rem;line-height:1.6;color:#ebeff0}
/* More separation through whitespace; fewer gray horizontal bars. */
.block-gap{height:1.3rem}

.pill{display:inline-block;padding:5px 10px;border-radius:5px;background:#322013;color:#ff951f;font-weight:700}
.stButton>button{border:1px solid #ff951f;background:#151a23;color:#ff951f}
</style>''', unsafe_allow_html=True)

try:
    with (ROOT / 'nghi_dashboard_handoff_1118.json').open(encoding='utf-8-sig') as handle:
        data = json.load(handle)
except (OSError, ValueError) as exc:
    st.error('Cannot read the validated ML handoff. Place nghi_dashboard_handoff_1118.json beside this Python script.')
    st.code(str(exc))
    st.stop()

if data.get('handoff_status') != 'FINAL_VALIDATED_FOR_DASHBOARD':
    st.error('The supplied handoff is not marked FINAL_VALIDATED_FOR_DASHBOARD.')
    st.stop()

scenarios = data['dashboard_scenarios_by_name']
scenario_keys = list(scenarios)
if not scenario_keys:
    st.error('No validated scenarios supplied by the ML handoff.')
    st.stop()

# The approved KRI definitions are retained. Only the Data Sensitivity entry
# and its card are removed; the Token Velocity availability sentence is updated.
KRI_HELP = {
    'BLAST RADIUS': (
        'Count of distinct resources directly targeted by NEW_EDGE relationships. '
        'Formula: count of unique target IDs across observed new relationships. '
        'Repeat signals and multiple agents targeting one resource do not increase the count. '
        'No downstream propagation or confirmed compromise is implied.'
    ),
    'BOUNDARY DRIFT': (
        'Count of distinct observed source–relationship–target triples absent from the '
        'proposed reference topology. Repeat NEW_EDGE signals for the same triple '
        'count only once. A new relationship does not automatically mean a policy breach.'
    ),
    'TOKEN VELOCITY': (
        'Sum of recorded LLM input and output tokens in a fixed monitoring window, '
        'divided by elapsed window minutes (tokens/min). Compare to similar historical '
        'windows before assessing a spike; without enough history, report '
        '“Insufficient history.” DE2 interaction counts are not token counts. '
        'A validated historical workflow token measurement is available only for the rejected-interaction scenario.'
    ),
}

# Stable per-scenario event details from ML; never use a missing/velocity event
# as a token-usage measurement from another workflow.
DETAIL_PATH = {
    scenario_keys[0]: ('level_2',),
    scenario_keys[1]: ('additional_validated_events', 'graph_boundary_anomaly'),
    scenario_keys[2]: ('additional_validated_events', 'velocity_anomaly'),
}

def get_detail(key):
    value = data
    for part in DETAIL_PATH[key]:
        value = value[part]
    return value


def nice_entity(value):
    if value.startswith('agent-'):
        return 'Agent: ' + value.removeprefix('agent-')
    if value.startswith('tool:'):
        return value.split(':')[-1].replace('_', ' ') + ' (tool)'
    if value.startswith('model:'):
        return value.split(':')[-1] + ' (model)'
    return value


# Executive-readable explanations, based on the validated ML handoff.
# These are presentation summaries, never replacement ML measurements.
SCENARIO_GUIDE = {
    'REJECTED_INTERACTION': {
        'short_name': 'Rejected payout action',
        'what': 'A customer-service AI agent attempted to use a payout approval tool, outside its assigned role of answering policy questions.',
        'why': 'Rule BL-1 prohibits customer-service agents from approving or sending payouts. DE2 flagged this interaction as rejected.',
        'unknown': 'The downstream financial outcome was not independently confirmed. Tier 2 reported MEDIUM risk but UNCERTAIN intent.',
        'focus': 'A policy-rejected connection is not the same as a NEW_EDGE signal.',
    },
    'GRAPH_BOUNDARY_ANOMALY': {
        'short_name': 'Graph boundary anomaly',
        'what': 'A claims-processing agent used an unapproved AI model, while two expected claim-processing tool connections were absent from the same trace.',
        'why': 'DE2 detected one NEW_EDGE to an unapproved model and two MISSING_EDGE signals for fetch claim and verify coverage. Tier 1 flagged the new connection as a graph and policy anomaly.',
        'unknown': 'The downstream effect has not been assessed. Tier 2 was triggered for all three findings but model execution was not run.',
        'focus': 'This trace contains one newly observed model connection and two missing expected tool connections.',
    },
    'VELOCITY_ANOMALY': {
        'short_name': 'Unusual claims-tool activity',
        'what': 'A claims agent used an approved claim-retrieval connection at a higher interaction rate than its recorded baseline.',
        'why': 'DE2 flagged 20 interactions versus a baseline of about 2.39 in its five-minute monitoring window.',
        'unknown': 'The event came from a controlled temporary velocity-test topology. Its version differs from the restored current v3 Qwen topology, and Tier 2 was not executed.',
        'focus': 'This is DE2 interaction activity, not the Token Velocity KRI measured in tokens/min.',
    },
}


def kri_explanation(signal_type, name):
    """Short context next to the card; authoritative values remain ML-provided."""
    if name == 'BLAST RADIUS':
        if signal_type == 'GRAPH_BOUNDARY_ANOMALY':
            return 'One agent reached one unapproved model directly; downstream impact is not assessed.'
        return 'No NEW_EDGE exposure for this event; other anomaly types can still require review.'
    if name == 'BOUNDARY DRIFT':
        return {
            'REJECTED_INTERACTION': 'This is a BL-1 policy rejection, not a NEW_EDGE drift signal.',
            'GRAPH_BOUNDARY_ANOMALY': 'One new model connection and two missing expected tool connections in one trace.',
            'VELOCITY_ANOMALY': 'The version mismatch comes from a controlled velocity test.',
        }[signal_type]
    if signal_type == 'REJECTED_INTERACTION':
        return 'Validated Nov. 17 workflow snapshot, not a current rolling measurement.'
    if signal_type == 'VELOCITY_ANOMALY':
        return 'Not measured for this event; DE2 interaction rate is a separate metric.'
    return 'No verified workflow-token measurement was captured for this trace.'



def boundary_drift_scope_note(signal_type):
    """Explain the expanded ML scenario measure without rewriting KRI_HELP."""
    if signal_type == 'GRAPH_BOUNDARY_ANOMALY':
        return ('ML scenario detail: Boundary Drift reports 1 new, unapproved model '
                'connection and 2 expected tool connections missing from the same trace. '
                'The original tooltip defines the distinct NEW_EDGE component only.')
    return None


def readable_status(value):
    """Readable backend states; original machine values remain in Technical Evidence."""
    if value is None:
        return 'Not supplied'
    states = {
        'COMPLETED': 'Completed',
        'ASSESSED': 'Assessed',
        'NOT_ASSESSED': 'Not assessed',
        'NOT_MEASURED': 'Not measured',
        'NOT_EXECUTED_BY_DESIGN': 'Not executed by design',
        'AWAITING_EXPLICIT_EXECUTION': 'Triggered — not executed by design',
        'VERSION_MISMATCH': 'Version mismatch — controlled test',
        'VERSION_MISMATCH_EXPECTED_AFTER_CONTROLLED_TEST_RESTORE': 'Version mismatch — controlled test',
        'READY': 'Ready',
    }
    return states.get(str(value), str(value).replace('_', ' ').capitalize())


def evidence_summary(scenario, detail):
    """Exclude evaluator-only guidance from participant-facing evidence JSON."""
    ev = scenario['evidence']
    return {
        'incident_id': ev['incident_id'],
        'event_type': ev['event_type'],
        'agent': ev['agent'],
        'target': ev['target'],
        'event_time': ev.get('event_time'),
        'tier1_flagged': ev.get('tier1_flagged'),
        'tier2_status': ev.get('tier2_status'),
        'data_classification_status': ev.get('data_classification_status'),
        'access_outcome': ev.get('access_outcome'),
        'token_metrics_status': ev.get('token_metrics_status'),
        'interaction_velocity': ev.get('interaction_velocity'),
    }


def graph_edges_for_view(scenario_key, focus_event):
    """Full approved network for Level 1; exact scenario relationships for Level 2."""
    edges = data['level_1']['graph']['edges']
    if not focus_event:
        return edges
    states = scenarios[scenario_key]['graph_rendering'].get('edge_states') or []
    if states:
        relevant = {(item['source'], item['target']) for item in states}
        return [edge for edge in edges if (edge['source'], edge['target']) in relevant]
    selected_agent = scenarios[scenario_key]['agent']
    selected_target = scenarios[scenario_key]['evidence']['target']
    return [edge for edge in edges if edge['source'] == selected_agent
            and edge['target'] == selected_target]


def edge_display(edge, scenario_key):
    """Label and style per validated ML edge state, not inferred from historical observed flags."""
    scenario = scenarios[scenario_key]
    mode = scenario['graph_rendering']['anomaly_type']
    states = scenario['graph_rendering'].get('edge_states') or []
    state = next((s for s in states if s['source'] == edge['source']
                  and s['target'] == edge['target']), None)
    if state:
        state_code = state['state']
        if state_code in ('OBSERVED_NOT_APPROVED_POLICY_REJECTED', 'OBSERVED_NOT_APPROVED_NEW_EDGE'):
            return state['label'], 'orange'
        if state_code in ('APPROVED_NOT_OBSERVED_IN_SELECTED_TRACE',
                          'APPROVED_BASELINE_NOT_OBSERVED_IN_SELECTED_TRACE'):
            return state['label'], 'grey'
        if state_code == 'APPROVED_AND_OBSERVED':
            return state['label'], 'green'
    if mode == 'VELOCITY_ANOMALY' and (
        edge['source'] == scenario['agent'] and
        edge['target'] == scenario['evidence']['target']
    ):
        return 'VELOCITY ANOMALY', 'orange'
    # A flagged edge from another scenario should NOT be highlighted as the selected finding.
    if edge.get('approved') is False:
        return 'OTHER VALIDATED EVENT', 'muted'
    return 'APPROVED BASELINE', 'green'


def graph_mermaid(scenario_key, focus_event=True):
    """Mermaid directed graph with scenario-scoped evidence styling."""
    edges = graph_edges_for_view(scenario_key, focus_event)
    triples = [(e['source'], e['relationship'], e['target']) for e in edges]
    entities = sorted({node for src, _, dst in triples for node in (src, dst)})
    node_ids = {name: f'N{i}' for i, name in enumerate(entities)}
    lines = ['flowchart LR']
    for name, nid in node_ids.items():
        label = nice_entity(name).replace('"', "'").replace('\n', ' ')
        lines.append(f'{nid}["{label}"]')
    styles = {'green': [], 'orange': [], 'grey': [], 'muted': []}
    for idx, edge in enumerate(edges):
        label, status = edge_display(edge, scenario_key)
        label = label.replace('"', "'")
        lines.append(f'{node_ids[edge["source"]]} -->|"{label}"| {node_ids[edge["target"]]}')
        styles[status].append(idx)
    for kind, css in (
        ('green', 'stroke:#65a78b,stroke-width:2px;'),
        ('orange', 'stroke:#ff951f,stroke-width:4px;'),
        ('grey', 'stroke:#91959f,stroke-width:3px,stroke-dasharray:5 5;'),
        ('muted', 'stroke:#637082,stroke-width:1.5px;'),
    ):
        if styles[kind]:
            lines.append('linkStyle ' + ','.join(map(str, styles[kind])) + ' ' + css)
    lines.append('classDef default fill:#10141c,stroke:#677080,color:#f2f2f2;')
    return '\n'.join(lines)


def render_mermaid(key, focus_event=True):
    """Render Mermaid explicitly; show the same edges if its CDN is unavailable."""
    code = graph_mermaid(key, focus_event=focus_event)
    edges = graph_edges_for_view(key, focus_event)
    fallback_rows = []
    for edge in edges:
        state, style = edge_display(edge, key)
        accent = {'green': '#65a78b', 'orange': '#ff951f',
                  'grey': '#b1b4bd', 'muted': '#637082'}[style]
        source = html_lib.escape(nice_entity(edge['source']))
        target = html_lib.escape(nice_entity(edge['target']))
        fallback_rows.append(
            f'<div class="edge-row" style="--accent:{accent}">'
            f'<span class="node">{source}</span>'
            f'<span class="edge-label">⟶<small>{html_lib.escape(state)}</small></span>'
            f'<span class="node">{target}</span></div>'
        )
    fallback = ''.join(fallback_rows) or '<p>No graph relationships provided.</p>'
    js_code = json.dumps(code).replace('</', '<\\/')
    embed = f'''<style>
      body{{background:#07090e;color:#f1f1ef;font:14px system-ui,sans-serif;margin:6px}}
      #fallback{{display:grid;gap:12px;max-height:425px;overflow:auto;padding:3px}}
      .edge-row{{display:flex;align-items:center;gap:8px;min-width:0}}
      .node{{background:#10141c;border:1px solid #677080;border-radius:6px;padding:10px 8px;
             flex:1;min-width:0;overflow-wrap:anywhere;text-align:center;font-size:14px}}
      .edge-label{{display:flex;flex-direction:column;align-items:center;gap:4px;
                   flex:0 0 128px;color:var(--accent);font-size:22px;font-weight:700}}
      .edge-label small{{font-size:11px;line-height:1.3;text-align:center}}
      #mermaid-target{{display:none}}
      #mermaid-target svg{{max-width:100%;height:auto}}
      @media(max-width:650px){{.edge-label{{flex-basis:92px}}.node{{font-size:12px}}}}
    </style>
    <div id="fallback" aria-label="Interaction relationship graph">{fallback}</div>
    <div id="mermaid-target" class="mermaid"></div>
    <script type="module">
      const source = {js_code};
      try {{
        const m = await import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs');
        const mermaid = m.default;
        mermaid.initialize({{startOnLoad:false,theme:'dark',securityLevel:'strict',
          themeVariables:{{background:'#07090e',primaryColor:'#10141c',
                           primaryTextColor:'#eeeeee',lineColor:'#ff951f'}}}});
        const node = document.getElementById('mermaid-target');
        node.textContent = source;
        node.style.display = 'block';
        await mermaid.run({{nodes:[node]}});
        if (!node.querySelector('svg')) throw new Error('Mermaid did not create SVG');
        document.getElementById('fallback').style.display = 'none';
      }} catch (error) {{
        document.getElementById('mermaid-target').style.display = 'none';
        document.getElementById('fallback').style.display = 'grid';
        console.warn('Mermaid unavailable; showing validated relationship fallback.', error);
      }}
    </script>'''
    components.html(embed, height=450, scrolling=True)

if 'selected_scenario' not in st.session_state or st.session_state.selected_scenario not in scenarios:
    st.session_state.selected_scenario = data['display_contract']['default_selected_scenario_key']
if 'view_level' not in st.session_state:
    st.session_state.view_level = 1

with st.sidebar:
    st.title('GUARDIUMONE')
    st.caption('AgentMonitor · executive prototype')
    st.markdown('---')
    chosen = st.selectbox('Scenario', scenario_keys,
                          index=scenario_keys.index(st.session_state.selected_scenario),
                          format_func=lambda k: k.split(' · ', 1)[0] + ' · ' + SCENARIO_GUIDE[scenarios[k]['graph_rendering']['anomaly_type']]['short_name'])
    if chosen != st.session_state.selected_scenario:
        st.session_state.selected_scenario = chosen
        st.session_state.view_level = 1
        st.rerun()
    if st.session_state.view_level == 2:
        if st.button('← Back to overview', width='stretch'):
            st.session_state.view_level = 1
            st.rerun()
    st.info('Validated live sandbox evidence · Not a production incident.')
    st.caption('Selected ML scenario: ' + st.session_state.selected_scenario)
    st.caption('Choose a scenario, review Level 1, then investigate its evidence in Level 2.')
    st.caption('Approved topology: ' + data['current_environment']['current_topology_version'])
    st.caption('Measurement counts describe the selected validated evidence package, not the full telemetry stream.')
    with st.expander('Data source details'):
        st.write('Processed, validated ML/KRI handoff; the dashboard does not read raw DE2 data.')
        st.code('nghi_dashboard_handoff_1118.json')
        st.caption('Handoff revision: ' + data['handoff_revision'])

key = st.session_state.selected_scenario
scenario = scenarios[key]
signal_type = scenario['graph_rendering']['anomaly_type']
guide = SCENARIO_GUIDE[signal_type]
detail = get_detail(key)
incident = scenario['incident']

st.caption('ENTERPRISE AI GOVERNANCE / EXECUTIVE VIEW / VALIDATED SANDBOX')
if st.session_state.view_level == 1:
    st.caption('LEVEL 1 / EXECUTIVE OVERVIEW')
    st.title('AI Risk Overview')
    st.markdown(f"### {scenario['headline']}")
    st.markdown('<div class="summary-lead">' + html_lib.escape(guide['what']) + '</div>',
                unsafe_allow_html=True)
    status_label = {
        'REJECTED_INTERACTION': 'Policy rejected · BL-1 · Review required',
        'GRAPH_BOUNDARY_ANOMALY': 'Unapproved model + two missing steps · Review required',
        'VELOCITY_ANOMALY': 'Unusual interaction activity · Review required',
    }[signal_type]
    st.markdown('<div class="status-line"><strong>' + html_lib.escape(status_label) +
                '</strong> · Validated live sandbox evidence (not production)</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)

    st.subheader('Three Executive KRIs')
    risk = scenario['risk_data']
    values = [
        ('BLAST RADIUS', risk['blast']),
        ('BOUNDARY DRIFT', risk['drift']),
        ('TOKEN VELOCITY', risk['tokens']),
    ]
    for col, (name, value) in zip(st.columns(3, gap='medium'), values):
        with col:
            st.metric(name, value, help=KRI_HELP[name])
    # Short explanation avoids interpreting a zero as confirmation of safety.
    with st.expander('What do these measurements mean?'):
        for name, _ in values:
            st.markdown('**' + name.title() + ':** ' + kri_explanation(signal_type, name))
        scope_note = boundary_drift_scope_note(signal_type)
        if scope_note:
            st.info(scope_note)
        st.caption('Hover over each KRI label for its original calculation definition.')

    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.4, 1], gap='large')
    with left:
        st.subheader('Approved vs. Observed Interaction Graph')
        st.caption('Current approved baseline and validated flagged activity; not a complete trace of this event.')
        # Level 1: full graph always visible. Avoid rendering Mermaid inside a collapsed expander.
        render_mermaid(key, focus_event=False)
        st.caption('Green: approved baseline · Orange: selected flagged connection · Gray dashed: expected but missing in the selected trace · Muted: another event')
        st.button('Investigate this event →', type='primary', width='stretch',
                  on_click=lambda: st.session_state.update(view_level=2))
    with right:
        st.subheader('Why it matters')
        st.markdown('<div class="focus-note">' + html_lib.escape(guide['why']) + '</div>',
                    unsafe_allow_html=True)
        st.markdown('**What remains unknown**')
        st.write(guide['unknown'])
        with st.expander('Evidence signals and identifiers'):
            st.write('Agent:', nice_entity(scenario['agent']))
            st.write('Target:', nice_entity(scenario['evidence']['target']))
            st.write('Signal:', scenario['evidence']['event_type'])
            st.write('Event ID:', incident)
            if signal_type == 'GRAPH_BOUNDARY_ANOMALY':
                st.write('Graph findings:', '1 NEW_EDGE and 2 MISSING_EDGE signals in the same trace')
            if signal_type == 'REJECTED_INTERACTION':
                st.write('Direct incident scope:', '1 agent / 1 target (different from NEW_EDGE Blast Radius)')
            elif signal_type == 'VELOCITY_ANOMALY':
                iv = scenario['evidence']['interaction_velocity']
                st.write('DE2 interaction rate:', f"{iv['current_rate']} vs {iv['baseline_rate']:.2f} baseline")
                st.caption('Interaction velocity is NOT token velocity.')

    with st.expander('Backend evidence · Optional technical detail'):
        st.caption('The full backend details refer only to the selected validated event.')
        st.json(detail.get('backend_processing', {}), expanded=False)
        st.json(evidence_summary(scenario, detail), expanded=False)
        st.download_button('Export scenario evidence', json.dumps(scenario['evidence'], indent=2),
                           file_name=f'{scenario["evidence"]["event_type"].lower()}_evidence.json',
                           mime='application/json')
else:
    st.title('Connection Investigation')
    st.caption('LEVEL 2 / EVENT INVESTIGATION · Validated sandbox evidence')
    st.subheader(scenario['headline'])
    event = detail['primary_event'] if signal_type == 'GRAPH_BOUNDARY_ANOMALY' else detail['selected_event']
    st.markdown('<span class="pill">EVENT-LEVEL EVIDENCE</span>', unsafe_allow_html=True)
    # Level 1 already explains what happened, why it matters, and what is unknown.
    # Keep Level 2 focused on detailed connections, observations, and ML findings.
    st.caption('Investigate the selected connection, review validated observations, and inspect the backend findings.')
    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)
    st.subheader('Three Executive KRIs · Selected Event')
    risk = scenario['risk_data']
    for col, (name, value) in zip(st.columns(3), [
        ('BLAST RADIUS', risk['blast']),
        ('BOUNDARY DRIFT', risk['drift']),
        ('TOKEN VELOCITY', risk['tokens']),
    ]):
        with col:
            st.metric(name, value, help=KRI_HELP[name])
    scope_note = boundary_drift_scope_note(signal_type)
    if scope_note:
        st.caption(scope_note)

    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)
    a, b = st.columns([1.45, 1])
    with a:
        # Level 2: show only the selected agent's relevant connection(s).
        # This is intentionally different from Level 1's full approved topology.
        st.subheader('Selected Event Connection')
        render_mermaid(key, focus_event=True)
        if signal_type == 'REJECTED_INTERACTION':
            st.caption('Orange: rejected payout action · Gray dashed: approved lookup absent from this trace')
        elif signal_type == 'GRAPH_BOUNDARY_ANOMALY':
            st.caption('Orange: new unapproved model · Gray dashed: two expected tool steps missing from the trace')
        else:
            st.caption('Orange: approved claim-retrieval connection flagged for unusual interaction rate')
        st.subheader('Event Evidence Trail')
        st.caption('Validated observations and backend processing. The steps below describe evidence stages, not an inferred sequence of agent actions.')
        if signal_type == 'REJECTED_INTERACTION':
            context = detail['backend_processing']['runtime_context']
            observed = context['observed_action']
            st.markdown('**1. Tool action recorded**')
            st.write('Customer-service agent → ' + nice_entity(event['target_entity_id']))
            st.write('Action: ' + observed['operation'].replace('_', ' ') + ' · ' + str(observed.get('tool', 'Not supplied')).replace('_', ' '))
            st.markdown('**2. Policy rejection issued**')
            st.write('DE2 emitted REJECTED_INTERACTION under rule ' + str(detail['backend_processing']['tier1_evidence']['policy_id']) + '.')
            st.markdown('**3. Backend processing recorded**')
            st.write('Tier 1 flagged the policy violation; Tier 2 analysis completed.')
            st.caption('The observed action is not confirmation that a payout was completed.')
        elif signal_type == 'GRAPH_BOUNDARY_ANOMALY':
            st.markdown('**1. New model relationship observed**')
            st.write(nice_entity(event['source_entity_id']) + ' → ' + nice_entity(event['target_entity_id']))
            st.caption('NEW_EDGE · observed relationship not in the approved current-v3 topology')
            missing = detail['associated_missing_edge_events']
            for idx, item in enumerate(missing, start=2):
                st.markdown(f'**{idx}. Expected tool relationship not observed**')
                st.write(nice_entity(item['source_entity_id']) + ' → ' + nice_entity(item['target_entity_id']))
                st.caption('MISSING_EDGE · expected connection absent from the selected trace')
            st.markdown('**4. Backend processing recorded**')
            st.write('Tier 1 flagged all three signals; all triggered Tier 2 preparation.')
            st.caption('All three findings belong to the same validated trace. This display order is not an execution timeline.')
        else:
            v = scenario['evidence']['interaction_velocity']
            st.markdown('**1. Approved tool relationship observed**')
            st.write(nice_entity(event['source_entity_id']) + ' → ' + nice_entity(event['target_entity_id']))
            st.markdown('**2. Interaction-rate anomaly emitted**')
            st.write(f"Recorded: {v['current_rate']:g} interactions · Baseline: {v['baseline_rate']:.2f} · Threshold: {v['threshold']:g} · Window: {v['window_minutes']:g} minutes")
            st.markdown('**3. Backend processing recorded**')
            st.write('Tier 1 flagged the velocity anomaly and identified a topology-version mismatch.')
            st.caption('Interaction rate is not Token Velocity in tokens/min. The different topology is documented controlled-test provenance.')
        st.caption('Source: validated ML handoff; no events, metrics, or outcomes were inferred.')
    with b:
        st.subheader('Investigation Findings')
        st.caption('Backend determinations and unresolved questions—not a repeat of the event trace.')
        processing = detail.get('backend_processing', {})
        if signal_type == 'GRAPH_BOUNDARY_ANOMALY':
            stages = [
                ('New model edge', processing.get('NEW_EDGE', {})),
                ('Missing fetch_claim', processing.get('MISSING_FETCH', {})),
                ('Missing verify_policy_coverage', processing.get('MISSING_VERIFY', {})),
            ]
            for label, stage in stages:
                t1 = stage.get('tier1_evidence', {})
                st.markdown('**' + label + '**')
                st.write('Graph anomaly: ' + ('Detected' if t1.get('graph_anomaly') is True else 'Not flagged' if t1.get('graph_anomaly') is False else 'Not supplied'))
                if t1.get('policy_violation') is True:
                    st.write('Policy finding: Flagged · ' + str(t1.get('policy_id') or 'Policy ID unavailable'))
                st.caption('Tier 2: Triggered — ' + readable_status(stage.get('tier2_result_status')))
            st.markdown('**Topology assessment:** ' + readable_status(processing.get('NEW_EDGE', {}).get('tier1_evidence', {}).get('topology_assessment_status')))
            st.markdown('**Downstream impact:** ' + readable_status(detail.get('blast_radius', {}).get('downstream_impact_status')))
        else:
            t1 = processing.get('tier1_evidence', {})
            st.markdown('**Tier 1 assessment**')
            st.write('Flagged: ' + ('Yes' if t1.get('tier1_flagged') else 'No' if t1.get('tier1_flagged') is False else 'Not supplied'))
            st.write('Graph anomaly: ' + ('Detected' if t1.get('graph_anomaly') is True else 'Not flagged' if t1.get('graph_anomaly') is False else 'Not supplied'))
            st.write('Policy violation: ' + ('Flagged' if t1.get('policy_violation') is True else 'Not flagged' if t1.get('policy_violation') is False else 'Not supplied'))
            st.write('Velocity anomaly: ' + ('Detected' if t1.get('velocity_anomaly') is True else 'Not flagged' if t1.get('velocity_anomaly') is False else 'Not supplied'))
            st.write('Topology assessment: ' + readable_status(t1.get('topology_assessment_status')))
            st.markdown('**Tier 2 assessment**')
            st.write('Execution: ' + readable_status(processing.get('tier2_execution_status', processing.get('tier2_result_status'))))
            if signal_type == 'REJECTED_INTERACTION':
                tier2 = processing.get('tier2_handoff', {}).get('tier2_result', {})
                intent = processing.get('tier2_handoff', {}).get('intent_drift_result', {})
                st.write('Composite risk: ' + str(tier2.get('risk_level', 'Not supplied')))
                st.write('Intent classification: ' + str(intent.get('classification', 'Not supplied')))
                st.markdown('**Unconfirmed:** Downstream payout outcome')
            else:
                st.markdown('**Unresolved:** ' + readable_status(processing.get('tier2_result_status')))
                st.caption('Version mismatch reflects the controlled velocity-test topology.')
        st.caption('No automatic containment action is asserted by the ML handoff.')

    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)
    st.subheader('Technical Evidence')
    st.caption('Optional supporting material, kept out of the main investigation flow.')
    with st.expander('Event details and identifiers'):
        st.write('Event ID:', incident)
        st.write('Trace ID:', event.get('trace_id', 'Not supplied'))
        st.write('Span ID:', event.get('span_id') or 'Not supplied')
        st.write('Evidence source:', scenario['evidence']['source'])
        st.json(event, expanded=False)
    with st.expander('Tier 1 / Tier 2 backend evidence'):
        st.json(processing, expanded=False)
    with st.expander('Selected event JSON'):
        st.json(detail, expanded=False)
    st.download_button('Export selected event evidence', json.dumps(detail, indent=2),
                       file_name=f'{event["signal_type"].lower()}_event.json', mime='application/json')

with st.expander('Data provenance'):
    st.caption('Validated ML/KRI handoff · selected evidence set only; not the full telemetry stream.')
    st.write('Handoff:', data['handoff_revision'])
    st.write('Current topology:', data['current_environment']['current_topology_version'])
    st.write('Current model mode:', data['current_environment']['current_model_mode'])
    st.caption('The controlled velocity test used a temporary topology; it is not the current v3 Qwen baseline.')
# Do not display the full handoff in participant mode: it includes evaluator-only
# recommended decisions. Keep the validated source JSON in the app directory.

