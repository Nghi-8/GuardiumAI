"""GuardiumOne — JSON-driven executive risk dashboard (product demonstration).

Run: streamlit run guardiumone_dashboard.py
Keep guardiumone_dashboard_data.json beside this file.

The Python renders the UI. The JSON supplies validated ML results, presentation
configuration, scenario-specific explanations and the recommended next step.
No new ML model calls, inference, or risk calculations are performed.
"""
from pathlib import Path
import html
import json
import re

import streamlit as st
import streamlit.components.v1 as components

DATA_FILE = Path(__file__).with_name('guardiumone_dashboard_data.json')
st.set_page_config(page_title='GuardiumOne | Executive Risk Console',
                   layout='wide', page_icon='🛡️')

st.markdown('''
<style>
.stApp{background:#07090e;color:#f1f1ef}
[data-testid="stSidebar"]{background:#10141c}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.7rem}
.scenario-position{margin:4px 0 0;color:#87b9e7;font-size:.78rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase}
.sidebar-steps{list-style:none;counter-reset:steps;margin:0;padding:0}
.sidebar-steps li{counter-increment:steps;position:relative;padding:8px 0 8px 34px;line-height:1.45;font-size:.92rem;color:#cbd5df}
.sidebar-steps li::before{content:counter(steps);position:absolute;left:0;top:8px;width:23px;height:23px;border-radius:50%;display:grid;place-items:center;background:#202f40;border:1px solid #394c62;color:#99c5eb;font-weight:600;font-size:.75rem}
.sidebar-steps li:last-child{font-weight:700;color:#f4f6f9}
[data-testid="stMetric"]{background:#121824;border:1px solid #354154;padding:15px 16px;border-radius:9px;min-height:116px;border-top:2px solid #7eacd6}
[data-testid="stMetricLabel"]{color:#cbd5e3;font-weight:600}
[data-testid="stMetricLabel"] p{white-space:normal!important;overflow-wrap:anywhere}
[data-testid="stMetricValue"]{color:#f1d29a;font-size:clamp(1.12rem,2.1vw,1.85rem);line-height:1.24;font-weight:600;font-variant-numeric:tabular-nums}
[data-testid="stMetricValue"] *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}
[data-testid="stMarkdownContainer"] p{line-height:1.55}
[data-testid="stCaptionContainer"] p{color:#a8b4c4;line-height:1.45}
h1,h2,h3{letter-spacing:-.025em}
[data-testid="stMainBlockContainer"] h2{margin-top:.55rem}
[data-testid="stMainBlockContainer"] h3{margin-top:.45rem}
.kri-note{font-size:.9rem;line-height:1.45;color:#b5c1cf;margin:3px 0 7px}
.kri-technical{font-size:.76rem;letter-spacing:.04em;color:#9fadc0;text-transform:uppercase;margin:2px 0}
 .overview-panel{border:1px solid #354151;border-top:3px solid #87b9e7;background:#151b24;color:#f1f1ef;border-radius:10px;padding:18px 20px;margin:10px 0 18px}
.overview-panel h3{margin:0 0 4px;color:#d3e8ff;font-size:1.25rem}
.overview-panel .ov-subtitle{color:#adb7c6;margin:0 0 14px;font-size:.91rem}
 .ov-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 18px}
.behavior-panel{border:1px solid #3b4653;border-top:3px solid #82c8a4;background:#182721;border-radius:8px;padding:13px 15px;margin:8px 0 2px;min-width:0}
.behavior-panel.actual{background:#2b241c;border-color:#604323;border-top-color:#ffad50}
.behavior-panel.expected strong{color:#a6e0c3}
.behavior-panel.actual strong{color:#ffd19f}
.behavior-panel strong{display:block;font-size:.95rem;margin-bottom:5px}
.behavior-panel p{margin:0;line-height:1.55;overflow-wrap:anywhere}
.ov-field{border-top:1px solid #3c424c;padding:10px 0;min-width:0}
.ov-field.wide{grid-column:1/-1}
.ov-field strong,.ov-status strong,.ov-unknown strong{display:block;color:#edc492;font-size:.94rem;margin-bottom:4px}
.ov-field p,.ov-status p,.ov-unknown p{margin:0;line-height:1.55;overflow-wrap:anywhere}
.ov-status-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:12px 0}
.ov-status{background:#1e242d;border:1px solid #39424e;border-radius:6px;padding:11px;min-width:0}
.ov-status p{font-size:.94rem}
.ov-status small{color:#aeb8c7;font-size:.77rem}
.ov-status .recorded-status{font-size:1.05rem;font-weight:700;color:#f1f1ef;margin:4px 0 8px}
.ov-status .risk-explanation{font-size:.8rem;color:#aeb8c7;line-height:1.45}
.status-badge{display:inline-flex;align-items:center;gap:6px;border-radius:5px;padding:5px 8px;margin:5px 0 8px;font-weight:650;font-size:.8rem;line-height:1.25;max-width:100%;overflow-wrap:anywhere}
.status-badge::before{content:"";width:7px;height:7px;background:currentColor;border-radius:50%;flex:none}
.status-badge.approved{color:#a6e0c3;background:#20392d;border:1px solid #3e7656}
.status-badge.flagged{color:#ffd09b;background:#39291b;border:1px solid #97672e}
.status-badge.violation{color:#ffc1c1;background:#41252a;border:1px solid #96525b}
.status-badge.unknown{color:#d0d8e5;background:#292f39;border:1px solid #505c6d}
.status-badge.context{color:#b9dcff;background:#23384c;border:1px solid #4c6b8a}
.ov-unknown{background:#22262c;border:1px solid #484e58;padding:12px;border-radius:6px;margin-top:7px}
.ov-unknown strong{color:#e1e6ed}
 .next-step{background:linear-gradient(100deg,#35291e,#28211a);border:1px solid #d39447;border-left:5px solid #ffad50;color:#f9ead6;border-radius:9px;padding:21px 23px;margin:16px 0}
.next-step h3{color:#ffca8e;font-size:1.35rem;margin:0 0 7px}
.next-step p{font-size:1.16rem;line-height:1.6;margin:0}
.context-metric{background:#141b24;border:1px solid #3b4554;border-radius:7px;padding:12px;margin:8px 0}
.context-metric strong{color:#f0d3a4}
.context-metric .context-note{color:#b5c1cf;font-size:.92rem;margin:7px 0 0}
.graph-evidence{width:100%;border-collapse:collapse;table-layout:auto;font-size:.92rem}
.graph-evidence th,.graph-evidence td{text-align:left;vertical-align:top;padding:9px 7px;border-bottom:1px solid #363c47;overflow-wrap:anywhere}
.graph-evidence th{color:#d9c09c;font-weight:600}
.graph-status{font-weight:600}
.graph-status.approved{color:#82c8a4}.graph-status.flagged{color:#ffad50}
 .graph-status.missing{color:#c0c4cf}.graph-status.other{color:#a0aaba}.graph-status.violation{color:#ff9b9b}
.graph-legend{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;margin:5px 0 8px}
.graph-chip{display:inline-flex;align-items:center;gap:7px;padding:5px 8px;border:1px solid #3a4655;border-radius:5px;background:#151d28;color:#d7dfeb;font-size:.79rem;line-height:1.4}
.graph-chip::before{content:"";width:20px;height:0;border-top:3px solid #a0aaba}
.graph-chip.approved::before{border-color:#65a78b}
.graph-chip.flagged::before{border-color:#ff951f}
.graph-chip.violation::before{border-color:#f07882}
.graph-chip.missing::before{border-color:#a0a7b2;border-top-style:dashed}
.graph-chip.other::before{border-color:#637082}
.stButton>button{border:1px solid #b97735;background:#171c25;color:#ffb05e}
@media(max-width:720px){.overview-panel{padding:13px}.ov-grid,.ov-status-row{grid-template-columns:minmax(0,1fr)}.graph-evidence{font-size:.82rem}}
</style>
''', unsafe_allow_html=True)


