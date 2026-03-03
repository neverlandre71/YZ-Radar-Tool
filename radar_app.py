import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Page Configuration
st.set_page_config(page_title="Radar Pro - Fixed v3", layout="wide")

st.title("🎯 Ultimate Radar Chart Generator (Pro)")

# --- 1. State Management ---
if 'df' not in st.session_state:
    # Set default values to a smaller scale as requested
    init_data = {
        "Parameter": ["Metric A", "Metric B", "Metric C", "Metric D", "Metric E"],
        "Group 1": [4.2, 3.8, 4.5, 3.0, 4.8],
        "Group 2": [3.0, 4.5, 2.8, 4.0, 3.5]
    }
    st.session_state.df = pd.DataFrame(init_data)

# --- 2. Helper Functions ---
def hex_to_rgba(hex_str, opacity):
    """Safe Hex to RGBA conversion."""
    try:
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join([c*2 for c in hex_str])
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return f"rgba({r},{g},{b},{opacity})"
    except:
        return None

# --- 3. Sidebar: Controls ---
st.sidebar.header("🛠️ Chart Controls")

# 3.1 Labels
with st.sidebar.expander("📝 Label & Text Settings", expanded=True):
    show_params = st.checkbox("Show Parameter Labels", value=True)
    param_font_size = st.slider("Parameter Label Size", 8, 30, 12)
    show_tick_labels = st.checkbox("Show Scale Values", value=True)
    tick_font_size = st.slider("Scale Number Size", 6, 20, 10)
    precision = st.slider("Decimal Precision", 0, 4, 1)

# 3.2 Range (Safety Fixed)
with st.sidebar.expander("📏 Range & Grid Strategy", expanded=True):
    manual_min = st.number_input("Origin Value (Center)", value=0.0, format="%.4f")
    # Default Maximum Value set to 5.0 as requested
    raw_max = st.number_input("Maximum Value (Outer Circle)", value=5.0, format="%.4f")
    
    # CRITICAL BUG FIX: Ensure Max is always > Min
    # If Max <= Min, Plotly Polar will crash and turn PINK
    if raw_max <= manual_min:
        manual_max = manual_min + 0.1
        st.warning(f"Max must be > Min. Adjusted to {manual_max}")
    else:
        manual_max = raw_max

    num_grids = st.slider("Number of Grid Circles", 2, 20, 5)

# 3.3 Style & Background (Fixed Pink Bug Logic)
with st.sidebar.expander("🎨 Style & Background", expanded=True):
    # Canvas Background
    st.markdown("**Canvas (Overall) Background**")
    paper_bg_choice = st.radio("Canvas Type", ["Transparent", "Solid Color"], key="p_choice")
    paper_bg_color = st.color_picker("Canvas Color", "#FFFFFF", key="p_col")
    paper_bg_opacity = st.slider("Canvas Opacity", 0.0, 1.0, 0.0 if paper_bg_choice == "Transparent" else 1.0)
    final_paper_bg = "rgba(0,0,0,0)" if paper_bg_choice == "Transparent" else hex_to_rgba(paper_bg_color, paper_bg_opacity)

    st.divider()
    
    # Radar Circle Background
    st.markdown("**Radar Circle (Inner) Fill**")
    enable_circle_bg = st.checkbox("Fill Radar Circle Background", value=False)
    if enable_circle_bg:
        radar_bg_color = st.color_picker("Circle Color", "#FFFFFF")
        radar_bg_opacity = st.slider("Circle Opacity", 0.0, 1.0, 0.2)
        final_radar_bg = hex_to_rgba(radar_bg_color, radar_bg_opacity)
    else:
        # Using None or an empty string is safer than rgba(0,0,0,0) for some Plotly versions
        final_radar_bg = None 

    st.divider()
    grid_color = st.color_picker("Grid Color", "#D3D3D3")
    grid_width = st.slider("Line Thickness", 0.5, 3.0, 1.0)
    grid_dash = st.selectbox("Circle Style", ["dash", "dot", "solid"])
    fill_opacity = st.slider("Data Fill Transparency", 0.0, 1.0, 0.3)

