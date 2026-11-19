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
    scenario_keys[1]: ('additional_validated_events', 'missing_edge'),
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
    'MISSING_EDGE': {
        'short_name': 'Expected policy lookup missing',
        'what': 'A policy-status lookup connection that was expected in this customer-service trace was not observed.',
        'why': 'DE2 produced a MISSING_EDGE signal. The approved relationship exists in the baseline, but it is absent from the selected trace.',
        'unknown': 'The evidence does not establish why the lookup was absent. Tier 2 analysis was triggered but not executed.',
        'focus': 'A missing expected connection is different from an unexpected new connection.',
    },
    'VELOCITY_ANOMALY': {
        'short_name': 'Unusual claims-tool activity',
        'what': 'A claims agent used an approved claim-retrieval connection at a higher interaction rate than its recorded baseline.',
        'why': 'DE2 flagged 20 interactions versus a baseline of about 2.39 in its five-minute monitoring window.',
        'unknown': 'The event came from a controlled temporary v3 topology. Its version differs from the restored current v2 topology, and Tier 2 was not executed.',
        'focus': 'This is DE2 interaction activity, not the Token Velocity KRI measured in tokens/min.',
    },
}


def kri_explanation(signal_type, name):
    """Short context next to the card; authoritative numbers stay in the ML payload."""
    if name == 'BLAST RADIUS':
        return 'No NEW_EDGE exposure in this evidence set; other anomaly types may still require review.'
    if name == 'BOUNDARY DRIFT':
        return {
            'REJECTED_INTERACTION': 'The finding is a BL-1 policy rejection, not a NEW_EDGE drift signal.',
            'MISSING_EDGE': 'One approved lookup was absent from this trace; it is not a new connection.',
            'VELOCITY_ANOMALY': 'The version mismatch came from controlled testing, not a new-edge finding.',
        }[signal_type]
    if signal_type == 'REJECTED_INTERACTION':
        return 'Validated Nov. 17 workflow snapshot, not the current rolling measurement.'
    if signal_type == 'VELOCITY_ANOMALY':
        return 'Not measured for this event. The detected interaction rate is a different metric.'
    return 'No verified workflow-token measurement for this selected event.'


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


def graph_mermaid(scenario_key, focus_event=True):
    """Approved rectangular Mermaid design. Edge styling reflects event-specific evidence."""
    graph = data['level_1']['graph']
    edges = graph['edges']
    mode = scenarios[scenario_key]['graph_rendering']['anomaly_type']
    if focus_event:
        # Level 2: show the relevant local neighborhood, not every baseline edge.
        # For the selected customer-service event, keep its policy lookup, model, and payout paths.
        selected_agent = scenarios[scenario_key]['agent']
        selected_target = scenarios[scenario_key]['evidence']['target']
        edges = [e for e in edges if (e['source'] == selected_agent and
                 (mode == 'REJECTED_INTERACTION' or e['target'] == selected_target))]

    incident = scenarios[scenario_key]['incident']
    # The graph is the current v2 approved baseline plus the selected live rejected edge.
    triples = [(e['source'], e['relationship'], e['target']) for e in edges]
    entities = sorted({x for a, _, b in triples for x in (a, b)})
    node_ids = {name: f'N{i}' for i, name in enumerate(entities)}
    lines = ['flowchart LR']
    for name, nid in node_ids.items():
        label = nice_entity(name).replace('"', "'").replace('\n', ' ')
        lines.append(f'{nid}["{label}"]')
    green, orange, grey, muted = [], [], [], []
    for idx, e in enumerate(edges):
        source, rel, target = triples[idx]
        if e['approved'] is False and e.get('review_status') == 'POLICY_REJECTED':
            if mode == 'REJECTED_INTERACTION':
                rel_label = 'REJECTED / BL-1'
                orange.append(idx)
            else:
                rel_label = 'OTHER EVENT / REJECTED'
                muted.append(idx)
        elif e.get('missing_in_selected_trace') and mode in ('REJECTED_INTERACTION', 'MISSING_EDGE'):
            # This expected policy lookup is not observed in the selected customer-service trace.
            rel_label = 'MISSING / EXPECTED NOT OBSERVED'
            grey.append(idx)
        elif mode == 'VELOCITY_ANOMALY' and e.get('velocity_anomaly_event_id') == incident:
            rel_label = 'CALLS_TOOL / VELOCITY ANOMALY'
            orange.append(idx)
        else:
            rel_label = str(rel)
            green.append(idx)
        safe_relation = rel_label.replace('"', "'")
        lines.append(f'{node_ids[source]} -->|"{safe_relation}"| {node_ids[target]}')
    if green:
        lines.append('linkStyle '+','.join(map(str,green))+' stroke:#65a78b,stroke-width:2px;')
    if orange:
        lines.append('linkStyle '+','.join(map(str,orange))+' stroke:#ff951f,stroke-width:4px;')
    if grey:
        lines.append('linkStyle '+','.join(map(str,grey))+' stroke:#91959f,stroke-width:3px,stroke-dasharray:5 5;')
    if muted:
        lines.append('linkStyle '+','.join(map(str,muted))+' stroke:#637082,stroke-width:1.5px;')
    lines.append('classDef default fill:#10141c,stroke:#677080,color:#f2f2f2;')
    return '\n'.join(lines)