def stop_with_error(message):
    st.error(message)
    st.stop()


try:
    with DATA_FILE.open(encoding='utf-8-sig') as handle:
        data = json.load(handle)
    if data['handoff_status'] != 'FINAL_VALIDATED_FOR_DASHBOARD':
        raise ValueError('The source handoff is not marked as validated.')
    config = data['dashboard_presentation']
    if config['mode'] != 'PRODUCT_DEMONSTRATION':
        raise ValueError('Unsupported presentation mode.')
    scenarios = data[config['scenario_collection']]
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError('No configured scenarios were supplied.')
    if config['scenario_collection'] != data['display_contract']['scenario_collection_for_existing_streamlit_pattern']:
        raise ValueError('Scenario collection does not match the ML display contract.')
except (OSError, ValueError, KeyError, TypeError) as exc:
    stop_with_error(f'Cannot load dashboard data: {exc}. Keep {DATA_FILE.name} beside this script.')

MISSING = 'Not supplied'
ESC = lambda value: html.escape(str(value))


def read_path(obj, path, default=None):
    """Read a dotted or explicit list path without evaluating user-provided code."""
    parts = path.split('.') if isinstance(path, str) else path
    try:
        for part in parts:
            obj = obj[part]
        return default if obj is None else obj
    except (KeyError, TypeError, IndexError):
        return default


