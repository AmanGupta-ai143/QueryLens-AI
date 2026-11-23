"""Small helpers that keep the UI working across Streamlit versions."""
import streamlit as st


def show_chart(fig, key: str | None = None) -> None:
    """Render a Plotly figure full-width (new and old Streamlit APIs)."""
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key=key)


def show_table(data, **kwargs) -> None:
    """Render a dataframe full-width (new and old Streamlit APIs)."""
    try:
        st.dataframe(data, width="stretch", hide_index=True, **kwargs)
    except TypeError:
        st.dataframe(data, use_container_width=True, hide_index=True, **kwargs)


def empty_state(message: str, icon: str = "📭") -> None:
    st.info(f"{icon}  {message}")
