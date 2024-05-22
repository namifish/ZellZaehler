import streamlit as st
import pandas as pd
import os
import json
import bcrypt
from datetime import datetime
import sqlite3
import io
import base64

st.set_page_config(page_title="ZellZähler", page_icon="🔬")
# Funktion, um das Hintergrundbild festzulegen
def set_background(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Hintergrund festlegen
set_background('hintergrund.png')

# Konfiguration
LOGIN_FILE = 'login_hashed_password_list.csv'

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
    if not os.path.exists(LOGIN_FILE):
        df = pd.DataFrame(columns=['username', 'password'])
        df.to_csv(LOGIN_FILE, index=False)

# Benutzerdaten laden
def load_user_data():
    if not os.path.exists(LOGIN_FILE):
        init_user_data()
    return pd.read_csv(LOGIN_FILE)

# Benutzerdaten speichern
def save_user_data(data):
    data.to_csv(LOGIN_FILE, index=False)

# Passwort verschlüsseln
def encrypt_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

# Passwort überprüfen
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode())

# Benutzerlogin überprüfen
def verify_user(username, password):
    users = load_user_data()
    if username in users['username'].values:
        hashed_password = users[users['username'] == username]['password'].values[0]
        if verify_password(password, hashed_password):
            return True
    return False

# Neuen Benutzer registrieren
def register_user(username, password):
    users = load_user_data()
    if username in users['username'].values:
        return False
    new_user = pd.DataFrame([[username, encrypt_password(password)]], columns=['username', 'password'])
    users = pd.concat([users, new_user], ignore_index=True)
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
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

# Datenbank und Benutzerdaten initialisieren
init_db()
init_user_data()

# Streamlit-Anwendung
st.title("ZellZähler")