def scenario_detail(scenario):
    """Resolve a stable JSON evidence reference, then verify incident identity."""
    ref = read_path(scenario, 'business_view.detail_ref')
    if not isinstance(ref, list) or not ref:
        raise ValueError('Scenario is missing a detail_ref.')
    detail = read_path(data, ref)
    if not isinstance(detail, dict):
        raise ValueError('The configured evidence reference does not exist.')
    primary = detail.get('selected_event') or detail.get('primary_event')
    if not isinstance(primary, dict) or primary.get('event_id') != scenario.get('incident'):
        raise ValueError('The configured event reference does not match the scenario incident ID.')
    return detail, primary


def validate_scenario(scenario):
    view = scenario['business_view']
    for field in config['overview_fields'] + config['overview_status_fields'] + config['reviewer_fields']:
        if not isinstance(read_path(view, field['field']), str):
            raise ValueError(f"Missing presentation field: {field['field']}")
    for field in ('business_title', 'scenario_label', 'recommended_next_step'):
        if not isinstance(view.get(field), str) or not view[field].strip():
            raise ValueError(f'Missing presentation field: {field}')
    for spec in config['kri_cards']:
        if spec['key'] not in scenario['kri_details']:
            raise ValueError(f"Missing validated metric: {spec['key']}")
    scenario_detail(scenario)


try:
    for scenario in scenarios.values():
        validate_scenario(scenario)
except (KeyError, TypeError, ValueError) as exc:
    stop_with_error(f'Dashboard presentation contract is incomplete: {exc}')


def entity_label(identifier):
    known = config.get('entity_labels', {}).get(identifier)
    if known:
        return known
    identifier = str(identifier)
    if identifier.startswith('tool:'):
        return identifier.rsplit(':', 1)[-1].replace('_', ' ').capitalize()
    if identifier.startswith('model:'):
        return identifier.split(':', 2)[-1] + ' (model)'
    return identifier.replace('_', ' ')


def display_metric(spec, metric, scenario):
    """Format validated evidence without substituting another KRI or making up counts."""
    status = metric.get('status')
    if status in ('NOT_MEASURED', 'NOT_ASSESSED'):
        return config.get('display_statuses', {}).get(status, status.replace('_', ' ').capitalize())
    raw = metric.get('display')
    if raw is None:
        raw = read_path(scenario, ['risk_data', spec['legacy_key']], MISSING)
    raw = str(raw)
    translated = config.get('display_translations', {}).get(raw)
    if translated:
        return translated
    if spec.get('format') == 'scope':
        # Accept any validated agent/target counts, not just 0/0 or 1/1.
        match = re.fullmatch(r'(\d+) agents? / (\d+) targets?', raw, re.I)
        if match:
            agents, targets = map(int, match.groups())
            return f"{agents} agent{'s' if agents != 1 else ''} / {targets} resource{'s' if targets != 1 else ''}"
    elif spec.get('format') == 'connection_changes':
        match = re.fullmatch(r'(\d+) new edges? / (\d+) missing edges?', raw, re.I)
        if match:
            new, missing = map(int, match.groups())
            return f'{new} unexpected / {missing} not observed'
    return raw


def render_kri_cards(scenario):
    """Loop over common KRI definitions; individual values always come from ML."""
    view = scenario['business_view']
    definitions = config['kri_cards']
    st.subheader('Executive Risk Indicators (KRIs)')
    for column, spec in zip(st.columns(len(definitions)), definitions):
        metric = scenario['kri_details'][spec['key']]
        with column:
            st.metric(spec['label'], display_metric(spec, metric, scenario),
                      help=f"{spec['technical_label']}: {spec['definition']}")
            full_context = view.get('kri_context', {}).get(spec['key'], metric.get('basis', MISSING))
            short_context = view.get('kri_context_short', {}).get(spec['key'], full_context)
            st.markdown('<div class="kri-technical">' + ESC(spec['technical_label'])
                        + '</div><div class="kri-note">' + ESC(short_context) + '</div>',
                        unsafe_allow_html=True)
            if metric.get('snapshot_label'):
                st.caption(metric['snapshot_label'])
    with st.expander('Technical KRI definitions and measurement scope'):
        for spec in definitions:
            metric = scenario['kri_details'][spec['key']]
            st.markdown(f"**{spec['technical_label']}**")
            st.write(spec['definition'])
            full_context = view.get('kri_context', {}).get(spec['key'])
            if full_context:
                st.write(full_context)
            st.caption('Original measurement: ' + str(metric.get('display', MISSING)))
            if metric.get('basis'):
                st.caption(metric['basis'])


