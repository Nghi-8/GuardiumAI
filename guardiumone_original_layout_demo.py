"""GuardiumOne client demo — Scenario 1/2 visual layout, driven by DE2 handoff files.

Run: streamlit run guardiumone_original_layout_demo.py

"""

import json
from math import isfinite

from pathlib import Path

import html as html_lib

import streamlit as st

import streamlit.components.v1 as components



ROOT = Path(__file__).parent



def load(name):

    with (ROOT / name).open(encoding='utf-8') as f:

        return json.load(f)



st.set_page_config(page_title='GuardiumOne | Executive Risk Console', layout='wide', page_icon='🛡️')

st.markdown('''<style>

.stApp{background:#07090e;color:#f1f1ef}

[data-testid="stSidebar"]{background:#10141c}

div[data-testid="stMetric"]{background:#10141c;border:1px solid #303139;padding:14px;border-radius:9px;min-height:120px;overflow:hidden}

div[data-testid="stMetricValue"]{color:#edcd8c;font-family:monospace;font-size:clamp(.9rem,1.4vw,1.3rem);line-height:1.3}

div[data-testid="stMetricValue"] *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}

h1,h2,h3{letter-spacing:-.025em}

.pill{display:inline-block;padding:5px 10px;border-radius:5px;background:#322013;color:#ff951f;font-weight:700}

.stButton>button{border:1px solid #ff951f;background:#151a23;color:#ff951f}

</style>''', unsafe_allow_html=True)



try:

    blast = load('direct_blast_radius.json')

    graph = load('graph_edges_for_dashboard.json')

    topology = load('approved_topology.json')

    summary = load('integration_summary.json')

except (OSError, ValueError) as exc:

    st.error('Cannot read the DE2 handoff files. Put the four JSON files beside this Python script.')

    st.code(str(exc))

    st.stop()



# Verify batch alignment rather than mixing datasets silently.

version = summary.get('topology_version')

if not (graph.get('topology_version') == version == blast.get('topology_version') == topology.get('schema_version')):

    st.error('The graph, metrics and baseline topology have different versions. Do not mix batches.')

    st.stop()



new_edges = [e for e in graph['edges'] if e['signal_type']=='NEW_EDGE' and e['observed']]

matched = [e for e in graph['edges'] if e['signal_type']=='MATCHED' and e['observed']]

missing = [e for e in graph['edges'] if e['signal_type']=='MISSING_EDGE']

new_triplets = {(e['source'],e['relationship'],e['target']) for e in new_edges}

if len(new_triplets) != blast['unique_new_relationship_count']:

    st.error('New relationship counts do not match the Blast Radius handoff.')

    st.stop()



# Direct Blast Radius = distinct directly targeted resources across NEW_EDGE relationships.

direct_targets = {target for _, _, target in new_triplets}

blast_radius_count = len(direct_targets)

if blast_radius_count != blast['distinct_target_count']:

    st.error('Distinct direct target count does not match the DE2 handoff.')

    st.stop()



with st.sidebar:

    st.title('GUARDIUMONE')

    st.caption('AgentMonitor · executive prototype')

    st.markdown('---')

    st.info('DEMO MODE · Synthetic DE2 batch. Not connected to production telemetry.')

    st.caption('Graph: ' + str(summary['graph_id']))

    st.caption('Proposed topology: ' + str(version))

    st.caption('Baseline approval pending · KRI definitions provisional.')

    with st.expander('Data source details'):

        st.write('Loaded from four handoff files in this folder; reload the page after replacing the batch files.')

        st.code('direct_blast_radius.json\ngraph_edges_for_dashboard.json\napproved_topology.json\nintegration_summary.json')



# Preserve EXACT section names and major column proportions of the original Scenario 1/2 view.

st.caption('ENTERPRISE AI GOVERNANCE / EXECUTIVE VIEW / DEMO')

st.title('AgentMonitor / Risk Overview')

st.warning('SYNTHETIC DE2 BATCH · Proposed topology is not formally approved. New relationships do not establish malicious behavior.')



st.markdown('<span class="pill">REVIEW · AUTHORIZATION UNCONFIRMED</span>',unsafe_allow_html=True)

st.subheader('New model relationships detected outside proposed topology')

st.caption(str(summary['graph_id'])+' · '+str(blast['affected_agent_count'])+' agents · Synthetic DE2 batch')



st.divider()

st.subheader('Four Executive KRIs')

values = [

    ('BLAST RADIUS',f'{blast_radius_count} resources'),

    ('DATA SENSITIVITY','Not available'),

    ('BOUNDARY DRIFT',f"{blast['unique_new_relationship_count']} new edges"),

    ('TOKEN VELOCITY','Not measured'),


]

# Executive KRI descriptions appear behind Streamlit's metric-label help icon.

# Definitions are independent of whether this DE2 batch contains a measurement.

