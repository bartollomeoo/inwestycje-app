import streamlit as st
from .auth import login_user, register_user


def show_login_screen():
    st.title("Aplikacja wspomagająca inwestycje giełdowe")
    st.caption("System do zapisu transakcji, analizy portfela, generowania raportów i prezentacji wykresów.")
    left, right = st.columns(2)

    with left:
        st.subheader("Logowanie")
        with st.form("login_form"):
            username = st.text_input("Nazwa użytkownika")
            password = st.text_input("Hasło", type="password")
            submitted = st.form_submit_button("Zaloguj")
            if submitted:
                try:
                    user = login_user(username, password)
                    if user:
                        st.session_state["user_id"] = user["id"]
                        st.session_state["username"] = user["username"]
                        st.success("Zalogowano poprawnie.")
                        st.rerun()
                    else:
                        st.error("Nieprawidłowy login lub hasło.")
                except Exception as exc:
                    st.error(f"Nie udało się zalogować: {exc}")

    with right:
        st.subheader("Rejestracja")
        with st.form("register_form", clear_on_submit=True):
            new_username = st.text_input("Nowa nazwa użytkownika")
            new_password = st.text_input("Nowe hasło", type="password")
            submitted = st.form_submit_button("Utwórz konto")
            if submitted:
                try:
                    register_user(new_username, new_password)
                    st.success("Konto zostało utworzone. Możesz się zalogować.")
                except Exception as exc:
                    st.error(str(exc))
    st.divider()