def render_mermaid(key, focus_event=True):
    """Render Mermaid explicitly; show the same edges if its CDN is unavailable."""
    code = graph_mermaid(key, focus_event=focus_event)
    mode = scenarios[key]['graph_rendering']['anomaly_type']
    edges = data['level_1']['graph']['edges']
    if focus_event:
        selected_agent = scenarios[key]['agent']
        selected_target = scenarios[key]['evidence']['target']
        edges = [e for e in edges if e['source'] == selected_agent and
                 (mode == 'REJECTED_INTERACTION' or e['target'] == selected_target)]
    fallback_rows = []
    for e in edges:
        if e['approved'] is False and e.get('review_status') == 'POLICY_REJECTED':
            state = 'REJECTED / BL-1' if mode == 'REJECTED_INTERACTION' else 'OTHER REJECTED EVENT'
            accent = '#ff951f' if mode == 'REJECTED_INTERACTION' else '#637082'
        elif e.get('missing_in_selected_trace') and mode in ('REJECTED_INTERACTION', 'MISSING_EDGE'):
            state, accent = 'MISSING / EXPECTED', '#b1b4bd'
        elif mode == 'VELOCITY_ANOMALY' and e.get('velocity_anomaly_event_id') == scenarios[key]['incident']:
            state, accent = 'VELOCITY ANOMALY', '#ff951f'
        else:
            state, accent = e['relationship'], '#65a78b'
        source = html_lib.escape(nice_entity(e['source']))
        target = html_lib.escape(nice_entity(e['target']))
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
                          format_func=lambda k: SCENARIO_GUIDE[scenarios[k]['graph_rendering']['anomaly_type']]['short_name'])
    if chosen != st.session_state.selected_scenario:
        st.session_state.selected_scenario = chosen
        st.session_state.view_level = 1
        st.rerun()
    if st.session_state.view_level == 2:
        if st.button('← Back to overview', width='stretch'):
            st.session_state.view_level = 1
            st.rerun()
    st.info('Validated live sandbox evidence · Not a production incident.')
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
        'MISSING_EDGE': 'Expected lookup missing · Review required',
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
        st.caption('Hover over each KRI label for its original calculation definition.')

    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.4, 1], gap='large')
    with left:
        st.subheader('Connection to review')
        render_mermaid(key, focus_event=True)
        if signal_type == 'REJECTED_INTERACTION':
            st.caption('Orange: policy-rejected payout connection · Green: approved connection · Gray dashed: expected lookup missing from this trace')
        elif signal_type == 'MISSING_EDGE':
            st.caption('Gray dashed: approved connection not observed in this trace')
        else:
            st.caption('Orange: approved tool connection with an unusual interaction rate; not a NEW_EDGE')
        st.button('Investigate this event →', type='primary', width='stretch',
                  on_click=lambda: st.session_state.update(view_level=2))
        with st.expander('View full interaction graph (all approved connections)'):
            st.caption('Full approved topology is available as additional context. It is not the selected event trace.')
            render_mermaid(key, focus_event=False)
            st.caption('Green: approved baseline · Orange: selected flagged activity · Gray dashed: expected but missing · Muted: separate event')
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
    event = detail['selected_event']
    st.markdown('<span class="pill">EVENT-LEVEL EVIDENCE</span>', unsafe_allow_html=True)
    # Executive summary comes before the technical identifiers.
    st.subheader('What happened?')
    st.write(guide['what'])
    st.subheader('Why was it flagged?')
    st.write(guide['why'])
    st.subheader('What is still unknown?')
    st.write(guide['unknown'])
    if signal_type == 'REJECTED_INTERACTION':
        st.caption('ML Tier 2: MEDIUM composite risk; intent UNCERTAIN. '
                   'The runtime ALLOW context does not override the DE2 BL-1 rejection.')
    elif signal_type == 'VELOCITY_ANOMALY':
        st.caption('The temporary test topology was v3; the current approved sandbox is v2.')
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
            st.caption(kri_explanation(signal_type, name))

    st.markdown('<div class="block-gap"></div>', unsafe_allow_html=True)
    a, b = st.columns([1.45, 1])
    with a:
        # Level 2 adds event-specific investigation evidence instead of repeating
        # the Level 1 relationship graph. All values come from the ML handoff.
        st.subheader('Event Evidence Trail')
        st.markdown('**Source agent**')
        st.write(nice_entity(event['source_entity_id']))
        st.markdown('**Relationship / target**')
        st.write(event['relationship_type'] + ' → ' + nice_entity(event['target_entity_id']))
        if signal_type == 'REJECTED_INTERACTION':
            context = detail['backend_processing']['runtime_context']
            observed = context['observed_action']
            st.markdown('**Observed tool action**')
            st.write(observed['operation'] + ' · ' + observed['tool'].replace('_', ' '))
            st.markdown('**Declared responsibility**')
            st.write(detail['selected_event']['declared_purpose'])
            st.error('Policy rejection · ' + str(detail['backend_processing']['tier1_evidence']['policy_id']))
            st.caption('The backend reported a rejected interaction. A completed payout or transfer is not confirmed.')
        elif signal_type == 'MISSING_EDGE':
            st.markdown('**Expected behavior**')
            st.write('Approved policy-status lookup should appear in the selected trace.')
            st.markdown('**Observed trace result**')
            st.warning('Expected connection not observed · MISSING_EDGE')
            st.caption('The reason for the missing relationship has not been established.')
        else:
            v = scenario['evidence']['interaction_velocity']
            c1, c2, c3 = st.columns(3)
            c1.metric('RECORDED RATE', f"{v['current_rate']:g}")
            c2.metric('BASELINE', f"{v['baseline_rate']:.2f}")
            c3.metric('THRESHOLD', f"{v['threshold']:g}")
            st.warning(f"Interaction-rate anomaly · {v['window_minutes']:g}-minute monitoring window")
            st.caption('This is DE2 interaction activity, not LLM Token Velocity.')
            st.caption('Event topology: ' + scenario['evidence']['event_topology_version'])
            st.caption('Current topology: ' + scenario['evidence']['current_topology_version'])
        st.caption('Event-specific evidence from the validated ML handoff; no new connections or metrics were inferred.')
    with b:
        st.subheader('Evidence Signals')
        st.markdown('**Agent:** ' + nice_entity(event['source_entity_id']))
        st.markdown('**Target:** ' + nice_entity(event['target_entity_id']))
        st.markdown('**Detected signal:** ' + event['signal_type'])
        tier1 = detail.get('backend_processing', {}).get('tier1_evidence', {})
        processing = detail.get('backend_processing', {})
        tier2_status = processing.get('tier2_execution_status', processing.get('status', 'Not supplied'))
        st.markdown('**Tier 1 flagged:** ' + ('Yes' if tier1.get('tier1_flagged') else 'No'))
        st.markdown('**Tier 2 status:** ' + str(tier2_status).replace('_', ' ').title())
        if signal_type == 'REJECTED_INTERACTION':
            st.markdown('**Policy finding:** REJECTED / BL-1')
            st.caption('Direct incident scope: 1 agent / 1 target. This is not the NEW_EDGE Blast Radius KRI.')
        elif signal_type == 'MISSING_EDGE':
            st.caption('The expected lookup connection is missing from the selected trace.')
        else:
            st.caption('Velocity event generated under a controlled temporary topology.')
        st.caption('No automatic containment action is asserted.')

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
    st.caption('The controlled velocity event used temporary v3 topology; it is not the current baseline.')
# Do not display the full handoff in participant mode: it includes evaluator-only
# recommended decisions. Keep the validated source JSON in the app directory.

