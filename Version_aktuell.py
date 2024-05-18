import streamlit as st
import pandas as pd
import os
import json
import bcrypt
from datetime import datetime
import sqlite3
import io

st.set_page_config(page_title="ZellZaehler", page_icon="🔬", layout="wide")

# Konfiguration
USER_DATA_FILE = 'benutzerdaten.json'

# SQLite-Datenbank initialisieren
def init_db():
    conn = sqlite3.connect('zellzaehler.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                username TEXT,
                sample_number TEXT,
                count_session INTEGER,
                date TEXT,
                counts TEXT,
                FOREIGN KEY(username) REFERENCES users(username)
              )''')
    conn.commit()
    conn.close()

# Benutzerdaten initialisieren
def init_user_data():
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as file:
            json.dump({}, file)

# Benutzerdaten laden
def load_user_data():
    with open(USER_DATA_FILE, 'r') as file:
        return json.load(file)

# Benutzerdaten speichern
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file)

# Passwort verschlüsseln
def encrypt_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

# Passwort überprüfen
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode())

# Benutzerlogin überprüfen
def verify_user(username, password):
    users = load_user_data()
    if username in users and verify_password(password, users[username]['password']):
        return True
    return False

# Neuen Benutzer registrieren
def register_user(username, password):
    users = load_user_data()
    if username in users:
        return False
    users[username] = {'password': encrypt_password(password)}
    save_user_data(users)
    return True

# Benutzerergebnisse speichern
def save_user_results(username, sample_number, count_session, date_time, current_counts):
    conn = sqlite3.connect('zellzaehler.db')
    c = conn.cursor()
    counts_str = ','.join(f'{key}:{value}' for key, value in current_counts.items())
    c.execute('''INSERT INTO results (username, sample_number, count_session, date, counts)
                 VALUES (?, ?, ?, ?, ?)''', (username, sample_number, count_session, date_time, counts_str))
    conn.commit()
    conn.close()

# Benutzerergebnisse abrufen
def get_user_results(username):
    conn = sqlite3.connect('zellzaehler.db')
    c = conn.cursor()
    c.execute('SELECT sample_number, count_session, date, counts FROM results WHERE username=?', (username,))
    results = c.fetchall()
    conn.close()
    return results

# Funktion zum Herunterladen von Daten als Excel
def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

# Datenbank und Benutzerdaten initialisieren
init_db()
init_user_data()

# Streamlit-Anwendung
st.title("ZellZaehler")

button_names = [
    "Pro", "Mye", "Meta", "Stab", "Seg", "Eos",
    "Baso", "Mono", "Ly", "Div1", "Div2", "Div3"
]

# Benutzer-Authentifizierung
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'register' not in st.session_state:
    st.session_state['register'] = False

if 'guest' not in st.session_state:
    st.session_state['guest'] = False

if not st.session_state['authenticated'] and not st.session_state['guest']:
    if st.session_state['register']:
        st.subheader("Registrieren")
        reg_username = st.text_input("Wähle einen Benutzernamen")
        reg_password = st.text_input("Wähle ein Passwort", type="password")
        reg_confirm_password = st.text_input("Passwort bestätigen", type="password")
        if st.button("Registrieren"):
            if reg_username and reg_password and reg_confirm_password:
                if reg_password == reg_confirm_password:
                    if register_user(reg_username, reg_password):
                        st.success("Registrierung erfolgreich. Du kannst dich jetzt einloggen.")
                        st.session_state['register'] = False
                    else:
                        st.error("Benutzername existiert bereits. Bitte wähle einen anderen Benutzernamen.")
                else:
                    st.error("Passwörter stimmen nicht überein.")
            else:
                st.error("Bitte fülle alle erforderlichen Felder aus.")
        if st.button("Zurück zum Login"):
            st.session_state['register'] = False
    else:
        st.subheader("Login")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        if st.button("Login"):
            if username and password:
                if verify_user(username, password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.session_state['results'] = get_user_results(username)
                else:
                    st.error("Ungültiger Benutzername oder Passwort")
            else:
                st.error("Bitte gebe sowohl Benutzernamen als auch Passwort ein")
        if st.button("Registrieren"):
            st.session_state['register'] = True
        if st.button("Als Gast eintreten"):
            st.session_state['guest'] = True
else:
    st.sidebar.header("Navigation")
    view = st.sidebar.radio("Ansicht wählen", ["Einführung", "Zählen", "Archiv"])

    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'sample_number' not in st.session_state:
        st.session_state['sample_number'] = ""

    if 'count_session' not in st.session_state:
        st.session_state['count_session'] = 1

    if 'custom_names' not in st.session_state:
        st.session_state['custom_names'] = ["Div1", "Div2", "Div3"]

    for name in button_names:
        if f'count_{name}' not in st.session_state:
            st.session_state[f'count_{name}'] = 0

    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = False

    if 'name_edit_mode' not in st.session_state:
        st.session_state['name_edit_mode'] = False

    def increment_button_count(name):
        total_count = sum(st.session_state[f'count_{name}'] for name in button_names)
        if total_count >= 100:
            st.error("Das Zählziel von 100 wurde bereits erreicht.")
        else:
            st.session_state[f'count_{name}'] += 1

    def save_state():
        current_counts = {name: st.session_state[f'count_{name}'] for name in button_names}
        st.session_state['history'].append(current_counts)

    def undo_last_step():
        if st.session_state['history']:
            last_state = st.session_state['history'].pop()
            for name in button_names:
                st.session_state[f'count_{name}'] = last_state[name]

    def reset_counts():
        for name in button_names:
            st.session_state[f'count_{name}'] = 0

    def save_results():
        sample_number = st.session_state['sample_number']
        count_session = st.session_state['count_session']
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_counts = {name: st.session_state[f'count_{name}'] for name in button_names}
        if 'username' in st.session_state:
            save_user_results(st.session_state['username'], sample_number, count_session, date_time, current_counts)
        if count_session == 2:
            st.session_state['count_session'] = 1
            st.session_state['sample_number'] = ""
        else:
            st.session_state['count_session'] += 1
        reset_counts()

    def display_results():
        if not st.session_state['results']:
            st.write("Keine gespeicherten Ergebnisse.")
            return
        
        for result in st.session_state['results']:
            sample_number, count_session, date, counts_str = result
            counts = dict(item.split(":") for item in counts_str.split(","))
            counts = {key: int(value) for key, value in counts.items()}
            
            st.write(f"**Probenummer:** {sample_number}")
            st.write(f"**Datum {count_session}. Zählung:** {date}")
            
            data = [[name, counts.get(name, 0)] for name in button_names]
            counts_df = pd.DataFrame(data, columns=['Zellentyp', f'Anzahl {count_session}. Zählung'])
            st.dataframe(counts_df, hide_index=True)
            
            if count_session == 2:
                avg_data = [[name, (counts.get(name, 0) + counts.get(name, 0)) / 2] for name in button_names]
                avg_df = pd.DataFrame(avg_data, columns=['Zellentyp', 'Durchschnitt'])
                st.write("**Durchschnitt:**")
                st.dataframe(avg_df, hide_index=True)

                df_combined = pd.concat([counts_df.set_index('Zellentyp'), avg_df.set_index('Zellentyp')], axis=1).reset_index()
                excel_data = to_excel(df_combined)
                st.download_button(label='Download Excel', data=excel_data, file_name=f'{sample_number}_{count_session}.xlsx')

    if view == "Einführung":
        st.header("Einführung")
        st.write("""
        Willkommen bei der ZellZähler-App. Diese App hilft Ihnen dabei, Zählungen von verschiedenen Zelltypen durchzuführen und zu speichern.

        **Funktionen:**
        - **Probenummer eingeben**: Geben Sie eine eindeutige Probenummer ein, um eine neue Zählung zu starten oder eine bestehende zu bearbeiten.
        - **Zählen**: Führen Sie die Zählungen durch, indem Sie die entsprechenden Knöpfe drücken.
        - **Zelle hinzufügen**: Klicken Sie auf diesen Knopf, um die letzten drei Knöpfe umzubenennen.
        - **Korrigieren**: Ermöglicht das manuelle Korrigieren der Zählerstände.
        - **Rückgängig**: Macht den letzten Zählungsschritt rückgängig.
        - **Zählung zurücksetzen**: Setzt alle Zählerstände auf Null zurück.
        - **Ergebnisse speichern**: Speichert die aktuellen Zählungsergebnisse.
        - **Archiv**: Zeigt alle gespeicherten Zählungsergebnisse an, die nach Probenummern durchsucht werden können.
        """)

    elif view == "Zählen":
        st.session_state['sample_number'] = st.text_input("Probenummer eingeben", value=st.session_state['sample_number'])
        
        if not st.session_state['sample_number']:
            st.warning("Bitte geben Sie eine Probenummer ein, um zu beginnen.")
        else:
            st.write(f"Aktuelle Zählungssession: {st.session_state['count_session']}")
            
            if st.session_state['count_session'] == 1:
                if st.button("Zu zweiter Zählung wechseln"):
                    st.session_state['count_session'] = 2
            else:
                if st.button("Zu erster Zählung wechseln"):
                    st.session_state['count_session'] = 1
            
            if st.button('Korrigieren'):
                st.session_state['edit_mode'] = not st.session_state['edit_mode']

            if st.button('Zelle hinzufügen'):
                st.session_state['name_edit_mode'] = not st.session_state['name_edit_mode']

            total_count = sum(st.session_state[f'count_{name}'] for name in button_names)
            st.write(f"{total_count}/100")

            if total_count == 100:
                st.success("100 Zellen gezählt!")
                st.button('Rückgängig', disabled=True, key='undo_button_disabled')
                st.button('Zelle hinzufügen (disabled)', disabled=True, key='add_cell_button_disabled')
                st.write("Ergebnisse:")
                if st.session_state.get('result_df') is None:
                    result_df = pd.DataFrame({'Zellentyp': button_names, 'Anzahl': [st.session_state[f'count_{name}'] for name in button_names]})
                    st.session_state['result_df'] = result_df
                st.dataframe(st.session_state['result_df'], hide_index=True)

            cols_per_row = 3
            rows = [st.columns(cols_per_row) for _ in range(len(button_names) // cols_per_row + 1)]
            button_pressed = None

            for name in button_names:
                index = button_names.index(name)
                row_index, col_index = divmod(index, cols_per_row)
                col = rows[row_index][col_index]
                with col:
                    display_name = name
                    if name in ["Div1", "Div2", "Div3"]:
                        display_name = st.session_state['custom_names'][int(name[-1]) - 1]
                    button_label = f"{display_name}\n({st.session_state[f'count_{name}']})"
                    if st.button(button_label, key=f'button_{name}'):
                        if not st.session_state['edit_mode'] and not st.session_state['name_edit_mode']:
                            save_state()
                            button_pressed = name
                    if st.session_state['edit_mode']:
                        new_count = st.number_input("Zähler korrigieren", value=st.session_state[f'count_{name}'], key=f'edit_{name}')
                        st.session_state[f'count_{name}'] = new_count

            if st.session_state['name_edit_mode']:
                for i in range(3):
                    new_name = st.text_input(f"Neuer Name für {button_names[9+i]}", value=st.session_state['custom_names'][i], key=f'custom_name_{i}')
                    st.session_state['custom_names'][i] = new_name

            if button_pressed is not None:
                increment_button_count(button_pressed)
                if total_count + 1 == 100:
                    st.rerun()

            if button_pressed is not None:
                if total_count == 100:
                    st.error("Das Zählziel von 100 wurde bereits erreicht.")
                    st.rerun()

            if st.button('Rückgängig', key='undo_button'):
                undo_last_step()

            if st.button('Zählung zurücksetzen'):
                reset_counts()

            if st.button('Zählung beenden - Archivieren'):
                save_results()
                st.info("Zählung archiviert und zurückgesetzt.")
                reset_counts()

    elif view == "Archiv":
        st.header("Archivierte Ergebnisse")
        sample_numbers = list(set(result[0] for result in st.session_state['results']))
        selected_sample = st.selectbox("Probenummer auswählen", sample_numbers)
        
        if selected_sample:
            for result in st.session_state['results']:
                if result[0] == selected_sample:
                    sample_number, count_session, date, counts_str = result
                    counts = dict(item.split(":") for item in counts_str.split(","))
                    counts = {key: int(value) for key, value in counts.items()}
                    
                    st.write(f"**Probenummer:** {sample_number}")
                    st.write(f"**Datum {count_session}. Zählung:** {date}")
                    
                    data = [[name, counts.get(name, 0)] for name in button_names]
                    counts_df = pd.DataFrame(data, columns=['Zellentyp', f'Anzahl {count_session}. Zählung'])
                    st.dataframe(counts_df, hide_index=True)
                    
                    if count_session == 2:
                        avg_data = [[name, (counts.get(name, 0) + counts.get(name, 0)) / 2] for name in button_names]
                        avg_df = pd.DataFrame(avg_data, columns=['Zellentyp', 'Durchschnitt'])
                        st.write("**Durchschnitt:**")
                        st.dataframe(avg_df, hide_index=True)

                        df_combined = pd.concat([counts_df.set_index('Zellentyp'), avg_df.set_index('Zellentyp')], axis=1).reset_index()
                        excel_data = to_excel(df_combined)
                        st.download_button(label='Download Excel', data=excel_data, file_name=f'{sample_number}_{count_session}.xlsx')