KRI_HELP = {

    'BLAST RADIUS': (

        'Count of distinct resources directly targeted by NEW_EDGE relationships. '

        'Formula: count of unique target IDs across observed new relationships. '

        'Repeat signals and multiple agents targeting one resource do not increase the count. '

        'No downstream propagation or confirmed compromise is implied.'

    ),

    'DATA SENSITIVITY': (

        'Classification of the data or resource involved, using the organization’s '

        'classification policy (for example, Public, Internal, Confidential, Restricted). '

        'This DE2 handoff does not include a classification, so the value is unavailable. '

        'Unknown or unclassified must not be treated as low sensitivity.'

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

        'This insurance batch has no correlated token-usage measurement.'

    ),


}



cols = st.columns(4)

for col,(name,value) in zip(cols,values):

    with col:

        st.metric(name,value,help=KRI_HELP[name])

        st.caption('Measured from DE2 batch' if name in ('BLAST RADIUS','BOUNDARY DRIFT') else 'No source measurement')



# One graph edge per directed relationship triple. MISSING_EDGE is not plotted as observed.

def mermaid_source():

    base = {(x['source'],x['relationship'],x['target']) for x in topology['approved_edges']}

    observed = {(x['source'],x['relationship'],x['target']) for x in matched + new_edges}

    all_triples = sorted(base | observed)

    entities = sorted({v for e in all_triples for v in (e[0],e[2])})

    node_id = {entity: f'N{i}' for i,entity in enumerate(entities)}

    def label(entity):

        if entity.startswith('agent-'):

            return entity.replace('agent-','Agent: ')

        if entity.startswith('model:'):

            return entity.split(':')[-1] + ' (model)'

        if entity.startswith('tool:'):

            return entity.split(':')[-1] + ' (tool)'

        return entity

    lines = ['flowchart LR']

    for name,nid in node_id.items():

        safe_label = label(name).replace('"', "'")

        lines.append(f'{nid}["{safe_label}"]')

    green,orange,grey = [],[],[]

    for idx,(src,relation,target) in enumerate(all_triples):

        lines.append(f'{node_id[src]} -->|"{relation}"| {node_id[target]}')

        if (src,relation,target) in new_triplets: orange.append(idx)

        elif (src,relation,target) in observed: green.append(idx)

        else: grey.append(idx)

    if green: lines.append('linkStyle '+','.join(map(str,green))+' stroke:#65a78b,stroke-width:2px;')

    if orange: lines.append('linkStyle '+','.join(map(str,orange))+' stroke:#ff951f,stroke-width:4px;')

    if grey: lines.append('linkStyle '+','.join(map(str,grey))+' stroke:#91959f,stroke-width:2px,stroke-dasharray:5 5;')

    lines.append('classDef default fill:#10141c,stroke:#677080,color:#f2f2f2;')

    return '\n'.join(lines)



st.divider()

a,b = st.columns([1.45,1])

with a:

    st.subheader('Approved vs. Observed Interaction Graph')

    code=mermaid_source()

    embed = '''<div class="mermaid">'''+html_lib.escape(code)+'''</div><script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";mermaid.initialize({startOnLoad:true,theme:"dark",themeVariables:{background:"#07090e",primaryColor:"#10141c",primaryTextColor:"#eeeeee",lineColor:"#ff951f"}});</script>'''

    components.html(embed,height=450,scrolling=True)

    st.caption('Green: matched in proposed baseline · Orange: new observed relationship')

with b:

    st.subheader('Evidence Signals')

    st.markdown('**Detected activity:** New system/model relationships detected')

    st.markdown('**Agent:** 4 agents (claims, customer support v1/v2, underwriting)')

    st.markdown('**Target system:** 2 model targets (Claude Sonnet 5; GPT-4o)')

    st.markdown('**Reason flagged:** 4 relationship triples absent from proposed topology')

    st.markdown('**Access status:** Observed in synthetic batch; authorization and security outcome unverified')





st.divider()

st.subheader('Verified Backend Component Evidence')

st.caption('DE2 handoff batch counts and graph evidence only; live telemetry, Tier 2 composite risk, and human review outcomes were not supplied.')

with st.expander('View Backend Evidence'):

    a1,a2,a3=st.columns(3)

    a1.metric('MATCHED signals',summary['signal_counts']['MATCHED'])

    a2.metric('NEW_EDGE signals',summary['signal_counts']['NEW_EDGE'])

    a3.metric('MISSING_EDGE signals',summary['signal_counts']['MISSING_EDGE'])

    st.write('Reported interactions:', summary['total_interaction_events_reported_by_de2'])

    st.write('Emitted signals:', summary['total_emitted_signals'])

    st.write('Topology version:',version)

    st.write('Baseline approval:',summary['topology_approval_status'])

    st.write('Explicit MISSING_EDGE evidence:',missing)

    st.write('**New relationships:**')

    st.dataframe([{'source':e['source'],'relationship':e['relationship'],'target':e['target'],'signal_count':e['signal_count']} for e in new_edges],width='stretch',hide_index=True)



st.divider()

st.subheader('Trace Evidence · Structured JSON')