def decision_badge(scenario):
    """Presentation status uses explicit backend evidence, not the scenario name."""
    evidence = scenario.get('evidence', {})
    policy = str(evidence.get('policy_status') or '').upper()
    if policy == 'REJECTED':
        return 'Policy rejection recorded', 'violation'
    if evidence.get('policy_violation') is True:
        return 'Policy violation flagged', 'violation'
    if evidence.get('tier1_flagged') is True:
        return 'Review required', 'flagged'
    if policy in ('APPROVED', 'AUTHORIZED', 'ALLOWED'):
        return 'Approved by policy', 'approved'
    return 'Decision not supplied', 'unknown'


def risk_badge(scenario):
    """Never convert Tier 1 policy severity into a composite risk rating."""
    evidence = scenario.get('evidence', {})
    level = str(evidence.get('composite_risk_level') or '').upper()
    colors = {'LOW':'approved', 'MEDIUM':'flagged', 'HIGH':'violation', 'CRITICAL':'violation'}
    if level in colors:
        return level.title() + ' composite risk', colors[level]
    return 'Composite risk not assessed', 'unknown'


def badge_html(label, tone):
    return '<span class="status-badge ' + ESC(tone) + '">' + ESC(label) + '</span>'


def render_overview(scenario):
    """Scenario content remains in the JSON; layout and badge styles are reusable."""
    view = scenario['business_view']
    fields = config['overview_fields']

    def item(field, classes='ov-field'):
        value = read_path(view, field['field'], MISSING)
        raw_path = field.get('technical_ref')
        raw = read_path(scenario, raw_path) if raw_path else None
        raw_line = f'<p><small>Recorded status: {ESC(raw)}</small></p>' if raw is not None else ''
        badge = ''
        if field['field'] == 'system_decision_business':
            badge = badge_html(*decision_badge(scenario))
        elif field['field'] == 'risk_summary':
            badge = badge_html(*risk_badge(scenario))
            recorded_status = (
                f'<p class="recorded-status">Recorded status: {ESC(raw)}</p>'
                if raw is not None else ''
            )
            return (
                f'<div class="{classes}">'
                f'<strong>{ESC(field["label"])}</strong>'
                f'{badge}{recorded_status}'
                f'<p class="risk-explanation">{ESC(value)}</p>'
                f'</div>'
            )
        return f'<div class="{classes}"><strong>{ESC(field["label"])}</strong>{badge}<p>{ESC(value)}</p>{raw_line}</div>'

    opening = ''.join(
        item(field, 'behavior-panel expected' if field['field'] == 'expected_behavior'
             else 'behavior-panel actual' if field['field'] == 'reviewer_context.observed_action'
             else 'ov-field wide')
        for field in fields[:3]
    )
    statuses = ''.join(item(field, 'ov-status') for field in config['overview_status_fields'])
    closing = ''.join(item(field, 'ov-field wide') for field in fields[3:-1])
    last = item(fields[-1], 'ov-unknown')
    st.markdown(
        '<section class="overview-panel" aria-label="Scenario overview">'
        '<h3>Scenario Overview</h3><p class="ov-subtitle">Understand the event and its business implications</p>'
        f'<div class="ov-grid">{opening}</div><div class="ov-status-row">{statuses}</div>'
        f'<div class="ov-grid">{closing}</div>{last}</section>',
        unsafe_allow_html=True,
    )


def render_context_metrics(scenario):
    """Optional event measurements belong beside scenario evidence, never in another KRI."""
    for spec in config.get('context_metrics', []):
        metric = scenario['kri_details'].get(spec['key'])
        if not isinstance(metric, dict):
            continue
        cells = []
        for item in spec['fields']:
            value = metric.get(item['key'])
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                value = format(value, item.get('format', 'g')) + item.get('suffix', '')
            elif value is None:
                value = MISSING
            cells.append(f'{ESC(item["label"])}: <strong>{ESC(value)}</strong>')
        st.markdown('<div class="context-metric"><strong>' + ESC(spec['title'])
                    + '</strong><p>' + ' &nbsp;·&nbsp; '.join(cells)
                    + '</p><p class="context-note">' + ESC(spec.get('note', '')) + '</p></div>',
                    unsafe_allow_html=True)


def pair(edge):
    return edge['source'], edge['target']


def graph_state_info(state):
    states = config['graph_states']
    return states.get(state, states['UNCLASSIFIED'])