button_names = [
    "Pro   ", "Mye   ", "Meta   ", "Stab   ", "Seg   ", "Eos   ",
    "Baso   ", "Mono   ", "Ly   ", "Div1   ", "Div2   ", "Div3   "
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
        register_columns = st.columns((0.5,3,3,0.5))

        with register_columns[1]:
            if st.button("Registrieren", use_container_width=True):
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

        with register_columns[2]:
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['register'] = False
    else:
        st.subheader("Login")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        login_columns = st.columns((0.5,3,3,3,0.5))
        with login_columns[1]:
            if st.button("Login",use_container_width=True):
                if username and password:
                    if verify_user(username, password):
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['results'] = get_user_results(username)
                    else:
                        st.error("Ungültiger Benutzername oder Passwort")
                else:
                    st.error("Bitte gebe sowohl Benutzernamen als auch Passwort ein")

        with login_columns[2]:
            if st.button("Registrieren",use_container_width=True):
                st.session_state['register'] = True

        with login_columns[3]:
            if st.button("Weiter als Gast", help="Als Gast hast du keinen Zugriff auf das Archiv.",use_container_width=True):
                st.session_state['guest'] = True
                if 'guest_results' not in st.session_state:
                    st.session_state['guest_results'] = []
else:
    st.sidebar.header("Navigation")
    view = st.sidebar.radio("Ansicht wählen", ["Einführung", "Zählen", "Archiv", "Account"])

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
            st.rerun()

    def save_state():
        current_counts = {name: st.session_state[f'count_{name}'] for name in button_names}
        st.session_state['history'].append(current_counts)

    def undo_last_step():
        if st.session_state['history']:
            last_state = st.session_state['history'].pop()
            for name in button_names:
                st.session_state[f'count_{name}'] = last_state[name]
            st.rerun()

    def reset_counts():
        for name in button_names:
            st.session_state[f'count_{name}'] = 0
        st.rerun()

    def save_results():
        sample_number = st.session_state['sample_number']
        count_session = st.session_state['count_session']
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_counts = {name: st.session_state[f'count_{name}'] for name in button_names}
        if 'username' in st.session_state:
            save_user_results(st.session_state['username'], sample_number, count_session, date_time, current_counts)
            st.session_state['results'] = get_user_results(st.session_state['username'])
        else:
            guest_result = {
                'sample_number': sample_number,
                'count_session': count_session,
                'date': date_time,
                'counts': current_counts
            }
            st.session_state['guest_results'].append(guest_result)
        if count_session == 2:
            st.session_state['count_session'] = 1
            st.session_state['sample_number'] = ""
        else:
            st.session_state['count_session'] += 1
        reset_counts()

    def display_results(results):
        if not results:
            st.write("Keine gespeicherten Ergebnisse.")
            return

        if isinstance(results[0], dict):  # Gast-Ergebnisse
            sample_numbers = list(set(result['sample_number'] for result in results))
            selected_sample = st.selectbox("Probenummer auswählen", sample_numbers)
        else:  # Registrierte Benutzer-Ergebnisse
            sample_numbers = list(set(result[0] for result in results))
            selected_sample = st.selectbox("Probenummer auswählen", sample_numbers)

        if selected_sample:
            data = {name: [0, 0, 0] for name in button_names}  # Mit Nullen initialisieren

            if isinstance(results[0], dict):  # Gast-Ergebnisse
                for result in results:
                    if result['sample_number'] == selected_sample:
                        sample_number = result['sample_number']
                        count_session = result['count_session']
                        date = result['date']
                        counts = result['counts']

                        if count_session == 1:
                            for name in button_names:
                                data[name][0] = counts.get(name, 0)
                        else:
                            for name in button_names:
                                data[name][1] = counts.get(name, 0)
            else:  # Registrierte Benutzer-Ergebnisse
                for result in results:
                    if result[0] == selected_sample:
                        sample_number = result[0]
                        count_session = result[1]
                        date = result[2]
                        counts_str = result[3]
                        counts = dict(item.split(":") for item in counts_str.split(","))
                        counts = {key: int(value) for key, value in counts.items()}

                        if count_session == 1:
                            for name in button_names:
                                data[name][0] = counts.get(name, 0)
                        else:
                            for name in button_names:
                                data[name][1] = counts.get(name, 0)

            for name in button_names:
                data[name][2] = (data[name][0] + data[name][1]) / 2  # Durchschnitt berechnen

            counts_df = pd.DataFrame(data, index=['1. Zählung', '2. Zählung', 'Durchschnitt']).T.reset_index()
            counts_df.columns = ['Zellentyp', '1. Zählung', '2. Zählung', 'Durchschnitt']
            st.dataframe(counts_df, hide_index=True)

            excel_data = to_excel(counts_df)
            st.download_button(label='Download Excel', data=excel_data, file_name=f'{selected_sample}.xlsx', key=f'download_{selected_sample}')


    if view == "Einführung":
        st.header("Einführung")
        st.write("""
        Willkommen bei der ZellZähler-App!
        
        **Funktionen:**
        - **Probenummer eingeben**: Gib eine eindeutige Probenummer ein, um eine neue Zählung zu starten.
        - **Zählen**: Führe die Zählungen durch, indem du die entsprechenden Knöpfe drückst.
        - **Neuen Zelltyp definieren**: Klicke auf diesen Knopf, um die unteren drei Knöpfe umzubenennen.
        - **Korrigieren**: Ermöglicht das manuelle Korrigieren der Zählerstände. Bitte achte darauf, dass durch die Korrektur nicht mehr als 100 Zellen insgesamt gezählt werden. Im Notfall kannst du den letzten Schritt rückgängig machen.
        - **Rückgängig**: Macht den letzten Zählungsschritt rückgängig.
        - **Zählung zurücksetzen**: Setzt alle Zählerstände auf Null zurück.
        - **Ergebnisse speichern**: Speichert die aktuellen Zählungsergebnisse.
        - **Archiv**: Zeigt alle gespeicherten Zählungsergebnisse an, die nach Probenummern durchsucht werden können.

        Diese App wurde für das Hämatologie Praktikum an der ZHAW erschaffen. Sie hilft beim Differenzieren des weissen Blutbildes. Entwickelt von Sarah 'Viki' Ramos Zähnler und Lucia Schweizer. Die Illustration ist von Sarah 'Viki' Ramos Zähnler.
        """)

    elif view == "Zählen":
        st.session_state['sample_number'] = st.text_input("Probenummer eingeben", value=st.session_state['sample_number'])
        
        if not st.session_state['sample_number']:
            st.warning("Bitte geben Sie eine Probenummer ein, um zu beginnen.")
        else:
            st.subheader(f"Aktuelle Zählungssession: {st.session_state['count_session']}")

            top_columns = st.columns((2, 2, 3))

            with top_columns[0]:
                if st.button('Rückgängig', key='undo_button', help="Macht den letzen Schritt rückgängig.", use_container_width=True):
                    undo_last_step()
                    st.rerun()
            with top_columns[1]:
                if st.button('Korrigieren', help="Manuelle Korrektur der Zählerstände. Mit zweitem Klick den Korrekturmodus beenden.", use_container_width=True):
                    st.session_state['edit_mode'] = not st.session_state['edit_mode']
                    st.rerun()

            with top_columns[2]:
                if st.button('Neuen Zelltyp definieren', help="Individuelle Umbenennung der unteren drei Zählerknöpfe. Die neue Benennung erscheint nicht auf der Tabelle.", use_container_width=True):
                    st.session_state['name_edit_mode'] = not st.session_state['name_edit_mode']
                    st.rerun()
            
            #if st.button('Korrigieren', help="Manuelle Korrektur der Zählerstände. Mit zweiten Klick den Korrekturmodus beenden."):
                #st.session_state['edit_mode'] = not st.session_state['edit_mode']
                #st.rerun()

            #if st.button('Neuen Zelltyp definieren', help="Individuelle Umbenennung der unteren drei Zählerknöpfe. Die neue Benennung erscheint nicht auf der Tabelle."):
                #st.session_state['name_edit_mode'] = not st.session_state['name_edit_mode']
                #st.rerun()

            total_count = sum(st.session_state[f'count_{name}'] for name in button_names)
            st.header(f"{total_count}/100")

            if total_count <= 100:
                st.progress(total_count / 100)

            if total_count == 100:
                st.success("100 Zellen gezählt!")
                st.write("Ergebnisse:")
                if st.session_state.get('result_df') is None:
                    result_df = pd.DataFrame({'Zellentyp': button_names, 'Anzahl': [st.session_state[f'count_{name}'] for name in button_names]})
                    st.session_state['result_df'] = result_df
                st.dataframe(st.session_state['result_df'], hide_index=True)

            if total_count > 100:
                st.error("Die Gesamtzahl darf 100 nicht überschreiten. Bitte mache den letzten Schritt rückgängig oder korrigiere den Zählerstand.")

            
            # Anpassen des Layouts mit spezifischen Spaltenbreiten

            rows = [st.columns((1.5, 1.5, 1.5)) for _ in range(4)]  # 3x4 Grid für Buttons
            button_pressed = None

            for name in button_names:
                index = button_names.index(name)
                row_index, col_index = divmod(index, 3)
                col = rows[row_index][col_index]
                with col:
                    display_name = name
                    if name in ["Div1", "Div2", "Div3"]:
                        display_name = st.session_state['custom_names'][int(name[-1]) - 1]
                    button_label = f"{display_name}\n({st.session_state[f'count_{name}']})"
                    if st.button(button_label, key=f'button_{name}', use_container_width=True):
                        if not st.session_state['edit_mode'] and not st.session_state['name_edit_mode']:
                            save_state()
                            button_pressed = name
                    if st.session_state['edit_mode']:
                        new_count = st.number_input("Zähler korrigieren", value=st.session_state[f'count_{name}'], key=f'edit_{name}')
                        if new_count + sum(st.session_state[f'count_{n}'] for n in button_names if n != name) <= 100:
                            st.session_state[f'count_{name}'] = new_count
                        else:
                            st.error("Die Gesamtzahl darf 100 nicht überschreiten.")

            #cols_per_row = 3
            #rows = [st.columns(cols_per_row) for _ in range(len(button_names) // cols_per_row + 1)]
            #button_pressed = None

            #for name in button_names:
                #index = button_names.index(name)
                #row_index, col_index = divmod(index, cols_per_row)
                #col = rows[row_index][col_index]
                #with col:
                    #display_name = name
                    #if name in ["Div1", "Div2", "Div3"]:
                        #display_name = st.session_state['custom_names'][int(name[-1]) - 1]
                    #button_label = f"{display_name}\n({st.session_state[f'count_{name}']})"
                    #if st.button(button_label, key=f'button_{name}'):
                        #if not st.session_state['edit_mode'] and not st.session_state['name_edit_mode']:
                            #save_state()
                            #button_pressed = name
                    #if st.session_state['edit_mode']:
                        #new_count = st.number_input("Zähler korrigieren", value=st.session_state[f'count_{name}'], key=f'edit_{name}')
                        #st.session_state[f'count_{name}'] = new_count

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

            st.markdown("<br>", unsafe_allow_html=True)
        

            bottom_columns = st.columns((2, 2, 2))

            with bottom_columns[0]:
                if st.button('Zählung zurücksetzen', help="Setzt alle Zählerstände wieder auf null.", use_container_width=True):
                    reset_counts()
                    st.rerun()

            with bottom_columns[2]:
                if st.session_state['count_session'] == 1:
                    if st.button("Speichern & weiter zu 2. Zählung", use_container_width=True):
                        if total_count == 100:
                            save_results()
                            reset_counts()
                            st.session_state['count_session'] = 2
                        else:
                            st.error("Die Gesamtzahl der Zellen muss 100 sein. Bitte korrigiere die Zählerstände.")

                if st.session_state['count_session'] == 2:
                    if st.button("Zählung beenden & archivieren", help="Die gespeicherten Ergebnisse sind im Archiv sichtbar.", use_container_width=True):
                        if total_count == 100:
                            save_results()
                            reset_counts()
                            st.session_state['count_session'] = 1
                        else:
                            st.error("Die Gesamtzahl der Zellen muss 100 sein. Bitte korrigiere die Zählerstände.")

            #if st.button('Rückgängig', key='undo_button', help="Macht den letzen Schritt rückgängig."):
                #undo_last_step()
                #st.rerun()

            #if st.button('Zählung zurücksetzen', help="Setzt alle Zählerstände wieder auf null"):
                #reset_counts()
                #st.rerun()

            #if st.session_state['count_session'] == 1:
                #if st.button("Speichern & weiter zu 2. Zählung"):
                    #if total_count == 100:
                        #save_results()
                        #reset_counts()
                        #st.session_state['count_session'] = 2
                    #else:
                        #st.error("Die Gesamtzahl der Zellen muss 100 sein. Bitte korrigieren Sie die Zählerstände.")

            #if st.session_state['count_session'] ==2:
                #if st.button("Zählung beenden & archivieren", help="Die gespeicherten Ergebnisse sind im Archiv sichtbar."):
                    #if total_count == 100:
                        #save_results()
                        #reset_counts()
                        #st.session_state['count_session'] = 1
                    #else:
                        #st.error("Die Gesamtzahl der Zellen muss 100 sein. Bitte korrigieren Sie die Zählerstände.")

    elif view == "Archiv":
        st.header("Archivierte Ergebnisse")
        if st.session_state['guest']:
            display_results(st.session_state.get('guest_results', []))
        else:
            display_results(st.session_state.get('results', []))
            
    elif view == "Account":
        st.header("Account-Verwaltung")
        if st.button("Passwort ändern"):
            st.session_state['change_password'] = True
        if st.button("Account löschen"):
            st.session_state['delete_account'] = True

        if 'change_password' in st.session_state and st.session_state['change_password']:
            new_password = st.text_input("Neues Passwort", type="password")
            confirm_password = st.text_input("Passwort bestätigen", type="password")
            if st.button("Passwort ändern"):
                if new_password and confirm_password:
                    if new_password == confirm_password:
                        users = load_user_data()
                        users[st.session_state['username']]['password'] = encrypt_password(new_password)
                        save_user_data(users)
                        st.success("Passwort erfolgreich geändert.")
                        st.session_state['change_password'] = False
                    else:
                        st.error("Passwörter stimmen nicht überein.")
                else:
                    st.error("Bitte fülle alle Felder aus.")
            if st.button("Abbrechen"):
                st.session_state['change_password'] = False

        if 'delete_account' in st.session_state and st.session_state['delete_account']:
            if st.button("Bestätigen"):
                users = load_user_data()
                del users[st.session_state['username']]
                save_user_data(users)
                st.success("Account erfolgreich gelöscht.")
                st.session_state['authenticated'] = False
                st.session_state['delete_account'] = False
            if st.button("Abbrechen"):
                st.session_state['delete_account'] = False