# 3.4 Group Management
st.sidebar.subheader("🌈 Group Management")
group_names = [col for col in st.session_state.df.columns if col != "Parameter"]
with st.sidebar.expander("Add/Remove Groups"):
    new_col = st.text_input("New Group Name")
    if st.button("➕ Add"):
        if new_col and new_col not in st.session_state.df.columns:
            st.session_state.df[new_col] = float(manual_min)
            st.rerun()
    selected_del = st.multiselect("Remove Groups", options=group_names)
    if st.button("🗑️ Delete"):
        st.session_state.df = st.session_state.df.drop(columns=selected_del)
        st.rerun()

group_colors = {}
for i, group in enumerate(group_names):
    palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
    group_colors[group] = st.sidebar.color_picker(f"Color: {group}", palette[i % len(palette)])

# --- 4. Main Interface ---
col_table, col_plot = st.columns([1, 1.4])

with col_table:
    st.subheader("📝 Data Editor")
    edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    st.session_state.df = edited_df

with col_plot:
    st.subheader("👁️ Live Radar Preview")
    
    categories = edited_df["Parameter"].astype(str).tolist()
    if not categories or not group_names:
        st.info("Please add parameters and groups.")
    else:
        fig = go.Figure()

        for group in group_names:
            raw_vals = edited_df[group].tolist()
            # Handle non-numeric gracefully
            vals = []
            for v in raw_vals:
                try: vals.append(float(v))
                except: vals.append(float(manual_min))
            
            # Close loop
            r_v = vals + [vals[0]]
            t_v = categories + [categories[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=r_v, theta=t_v,
                fill='toself', name=group,
                line=dict(color=group_colors[group], width=2),
                fillcolor=hex_to_rgba(group_colors[group], fill_opacity),
                marker=dict(size=6)
            ))

        tick_vals = np.linspace(manual_min, manual_max, num_grids)

        # Apply Layout with extreme safety
        fig.update_layout(
            template=None, # Remove all default templates to prevent theme-based pink glitches
            paper_bgcolor=final_paper_bg,
            plot_bgcolor="rgba(0,0,0,0)",
            polar=dict(
                bgcolor=final_radar_bg,
                radialaxis=dict(
                    visible=True, 
                    range=[manual_min, manual_max],
                    tickvals=tick_vals, 
                    showticklabels=show_tick_labels,
                    tickfont=dict(size=tick_font_size, color="gray"),
                    tickformat=f".{precision}f",
                    ticks="", 
                    showline=False,
                    gridcolor=grid_color, 
                    gridwidth=grid_width, 
                    griddash=grid_dash,
                    angle=0,
                ),
                angularaxis=dict(
                    showgrid=True, 
                    gridcolor=grid_color, 
                    gridwidth=grid_width,
                    showline=True, 
                    linecolor=grid_color, 
                    linewidth=grid_width,
                    showticklabels=show_params,
                    tickfont=dict(size=param_font_size, color="black"),
                    rotation=90, 
                    direction="clockwise"
                )
            ),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            height=700,
            margin=dict(l=80, r=80, t=100, b=80)
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- 5. Export ---
    st.divider()
    st.subheader("💾 Export Image")
    ce1, ce2 = st.columns(2)
    with ce1: fmt = st.selectbox("Format", ["png", "pdf", "svg", "jpg"])
    with ce2: scale = st.slider("Scale", 1, 5, 3)

    try:
        img = fig.to_image(format=fmt, engine="kaleido", scale=scale)
        st.download_button(label=f"Download {fmt.upper()}", data=img, file_name=f"radar.{fmt}")
    except:
        st.info("Install `kaleido` for export.")
