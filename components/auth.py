"""Admin login. The password is never stored in the code.

Set it with ONE of:
  * Streamlit secrets (.streamlit/secrets.toml locally, or App settings -> Secrets on Streamlit Cloud):
        ADMIN_PASSWORD = "your-password"
  * environment variable QUERYLENS_ADMIN_PASSWORD
If no password is configured, admin features stay locked (safe by default).
"""
import os
import time

import streamlit as st

from services.security import verify_password


def configured_password() -> str | None:
    try:
        password = st.secrets["ADMIN_PASSWORD"]
    except Exception:  # no secrets file / key not set
        password = None
    return password or os.getenv("QUERYLENS_ADMIN_PASSWORD") or None


def is_admin() -> bool:
    return bool(st.session_state.get("is_admin"))


def logout() -> None:
    st.session_state["is_admin"] = False


def require_admin(what: str, key: str) -> bool:
    """Return True for a logged-in admin; otherwise show a login form and return False."""
    if is_admin():
        return True
    expected = configured_password()
    if not expected:
        st.warning("🔒 Admin features are locked because no admin password has been set. "
                   "Set `ADMIN_PASSWORD` in the app's secrets (see the README), then reload.")
        return False
    st.info(f"🔒 **{what}** is for administrators. Enter the admin password to continue.")
    with st.form(f"admin_login_{key}"):
        entered = st.text_input("Admin password", type="password", key=f"admin_pw_{key}")
        submitted = st.form_submit_button("Unlock")
    if submitted:
        if verify_password(entered, expected):
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            time.sleep(1)  # slow down guessing
            st.error("Wrong password.")
    return False