evidence={

    'source':'DE2 synthetic handoff batch',

    'graph_id':summary['graph_id'],

    'topology_version':version,

    'topology_approval_status':summary['topology_approval_status'],

    'event_type':'NEW_EDGE',

    'new_relationships':blast['new_relationships'],

    'direct_blast_radius':{

        'formula':'Count of distinct directly targeted resources',

        'value':blast_radius_count,

        'unit':'resources',

        'distinct_target_ids':sorted(direct_targets),

    },

    'source_agents_in_new_relationships':blast['affected_agent_count'],

    'signal_counts':summary['signal_counts'],

    'missing_edge_signals':missing,

    'data_sensitivity':None,

    'token_velocity':None,

    'downstream_impact_assessed':False,

}

st.json(evidence,expanded=True)

st.download_button('Export scenario evidence',data=json.dumps(evidence,indent=2),file_name='de2_batch_evidence.json',mime='application/json')


# Optional, independent workflow-level Token Velocity snapshot from the ML team.
# This MUST NOT be attributed to the DE2 insurance batch without verified matching IDs.
def read_token_velocity_snapshot(path):
    try:
        with path.open(encoding='utf-8') as handle:
            payload = json.load(handle)
    except (OSError, ValueError, UnicodeError) as exc:
        return None, f'Cannot read token snapshot: {exc}'

    if not isinstance(payload, dict):
        return None, 'Token snapshot must contain one JSON object.'
    status = payload.get('status')
    if status not in ('MEASURED', 'WARNING', 'NOT_MEASURED'):
        return None, 'Unrecognized Token Velocity measurement status.'
    if status in ('MEASURED', 'WARNING'):
        rate = payload.get('rate_tokens_per_minute')
        window = payload.get('window_minutes')
        if (isinstance(rate, bool) or not isinstance(rate, (int, float))
                or not isfinite(rate) or rate < 0):
            return None, 'Measured token rate must be a finite nonnegative number.'
        if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
            return None, 'Measured observation window must be a positive integer.'
        if not isinstance(payload.get('workflow_id'), str) or not payload['workflow_id']:
            return None, 'Measured snapshot must identify a workflow.'
        if payload.get('data_mode') != 'RECORDED_USAGE':
            return None, 'Measured snapshot must identify RECORDED_USAGE.'
        if payload.get('measurement_basis') != 'Recorded workflow token usage':
            return None, 'Measured snapshot must identify the expected measurement basis.'
        for field in ('spike_alert', 'exhaustion_alert'):
            if type(payload.get(field)) is not bool:
                return None, f'{field} must be a boolean.'
        if status == 'WARNING' and not (payload['spike_alert'] or payload['exhaustion_alert']):
            return None, 'WARNING requires a spike or exhaustion alert.'
        if status == 'MEASURED' and (payload['spike_alert'] or payload['exhaustion_alert']):
            return None, 'MEASURED cannot carry active warnings.'
        if not isinstance(payload.get('as_of_utc'), str) or not payload['as_of_utc']:
            return None, 'Measured snapshot requires an observation timestamp.'
    return payload, None

st.divider()
st.subheader('Token Velocity · Separate ML Workflow Evidence')
st.caption(
    'Standalone workflow measurement from ML Cost Intelligence. '
    'Not linked to the synthetic insurance DE2 graph or its 255 interactions.'
)
token_path = ROOT / 'token_velocity_kri.json'
if not token_path.is_file():
    st.info(
        'No Token Velocity export has been supplied for this demonstration. '
        'Place a validated ML exporter response in token_velocity_kri.json alongside this dashboard.'
    )
else:
    token_snapshot, token_error = read_token_velocity_snapshot(token_path)
    if token_error:
        st.warning(token_error + ' Token Velocity remains not measured.')
    elif token_snapshot['status'] == 'NOT_MEASURED':
        st.metric('Workflow Token Velocity', 'Not measured')
        st.caption('ML exporter: ' + str(token_snapshot.get('reason', 'No verified measurement available.')))
    else:
        st.metric('Workflow Token Velocity', f"{token_snapshot['rate_tokens_per_minute']:,.2f} tokens/min")
        if token_snapshot['status'] == 'WARNING':
            st.warning('ML exporter reports a token rate spike or projected budget exhaustion.')
        st.write('Workflow:', token_snapshot['workflow_id'])
        st.write('Observation window:', str(token_snapshot['window_minutes']) + ' minutes')
        st.write('Observed at (UTC):', token_snapshot['as_of_utc'])
        st.write('Baseline ready:', token_snapshot.get('baseline_ready'))
        st.write('Spike alert:', token_snapshot['spike_alert'])
        st.write('Projected exhaustion alert:', token_snapshot['exhaustion_alert'])
        st.caption('Recorded usage with matching settled reconciliation and reservation records; not independently verified provider telemetry.')
    if token_snapshot is not None:
        with st.expander('View standalone Token Velocity JSON'):
            st.json(token_snapshot)
        st.download_button(
            'Export standalone Token Velocity evidence',
            data=json.dumps(token_snapshot, indent=2),
            file_name='token_velocity_evidence.json', mime='application/json'
        )
