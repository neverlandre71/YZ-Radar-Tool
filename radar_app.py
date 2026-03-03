import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Page Configuration
st.set_page_config(page_title="Professional Radar Chart Pro", layout="wide")

st.title("🎯 Ultimate Radar Chart Generator (Pro)")

# --- 1. State Management ---
if 'df' not in st.session_state:
    init_data = {
        "Parameter": ["Metric A", "Metric B", "Metric C", "Metric D", "Metric E"],
        "Group 1": [10, 80, 50, 40, 90],
        "Group 2": [30, 40, 60, 70, 50]
    }
    st.session_state.df = pd.DataFrame(init_data)

# --- 2. Sidebar: Advanced Controls ---
st.sidebar.header("🛠️ Chart Controls")

# 2.1 Labels & Text
with st.sidebar.expander("📝 Label & Text Settings", expanded=True):
    show_params = st.checkbox("Show Parameter Labels (Text)", value=True)
    param_font_size = st.slider("Parameter Label Size", 8, 30, 12)
    show_tick_labels = st.checkbox("Show Scale Values (Numbers)", value=True)
    tick_font_size = st.slider("Scale Number Size", 6, 20, 10)
    precision = st.slider("Decimal Precision", 0, 4, 1)

# 2.2 Range & Grid Strategy
with st.sidebar.expander("📏 Range & Grid Strategy", expanded=True):
    numeric_df = st.session_state.df.select_dtypes(include=[np.number])
    data_max = float(numeric_df.max().max()) if not numeric_df.empty else 100.0
    
    manual_min = st.number_input("Origin Value (Center)", value=0.0, format="%.4f")
    manual_max = st.number_input("Maximum Value (Outer Circle)", value=max(data_max, manual_min + 1), format="%.4f")
    num_grids = st.slider("Number of Grid Circles", min_value=2, max_value=20, value=5)

# 2.3 Style & Background (Updated with Radar Circle Background)
with st.sidebar.expander("🎨 Style & Background", expanded=True):
    # Overall Paper Background
    st.markdown("**Canvas (Overall) Background**")
    paper_bg_choice = st.radio("Canvas Type", ["Transparent", "Solid Color"], key="paper_bg")
    paper_bg_color = st.color_picker("Canvas Color", "#FFFFFF", key="p_color")
    paper_bg_opacity = st.slider("Canvas Opacity", 0.0, 1.0, 0.0 if paper_bg_choice == "Transparent" else 1.0)
    
    st.divider()
    
    # Radar Circle Background (NEW FEATURE)
    st.markdown("**Radar Circle (Inner) Background**")
    radar_bg_color = st.color_picker("Circle Fill Color", "#F0F2F6")
    radar_bg_opacity = st.slider("Circle Opacity", 0.0, 1.0, 0.5)

    st.divider()
    
    grid_color = st.color_picker("Grid/Spoke Color", "#D3D3D3")
    grid_width = st.slider("Line Thickness", 0.5, 3.0, 1.0)
    grid_dash = st.selectbox("Circle Style", ["dash", "dot", "solid"])
    fill_opacity = st.slider("Data Fill Transparency", 0.0, 1.0, 0.3)

# 2.4 Group Management
st.sidebar.subheader("🌈 Group Management")
with st.sidebar.expander("Add/Remove Groups"):
    new_col = st.text_input("New Group Name")
    if st.button("➕ Add Group"):
        if new_col and new_col not in st.session_state.df.columns:
            st.session_state.df[new_col] = manual_min
            st.rerun()
    
    cols_to_del = [c for c in st.session_state.df.columns if c != "Parameter"]
    selected_del = st.multiselect("Remove Groups", options=cols_to_del)
    if st.button("🗑️ Delete Selected"):
        st.session_state.df = st.session_state.df.drop(columns=selected_del)
        st.rerun()

# Group colors
group_names = [col for col in st.session_state.df.columns if col != "Parameter"]
group_colors = {}
for i, group in enumerate(group_names):
    default_palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
    group_colors[group] = st.sidebar.color_picker(f"Color: {group}", default_palette[i % len(default_palette)])

# --- 3. Helper Functions ---
def hex_to_rgba(hex_str, opacity):
    h = hex_str.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{opacity})"

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
        
        # Calculate Colors
        final_paper_bg = "rgba(0,0,0,0)" if paper_bg_choice == "Transparent" else hex_to_rgba(paper_bg_color, paper_bg_opacity)
        final_radar_bg = hex_to_rgba(radar_bg_color, radar_bg_opacity)

        for group in group_names:
            raw_values = edited_df[group].tolist()
            # Clean values
            values = []
            for v in raw_values:
                try:
                    values.append(float(v))
                except:
                    values.append(manual_min)
            
            # Close path
            r_values = values + [values[0]]
            theta_values = categories + [categories[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=r_values, theta=theta_values,
                fill='toself', name=group,
                line=dict(color=group_colors[group], width=2),
                fillcolor=hex_to_rgba(group_colors[group], fill_opacity),
                marker=dict(size=6)
            ))

        tick_vals = np.linspace(manual_min, manual_max, num_grids)

        fig.update_layout(
            paper_bgcolor=final_paper_bg,
            plot_bgcolor="rgba(0,0,0,0)", # Handled by polar.bgcolor
            polar=dict(
                bgcolor=final_radar_bg, # THE CORE CHANGE: Inner circle color
                radialaxis=dict(
                    visible=True, 
                    range=[manual_min, manual_max],
                    tickvals=tick_vals,
                    showticklabels=show_tick_labels,
                    tickfont=dict(size=tick_font_size, color="gray"),
                    tickformat=f".{precision}f",
                    ticks="", showline=False,
                    gridcolor=grid_color, gridwidth=grid_width, griddash=grid_dash,
                    angle=0,
                ),
                angularaxis=dict(
                    showgrid=True, gridcolor=grid_color, gridwidth=grid_width,
                    showline=True, linecolor=grid_color, linewidth=grid_width,
                    showticklabels=show_params,
                    tickfont=dict(size=param_font_size, color="black"),
                    rotation=90, direction="clockwise"
                )
            ),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            height=750,
            margin=dict(l=100, r=100, t=100, b=100)
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- 5. Export ---
    st.divider()
    st.subheader("💾 Export Image")
    ce1, ce2 = st.columns(2)
    with ce1: fmt = st.selectbox("Image Format", ["png", "pdf", "svg", "jpg"])
    with ce2: scale = st.slider("Resolution (Scale)", 1, 5, 3)

    try:
        img_data = fig.to_image(format=fmt, engine="kaleido", scale=scale)
        st.download_button(label=f"Download {fmt.upper()}", data=img_data, file_name=f"radar_pro.{fmt}")
    except:
        st.info("Note: Ensure `kaleido` is installed for exports.")
