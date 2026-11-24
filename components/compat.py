"""Small helpers that keep the UI working across Streamlit versions."""
import streamlit as st


PLOT_CONFIG = {"displayModeBar": False}  # hides the Plotly toolbar (zoom/pan/camera icons)


def show_chart(fig, key: str | None = None) -> None:
    """Render a Plotly figure full-width (new and old Streamlit APIs)."""
    try:
        st.plotly_chart(fig, width="stretch", key=key, theme=None, config=PLOT_CONFIG)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key=key, theme=None, config=PLOT_CONFIG)


def show_table(data, **kwargs) -> None:
    """Render a dataframe full-width (new and old Streamlit APIs)."""
    try:
        st.dataframe(data, width="stretch", hide_index=True, **kwargs)
    except TypeError:
        st.dataframe(data, use_container_width=True, hide_index=True, **kwargs)


def empty_state(message: str, icon: str = "📭") -> None:
    st.info(f"{icon}  {message}")