def graph_relationships(scenario, focus=False):
    """Use actual graph edges and validated selected-scenario states, not inferred events."""
    full = data['level_1']['graph']['edges']
    graph = scenario['graph_rendering']
    explicit = {pair(e): e for e in graph.get('edge_states', [])}
    approved = {tuple(e) for e in scenario.get('approved', [])}
    observed = {tuple(e) for e in scenario.get('observed', [])}
    current_pair = (scenario.get('agent'), scenario.get('evidence', {}).get('target'))
    focus_pairs = approved | observed | set(explicit)
    if not focus_pairs and all(current_pair):
        focus_pairs.add(current_pair)
    rows = [dict(e) for e in full if not focus or pair(e) in focus_pairs]
    if focus:
        existing = {pair(e) for e in rows}
        # A compatible new scenario can declare a validated pair not in the full graph.
        # This uses the supplied approved/observed relationships; no edges are invented.
        for source, target in sorted(focus_pairs - existing):
            rows.append({'source': source, 'target': target, 'approved': (source,target) in approved})
    result = []
    for edge in rows:
        key = pair(edge)
        if key in explicit:
            state = explicit[key]['state']
            technical_label = explicit[key].get('label', state)
        elif key == current_pair and graph.get('edge_state'):
            state = graph['edge_state']
            technical_label = graph.get('edge_label', state)
        elif focus and key in approved and key in observed:
            state, technical_label = 'APPROVED_AND_OBSERVED', 'APPROVED + OBSERVED'
        elif focus and key in approved:
            state, technical_label = 'APPROVED_BASELINE_NOT_OBSERVED_IN_SELECTED_TRACE', 'APPROVED BASELINE / NOT OBSERVED'
        elif edge.get('approved') is False:
            state, technical_label = ('UNCLASSIFIED', 'STATUS NOT SUPPLIED') if focus else ('OTHER_VALIDATED_EVENT', 'OTHER VALIDATED EVENT')
        elif edge.get('approved') is True:
            state, technical_label = 'APPROVED_BASELINE', 'APPROVED BASELINE'
        else:
            state, technical_label = 'UNCLASSIFIED', 'STATUS NOT SUPPLIED'
        info = graph_state_info(state)
        result.append({**edge, 'state':state, 'technical_label':technical_label,
                       'label':info['label'], 'meaning':info['meaning'], 'style':info['style']})
    return result


def mermaid_code(rows):
    """Mermaid graph from the same relationship list as the local fallback."""
    ids = {n:f'N{i}' for i,n in enumerate(sorted({x for r in rows for x in (r['source'],r['target'])}))}
    def clean(text):
        return str(text).replace('"', "'").replace('\n',' ').replace('<','(').replace('>',')')
    lines = ['flowchart LR']
    for node, ident in ids.items():
        lines.append(f'{ident}["{clean(entity_label(node))}"]')
    styles = {'approved':[], 'flagged':[], 'violation':[], 'missing':[], 'other':[]}
    for index, row in enumerate(rows):
        label = clean(row['label'])
        lines.append(f'{ids[row["source"]]} -->|"{label}"| {ids[row["target"]]}')
        styles.get(row['style'], styles['other']).append(index)
    colors = {'approved':'stroke:#65a78b,stroke-width:2px;',
              'flagged':'stroke:#ff951f,stroke-width:4px;',
              'violation':'stroke:#f07882,stroke-width:4px;',
              'missing':'stroke:#a0a7b2,stroke-width:3px,stroke-dasharray:5 5;',
              'other':'stroke:#637082,stroke-width:1.5px;'}
    for style, indices in styles.items():
        if indices:
            lines.append('linkStyle ' + ','.join(map(str,indices)) + ' ' + colors[style])
    lines.append('classDef default fill:#10141c,stroke:#677080,color:#f2f2f2;')
    return '\n'.join(lines)


