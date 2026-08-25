import streamlit as st
from .auth import delete_account


def render_sidebar(user_id: int, username: str):
    with st.sidebar:
        st.header("Panel użytkownika")
        st.write("Zalogowano jako:")
        st.subheader(username)
        if st.button("Wyloguj"):
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.subheader("Usuń konto")
        confirm_delete = st.checkbox("Potwierdzam usunięcie konta")
        if st.button("Usuń konto"):
            if confirm_delete:
                delete_account(user_id)
                st.session_state.clear()
                st.success("Konto zostało usunięte.")
                st.rerun()
            else:
                st.warning("Najpierw zaznacz potwierdzenie usunięcia konta.")
