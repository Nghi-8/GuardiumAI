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
[data-testid="stMetric"]{background:#10141c;border:1px solid #303139;padding:14px;border-radius:8px;min-height:106px}
[data-testid="stMetricLabel"] p{white-space:normal!important;overflow-wrap:anywhere}
[data-testid="stMetricValue"]{color:#edcd8c;font-size:clamp(.95rem,1.75vw,1.45rem);line-height:1.35}
[data-testid="stMetricValue"] *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}
[data-testid="stMarkdownContainer"] p{line-height:1.55}
[data-testid="stCaptionContainer"] p{color:#a8b4c4;line-height:1.45}
h1,h2,h3{letter-spacing:-.025em}
.overview-panel{border:1px solid #93622b;background:#15191c;color:#f1f1ef;border-radius:9px;padding:18px 20px;margin:10px 0 18px}
.overview-panel h3{margin:0 0 4px;color:#ffce94;font-size:1.25rem}
.overview-panel .ov-subtitle{color:#adb7c6;margin:0 0 14px;font-size:.91rem}
.ov-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 24px}
.ov-field{border-top:1px solid #3c424c;padding:10px 0;min-width:0}
.ov-field.wide{grid-column:1/-1}
.ov-field strong,.ov-status strong,.ov-unknown strong{display:block;color:#edc492;font-size:.94rem;margin-bottom:4px}
.ov-field p,.ov-status p,.ov-unknown p{margin:0;line-height:1.55;overflow-wrap:anywhere}
.ov-status-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:12px 0}
.ov-status{background:#1e242d;border:1px solid #39424e;border-radius:6px;padding:11px;min-width:0}
.ov-status p{font-size:.96rem}
.ov-unknown{background:#22262c;border:1px solid #484e58;padding:12px;border-radius:6px;margin-top:7px}
.ov-unknown strong{color:#e1e6ed}
.next-step{background:#302218;border:1px solid #d39447;border-left:5px solid #ff951f;color:#f9ead6;border-radius:8px;padding:19px 21px;margin:14px 0}
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
.graph-status.missing{color:#c0c4cf}.graph-status.other{color:#a0aaba}
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
            st.caption(spec['technical_label'])
            st.write(view.get('kri_context', {}).get(spec['key'], metric.get('basis', MISSING)))
            if metric.get('snapshot_label'):
                st.caption(metric['snapshot_label'])
    with st.expander('Technical KRI definitions and measurement scope'):
        for spec in definitions:
            metric = scenario['kri_details'][spec['key']]
            st.markdown(f"**{spec['technical_label']}**")
            st.write(spec['definition'])
            st.caption('Original measurement: ' + str(metric.get('display', MISSING)))
            if metric.get('basis'):
                st.caption(metric['basis'])


def render_overview(scenario):
    """The explanatory panel uses the JSON field configuration, not scenario branches."""
    view = scenario['business_view']
    fields = config['overview_fields']

    def item(field, classes='ov-field'):
        value = read_path(view, field['field'], MISSING)
        raw_path = field.get('technical_ref')
        raw = read_path(scenario, raw_path) if raw_path else None
        raw_line = f'<p><small>Recorded status: {ESC(raw)}</small></p>' if raw is not None else ''
        return f'<div class="{classes}"><strong>{ESC(field["label"])}</strong><p>{ESC(value)}</p>{raw_line}</div>'

    opening = ''.join(item(field, 'ov-field wide' if i == 0 else 'ov-field')
                      for i, field in enumerate(fields[:3]))
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
    styles = {'approved':[], 'flagged':[], 'missing':[], 'other':[]}
    for index, row in enumerate(rows):
        label = clean(row['label'])
        lines.append(f'{ids[row["source"]]} -->|"{label}"| {ids[row["target"]]}')
        styles.get(row['style'], styles['other']).append(index)
    colors = {'approved':'stroke:#65a78b,stroke-width:2px;',
              'flagged':'stroke:#ff951f,stroke-width:4px;',
              'missing':'stroke:#a0a7b2,stroke-width:3px,stroke-dasharray:5 5;',
              'other':'stroke:#637082,stroke-width:1.5px;'}
    for style, indices in styles.items():
        if indices:
            lines.append('linkStyle ' + ','.join(map(str,indices)) + ' ' + colors[style])
    lines.append('classDef default fill:#10141c,stroke:#677080,color:#f2f2f2;')
    return '\n'.join(lines)


def render_graph(rows, height=450, *, fit_to_panel=False):
    """Render the full overview without an inner scrollbar; preserve the focused view."""
    colors = {'approved':'#82c8a4','flagged':'#ffad50','missing':'#c0c4cf','other':'#9ca8bc'}
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
    states = dict.fromkeys(row['state'] for row in rows)
    legend = [f"{graph_state_info(state)['label']}: {graph_state_info(state)['meaning']}" for state in states]
    if legend:
        st.caption(' · '.join(legend))


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
    st.selectbox('Scenario', scenario_keys, key='scenario_key',
                 format_func=lambda k: k.split(' · ', 1)[0] + ' · ' + scenarios[k]['business_view']['scenario_label']
                 if ' · ' in k else scenarios[k]['business_view']['scenario_label'],
                 on_change=set_level, args=(1,))
    st.divider()
    st.subheader('Steps to Use Dashboard')
    instructions = config['instructions']
    for index, instruction in enumerate(instructions, 1):
        if index == len(instructions):
            st.markdown(f'**{index}. {instruction}**')
        else:
            st.markdown(f'{index}. {instruction}')
    st.info('Validated sandbox evidence · Not a production incident.')
    if st.session_state.view_level == 2:
        st.button('← Back to overview', use_container_width=True, on_click=set_level, args=(1,))
    st.caption('Product demonstration · Review recommendations and supporting evidence.')

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