def render_graph(rows, height=450, *, fit_to_panel=False):
    """Render the full overview without an inner scrollbar; preserve the focused view."""
    colors = {'approved':'#82c8a4','flagged':'#ffad50','violation':'#ff9b9b','missing':'#c0c4cf','other':'#9ca8bc'}
    fallback = ''.join(
        f'<div class="edge-row"><div class="node">{ESC(entity_label(r["source"]))}</div>'
        f'<div class="edge" style="color:{colors.get(r["style"],colors["other"])}">→<small>{ESC(r["label"])}</small></div>'
        f'<div class="node">{ESC(entity_label(r["target"]))}</div></div>'
        for r in rows) or '<p>No graph relationships supplied.</p>'
    js_code = json.dumps(mermaid_code(rows)).replace('</','<\\/')
    fit_css = '''
      html,body{width:100%;height:100%;margin:0;overflow:hidden}
      #graph-viewport{position:relative;box-sizing:border-box;width:100%;height:100%;padding:5px;overflow:hidden}
      #fallback{position:absolute;left:50%;top:50%;box-sizing:border-box;width:calc(100% - 10px);
          transform:translate(-50%,-50%);transform-origin:center center;
          grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 14px;align-content:center}
      #fallback .edge-row{gap:5px}
      #fallback .node{padding:7px 5px;font-size:13px;line-height:1.25}
      #fallback .edge{flex-basis:98px;font-size:19px}
      #fallback .edge small{font-size:11px;line-height:1.2}
      #word-graph{width:100%;height:100%;overflow:hidden}
      #word-graph svg{display:block;width:100%!important;height:100%!important;max-width:100%!important;max-height:100%!important}
      @media(max-width:660px){#fallback{grid-template-columns:1fr;gap:4px}
          #fallback .node{padding:4px 5px;font-size:12px}
          #fallback .edge{flex-basis:100px;font-size:15px}
          #fallback .edge small{font-size:10px}}
    ''' if fit_to_panel else ''
    fit_js = '''
      const viewport = document.getElementById('graph-viewport');
      const fallback = document.getElementById('fallback');
      function fitFallback() {
        if (getComputedStyle(fallback).display === 'none') return;
        fallback.style.transform = 'translate(-50%,-50%)';
        const available = Math.max(1,viewport.clientHeight - 12);
        const natural = Math.max(1,fallback.offsetHeight);
        const scale = Math.min(1,available / natural);
        fallback.style.transform = 'translate(-50%,-50%) scale(' + scale + ')';
      }
      fitFallback();
      if (typeof ResizeObserver !== 'undefined') {
        new ResizeObserver(fitFallback).observe(viewport);
      }
      window.addEventListener('resize',fitFallback);
    ''' if fit_to_panel else ''
    doc = f'''<style>
      body{{background:#07090e;color:#f1f1ef;font:14px system-ui,sans-serif;margin:5px}}
      #fallback{{display:grid;gap:8px;padding:3px}}
      .edge-row{{display:flex;align-items:center;gap:8px;min-width:0}}
      .node{{background:#141b25;border:1px solid #566172;border-radius:6px;padding:9px 7px;flex:1;min-width:0;text-align:center;overflow-wrap:anywhere}}
      .edge{{flex:0 0 112px;display:flex;align-items:center;flex-direction:column;font-size:23px}}
      .edge small{{font-size:11px;text-align:center;line-height:1.3}}
      #word-graph{{display:none}} #word-graph svg{{width:100%!important;max-width:100%!important;height:auto!important}}
      @media(max-width:450px){{.edge{{flex-basis:85px}}.node{{font-size:12px}}}}
      {fit_css}
    </style><div id="graph-viewport"><div id="fallback">{fallback}</div><div id="word-graph"></div></div>
    <script type="module">
    {fit_js}
    const source = {js_code};
    try {{
      const m = await import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs');
      const mermaid = m.default;
      mermaid.initialize({{startOnLoad:false,theme:'dark',securityLevel:'strict',
        flowchart:{{htmlLabels:false,nodeSpacing:30,rankSpacing:65,useMaxWidth:true}},
        themeVariables:{{background:'#07090e',primaryColor:'#10141c',primaryTextColor:'#eee'}}}});
      const node = document.getElementById('word-graph');
      node.style.display = 'block'; node.textContent = source;
      await mermaid.run({{nodes:[node]}});
      const svg = node.querySelector('svg');
      if (!svg) throw new Error('No SVG');
      if ({str(fit_to_panel).lower()}) {{
        // Preserve the graph's aspect ratio and fit both dimensions so no
        // relationship is clipped by the iframe's viewport.
        svg.setAttribute('preserveAspectRatio','xMidYMid meet');
        if (!svg.getAttribute('viewBox')) {{
          const bounds = svg.getBBox();
          if (bounds.width > 0 && bounds.height > 0) {{
            svg.setAttribute('viewBox', [bounds.x,bounds.y,bounds.width,bounds.height].join(' '));
          }}
        }}
      }}
      document.getElementById('fallback').style.display = 'none';
    }} catch (error) {{
      document.getElementById('word-graph').style.display = 'none';
      document.getElementById('fallback').style.display = 'grid';
      if (typeof fitFallback === 'function') fitFallback();
    }}
    </script>'''
    components.html(doc, height=height, scrolling=not fit_to_panel)
    states = list(dict.fromkeys(row['state'] for row in rows))
    legend_items = [graph_state_info(state) for state in states]
    if legend_items:
        chips = ''.join(
            '<span class="graph-chip ' + ESC(item['style']) + '" title="' + ESC(item['meaning'])
            + '">' + ESC(item['label']) + '</span>' for item in legend_items
        )
        st.markdown('<div class="graph-legend" aria-label="Graph legend">' + chips + '</div>',
                    unsafe_allow_html=True)
        with st.expander('Graph legend definitions'):
            for item in legend_items:
                st.write(item['label'] + ': ' + item['meaning'])


