"""Plotly 3-D surface helper for ChemSpec folder waterfalls.

Requires the ``[ui]`` extra (plotly). Core grid math lives in
``spectrum_core.viz3d`` so tests do not import NiceGUI.
"""

from __future__ import annotations

import plotly.graph_objects as go

from spectrum_core.viz3d import spectra_to_surface


def build_surface_figure(traces, xlabel: str, ylabel: str) -> go.Figure:
    """Plotly Surface for folder traces. Series index is not time."""
    fig = go.Figure()
    try:
        grid = spectra_to_surface(traces)
    except ValueError as exc:
        fig.update_layout(
            title="ChemSpec — 3-D surface unavailable",
            template="plotly_white",
            height=520,
            annotations=[
                dict(
                    text=str(exc),
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="#888"),
                )
            ],
        )
        return fig

    fig.add_trace(
        go.Surface(
            x=grid.x.tolist(),
            y=grid.series.tolist(),
            z=grid.z.tolist(),
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title=ylabel),
            name="surface",
            hovertemplate=(
                "x=%{x:.3g}<br>series=%{y:.0f}<br>z=%{z:.4g}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=(
            f"ChemSpec — 3-D surface ({len(grid.series)} traces; "
            "series index, not time)"
        ),
        template="plotly_white",
        height=560,
        margin=dict(l=10, r=10, t=60, b=40),
        scene=dict(
            xaxis_title=xlabel,
            yaxis_title="Series index (folder order — not time)",
            zaxis_title=ylabel,
            xaxis=dict(autorange="reversed" if grid.x_unit == "cm-1" else True),
            aspectmode="manual",
            aspectratio=dict(x=1.6, y=0.7, z=0.6),
        ),
    )
    fig.add_annotation(
        text=(
            "3-D height is measured y (stack offsets stripped). "
            "Y axis is file order, not a time axis. "
            "ChemSpec makes no compound-ID claims."
        ),
        xref="paper",
        yref="paper",
        x=0,
        y=-0.08,
        showarrow=False,
        font=dict(size=11, color="#666"),
        xanchor="left",
    )
    return fig
