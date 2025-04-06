import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from utils.helpers import extract_mermaid_code

def render_mermaid(mermaid_code):
    """Render a Mermaid diagram from a code string."""
    if not mermaid_code or not isinstance(mermaid_code, str) or not mermaid_code.strip():
        st.caption("(No diagram)")
        return
    safe_code = mermaid_code.replace("`", r"\`")
    html = f"""<div class="mermaid" style="background-color:#ffffff; padding:10px; border-radius:5px; text-align:center;">{safe_code}</div> <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script> <script> try{{ mermaid.initialize({{ startOnLoad: true, theme: 'base', themeVariables: {{ primaryColor: '#eeeeee', primaryTextColor: '#1e1e2e', lineColor: '#4c4f69', textColor: '#4c4f69' }} }}); }} catch(e){{console.error("Mermaid fail:", e);}} </script> <style>.mermaid svg {{ max-width: 100%; height: auto; }}</style>"""
    with st.container(border=True):
        components.html(html, height=400, scrolling=True)
        
def render_skill_chart(skills_data, title):
    """Render a polar chart showing skill proficiency."""
    if not skills_data or not all(len(item)>=4 for item in skills_data):
        return None
    cats = [s[1] for s in skills_data]
    vals = [max(0.0, min(1.0, s[3])) for s in skills_data]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, 
        theta=cats, 
        fill='toself', 
        name='Proficiency', 
        line_color='#89b4fa', 
        fillcolor='rgba(137, 180, 250, 0.3)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])), 
        title=title, 
        margin=dict(t=50, b=10, l=40, r=40), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#cad3f5')
    )
    return fig
    
def render_progress_chart(user_id, db):
    """Render a chart showing user progress over time."""
    if not db:
        return None
    cur = db.conn.cursor()
    cur.execute('SELECT date(created_at) d, AVG(score) avg_s, COUNT(*) i FROM interactions WHERE user_id=? AND score IS NOT NULL GROUP BY d ORDER BY d ASC LIMIT 30', (user_id,))
    data = cur.fetchall()
    if not data:
        return None
    dates, scores, interactions = zip(*[(r[0], r[1] or 0, r[2]) for r in data]) # Ensure score is not None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, 
        y=scores, 
        mode='lines+markers', 
        name='Avg Score', 
        line=dict(color='#89b4fa', width=3)
    ))
    fig.add_trace(go.Bar(
        x=dates, 
        y=interactions, 
        name='Interactions', 
        marker_color='#fab387', 
        opacity=0.7, 
        yaxis='y2'
    ))
    fig.update_layout(
        title='Progress Over Time', 
        xaxis_title='Date', 
        yaxis=dict(title='Avg Score', range=[0, 1], color='#89b4fa'), 
        yaxis2=dict(title='Interactions', overlaying='y', side='right', color='#fab387', rangemode='nonnegative'), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#cad3f5'), 
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig

def apply_theme():
    """Apply the application theme with CSS."""
    st.markdown("""
    <style>
    /* Basic Catppuccin Macchiato Theme */
    .main { background-color: #24273a; color: #cad3f5; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #363a4f; border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: 600; color: #cad3f5; }
    .stTabs [aria-selected="true"] { background-color: #8aadf4 !important; color: #24273a !important; }
    h1, h2, h3 { color: #8aadf4; } /* Blue */
    .stButton>button { background-color: #8aadf4; color: #24273a; border: none; font-weight: bold; padding: 8px 16px; border-radius: 5px;}
    .stButton>button:hover { background-color: #a6daff; } /* Lighter blue on hover */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div { background-color: #363a4f; color: #cad3f5; border: 1px solid #494d64; border-radius: 5px; }
    .stSidebar { background-color: #1e2030; }
    .stExpander { background-color: #363a4f; border-radius: 8px; margin-bottom: 10px; border: 1px solid #494d64;}
    .stExpander header { color: #eed49f; font-weight: bold;} /* Yellow for expander headers */
    .metric-card { background-color: #363a4f; border-radius: 10px; padding: 15px; flex: 1; min-width: 180px; text-align: center; border-left: 5px solid #f5a97f; margin: 5px;} /* Peach */
    .metric-value { font-size: 24px; font-weight: bold; color: #8aadf4; }
    .metric-label { font-size: 14px; color: #b8c0e0; margin-top: 5px; }
    .skill-badge { background-color: #a6e3a1; color: #24273a; padding: 3px 10px; border-radius: 15px; font-weight: bold; display: inline-block; margin: 3px; font-size: 0.9em;} /* Green */
    .weak-badge { background-color: #ed8796; color: #24273a; padding: 3px 10px; border-radius: 15px; font-weight: bold; display: inline-block; margin: 3px; font-size: 0.9em;} /* Red */
    .content-card { background-color: #363a4f; color: #cad3f5; padding: 15px; border-radius: 8px; border-left: 5px solid #eed49f; margin: 10px 0; } /* Yellow */
    .recommendation-card { background-color: #363a4f; color: #cad3f5; padding: 15px; border-radius: 8px; border-left: 5px solid #c6a0f6; margin: 10px 0; } /* Mauve */
    .path-card { background-color: #363a4f; color: #cad3f5; padding: 15px; border-radius: 8px; border-left: 5px solid #a6e3a1; margin: 10px 0; } /* Green */
    .viz-container { background-color: #ffffff; padding: 10px; border-radius: 5px; margin-top: 10px; } /* White background for viz */
    footer {visibility: hidden;}
    /* Styling for buttons inside cards/columns for better spacing */
    .stButton { margin-top: 5px; margin-bottom: 5px; }
    </style>""", unsafe_allow_html=True)