def render_graph_evidence(rows, scenario):
    view = scenario['business_view']
    plain = read_path(view, 'graph_details.plain_summary')
    if plain:
        st.caption(plain)
    body = ''.join(
        '<tr><td>' + ESC(entity_label(r['source'])) + ' → ' + ESC(entity_label(r['target']))
        + '</td><td>' + ESC(r['meaning']) + '</td><td><span class="graph-status ' + ESC(r['style'])
        + '">' + ESC(r['label']) + '</span><br><small>' + ESC(r['technical_label'])
        + '</small></td></tr>' for r in rows)
    st.markdown('<table class="graph-evidence"><thead><tr><th>Interaction</th>'
                '<th>Meaning</th><th>Status</th></tr></thead><tbody>' + body
                + '</tbody></table>', unsafe_allow_html=True)


def render_recommendation(scenario):
    view = scenario['business_view']
    text = view['recommended_next_step']
    # Product demonstration explicitly displays decision support; never reveal
    # scenario.decision or evaluator-only ground truth.
    st.markdown('<section class="next-step" aria-label="Recommended next step">'
                '<h3>Recommended Next Step</h3><p>' + ESC(text) + '</p></section>',
                unsafe_allow_html=True)


def render_reviewer_context(view):
    st.subheader('Reviewer Context')
    for field in config['reviewer_fields']:
        st.markdown(f"**{field['label']}**")
        st.write(read_path(view, field['field'], MISSING))


def render_investigation_findings(view, detail):
    quality = view.get('evidence_quality', {})
    if quality.get('summary'):
        st.write(quality['summary'])
    for item in quality.get('items', []):
        st.markdown(f"**{item.get('label', MISSING)} — {item.get('status', MISSING)}**")
        st.write(item.get('explanation', MISSING))
    st.subheader('Technical details')
    # Read actual backend processing, not the duplicated summary in business_view.
    processing = detail.get('backend_processing', {})
    stages = [('Selected event', processing)] if 'tier1_evidence' in processing else [
        (key.replace('_', ' ').title(), value)
        for key, value in processing.items()
        if isinstance(value, dict) and 'tier1_evidence' in value
    ]
    if not stages:
        st.caption('No structured backend-processing details supplied. See Event Evidence.')
    for label, stage in stages:
        st.markdown(f'**{label}**')
        tier1 = stage.get('tier1_evidence', {})
        trigger = stage.get('tier2_trigger', {})
        status = stage.get('tier2_result_status') or stage.get('tier2_execution_status')
        handoff = stage.get('tier2_handoff', {})
        composite = handoff.get('tier2_result') or stage.get('composite_result')
        intent = handoff.get('intent_drift_result') or stage.get('intent_drift_result')
        st.write('Initial detection:', 'Flagged' if tier1.get('tier1_flagged') is True else
                 'Not flagged' if tier1.get('tier1_flagged') is False else MISSING)
        for reason in tier1.get('tier1_reasons', []):
            st.write('• ' + str(reason))
        if tier1.get('policy_id'):
            st.write('Policy reference:', tier1['policy_id'])
        for reason in trigger.get('trigger_reasons', []):
            st.write('Deeper-review trigger:', reason)
        st.write('Deeper analysis:', config.get('display_statuses', {}).get(status, status or MISSING))
        if isinstance(composite, dict):
            st.write('Composite risk:', composite.get('risk_level', MISSING))
            if composite.get('confidence') is not None:
                st.write('Reported confidence:', composite['confidence'])
        if isinstance(intent, dict):
            st.write('Intent classification:', intent.get('classification', MISSING))
        if not composite and status in ('NOT_EXECUTED_BY_DESIGN', 'AWAITING_EXPLICIT_EXECUTION'):
            st.caption('No completed composite risk assessment was supplied.')


