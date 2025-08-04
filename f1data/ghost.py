import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def get_ghost_data(tel1, tel2):
    # Normalize time
    t1 = (tel1["SessionTime"] - tel1["SessionTime"].iloc[0]).dt.total_seconds()
    t2 = (tel2["SessionTime"] - tel2["SessionTime"].iloc[0]).dt.total_seconds()

    common_time = np.linspace(max(t1.min(), t2.min()), min(t1.max(), t2.max()), 500)

    interp1 = pd.DataFrame({
        "X": np.interp(common_time, t1, tel1["X"]),
        "Y": np.interp(common_time, t1, tel1["Y"])
    })

    interp2 = pd.DataFrame({
        "X": np.interp(common_time, t2, tel2["X"]),
        "Y": np.interp(common_time, t2, tel2["Y"])
    })

    interp1["time"] = common_time
    interp2["time"] = common_time

    return interp1, interp2

import plotly.graph_objects as go
import streamlit as st

def plot_ghost(ghost1, ghost2, name1, name2):
    # Track bounds for fixed view
    x_min = min(ghost1["X"].min(), ghost2["X"].min())
    x_max = max(ghost1["X"].max(), ghost2["X"].max())
    y_min = min(ghost1["Y"].min(), ghost2["Y"].min())
    y_max = max(ghost1["Y"].max(), ghost2["Y"].max())

    # Static track outline
    track_outline = go.Scatter(
        x=list(ghost1["X"]) + list(ghost2["X"]),
        y=list(ghost1["Y"]) + list(ghost2["Y"]),
        mode="lines",
        name="Track",
        line=dict(color="lightgray", width=2),
        hoverinfo="skip",
        showlegend=False
    )

    # Initial empty ghost traces
    ghost1_trace = go.Scatter(
        x=[], y=[],
        mode="lines+markers",
        name=name1,
        line=dict(color="red"),
        marker=dict(size=6, color="red")
    )

    ghost2_trace = go.Scatter(
        x=[], y=[],
        mode="lines+markers",
        name=name2,
        line=dict(color="blue"),
        marker=dict(size=6, color="blue")
    )

    # Animation frames
    frames = []
    for i in range(len(ghost1)):
        frames.append(go.Frame(
            data=[
                {},  # Static track
                dict(
                    type="scatter",
                    x=ghost1["X"][:i+1],
                    y=ghost1["Y"][:i+1],
                    mode="lines+markers",
                    line=dict(color="red"),
                    marker=dict(size=6, color="red")
                ),
                dict(
                    type="scatter",
                    x=ghost2["X"][:i+1],
                    y=ghost2["Y"][:i+1],
                    mode="lines+markers",
                    line=dict(color="blue"),
                    marker=dict(size=6, color="blue")
                )
            ],
            name=str(i)
        ))

    # Figure setup
    fig = go.Figure(
        data=[track_outline, ghost1_trace, ghost2_trace],
        layout=go.Layout(
            title="Ghost Car Animation",
            xaxis=dict(title="X", range=[x_min, x_max]),
            yaxis=dict(title="Y", range=[y_min, y_max], scaleanchor="x"),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[dict(label="Play", method="animate", args=[None])]
            )]
        ),
        frames=frames
    )

    st.plotly_chart(fig, use_container_width=True)