def render_token_accounting(detail):
    """Display only selected-event accounting, without borrowing another event's data."""
    accounting = detail.get('token_accounting')
    if not isinstance(accounting, dict) or not accounting:
        st.info('Not measured for this selected event. No verified token-accounting record was provided.')
        return
    reservation = accounting.get('reservation', {})
    reconciliation = accounting.get('reconciliation', {})
    cells = st.columns(3)
    cells[0].metric('Reserved tokens', reservation.get('reserved_tokens', MISSING))
    cells[1].metric('Actual tokens', reconciliation.get('actual_tokens', reservation.get('consumed_tokens', MISSING)))
    cells[2].metric('Settlement status', str(reconciliation.get('status', reservation.get('status', MISSING))))
    st.caption('Selected-event recorded accounting, not a live rolling consumption rate.')
    st.json(accounting, expanded=False)


def set_level(level):
    st.session_state.view_level = level


# Scenario selection is based on the JSON keys and explicit event references.
scenario_keys = list(scenarios)
default_key = data['display_contract'].get('default_selected_scenario_key')
if default_key not in scenarios:
    default_key = scenario_keys[0]
if st.session_state.get('scenario_key') not in scenarios:
    st.session_state.scenario_key = default_key
if st.session_state.get('view_level') not in (1, 2):
    st.session_state.view_level = 1

with st.sidebar:
    st.title(config['brand'])
    st.caption('AgentMonitor · Executive Risk Console')
    position = scenario_keys.index(st.session_state.scenario_key) + 1
    st.markdown(f'<p class="scenario-position">Scenario {position} of {len(scenario_keys)}</p>',
                unsafe_allow_html=True)
    st.selectbox('Scenario', scenario_keys, key='scenario_key',
                 format_func=lambda k: k.split(' · ', 1)[0] + ' · ' + scenarios[k]['business_view']['scenario_label']
                 if ' · ' in k else scenarios[k]['business_view']['scenario_label'],
                 on_change=set_level, args=(1,), label_visibility='collapsed')
    st.divider()
    st.subheader('How to Use')
    instructions = config['instructions']
    items = ''.join('<li>' + ESC(instruction) + '</li>' for instruction in instructions)
    st.markdown('<ol class="sidebar-steps">' + items + '</ol>', unsafe_allow_html=True)
    if st.session_state.view_level == 2:
        st.button('← Back to overview', use_container_width=True, on_click=set_level, args=(1,))

key = st.session_state.scenario_key
scenario = scenarios[key]
view = scenario['business_view']
detail, primary = scenario_detail(scenario)
st.caption('ENTERPRISE AI GOVERNANCE / VALIDATED SANDBOX')

if st.session_state.view_level == 1:
    st.caption('PAGE 1 / EXECUTIVE OVERVIEW')
    st.title('AI Risk Overview')
    st.subheader(view['business_title'])
    render_overview(scenario)
    render_context_metrics(scenario)
    st.subheader('Expected vs. Actual AI Behavior')
    st.caption('Full approved workflow with validated flagged connections. This is not a complete record of the selected event.')
    render_graph(graph_relationships(scenario, focus=False), height=560, fit_to_panel=True)
    st.button('Investigate Event →', type='primary', use_container_width=True, on_click=set_level, args=(2,))
    st.divider()
    render_kri_cards(scenario)
    render_recommendation(scenario)
else:
    st.caption('PAGE 2 / EVENT INVESTIGATION')
    st.title('Event Investigation')
    st.subheader(view['business_title'])
    render_reviewer_context(view)
    st.divider()
    left, right = st.columns([1.12, 1], gap='large')
    rows = graph_relationships(scenario, focus=True)
    with left:
        st.subheader('Event-specific Graph')
        render_graph(rows, height=330)
    with right:
        st.subheader('Graph Evidence')
        render_graph_evidence(rows, scenario)
    with st.expander('Investigative Findings / Technical Details'):
        render_investigation_findings(view, detail)
    with st.expander('Token Accounting'):
        render_token_accounting(detail)
    with st.expander('Event Evidence / JSON'):
        st.caption('Original selected-event data from the validated ML handoff.')
        st.json(detail, expanded=False)
        st.download_button('Export selected event evidence',
                           json.dumps(detail, ensure_ascii=False, indent=2),
                           file_name=f'{scenario["incident"]}_evidence.json', mime='application/json')
    st.button('← Back to Overview', use_container_width=True, on_click=set_level, args=(1,))

with st.expander('Data provenance'):
    st.write('ML handoff revision:', data['handoff_revision'])
    st.write('Presentation version:', config['version'])
    st.write('Evidence source:', read_path(scenario, 'evidence.source', data.get('source', MISSING)))
    st.write('Current approved workflow:', read_path(data, 'current_environment.current_topology_version', MISSING))
    st.caption('Historical sandbox validation, not production incidents or the full telemetry stream. Recommendations are product decision support.')
