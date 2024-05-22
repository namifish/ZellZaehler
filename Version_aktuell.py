import streamlit as st
import pandas as pd
import os
import bcrypt
from datetime import datetime
import sqlite3
import io
import base64
import time
from github_contents import GithubContents

# GitHub-Verbindung herstellen
github = GithubContents(
    st.secrets["github"]["owner"],
    st.secrets["github"]["repo"],
    st.secrets["github"]["token"]
)

# Verwende secrets für die Dateipfade
LOGIN_FILE = st.secrets["data"]["LOGIN_FILE"]
DB_FILE = st.secrets["data"]["DB_FILE"]

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

# Hintergrund festlegen (transparente Version)
set_background('images/hintergrundtransparent.png')

# SQLite-Datenbank initialisieren
def init_db():
    conn = sqlite3.connect(DB_FILE)
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

def init_user_data():
    try:
        github.read_text(LOGIN_FILE)
    except github.NotFound:
        # Datei existiert nicht, initialisieren Sie eine neue DataFrame und speichern Sie sie
        df = pd.DataFrame(columns=['username', 'password'])
        save_user_data(df)
    except Exception as e:
        st.error(f"Fehler beim Initialisieren der Benutzerdaten: {e}")


def load_user_data():
    try:
        csv_content = github.read_text(LOGIN_FILE)
        users = pd.read_csv(io.StringIO(csv_content))
    except Exception as e:
        st.error(f"Fehler beim Laden der Benutzerdaten: {e}")
        users = pd.DataFrame(columns=['username', 'password'])
    return users


def save_user_data(data):
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    try:
        file_content = github.read_text(LOGIN_FILE)
        github.write_text(LOGIN_FILE, csv_buffer.getvalue(), "Update user data")
    except github.NotFound:
        github.write_text(LOGIN_FILE, csv_buffer.getvalue(), "Create user data file")
    except Exception as e:
        st.error(f"Fehler beim Speichern der Benutzerdaten: {e}")


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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    counts_str = ','.join(f'{key}:{value}' for key, value in current_counts.items())
    c.execute('''INSERT INTO results (username, sample_number, count_session, date, counts)
                 VALUES (?, ?, ?, ?, ?)''', (username, sample_number, count_session, date_time, counts_str))
    conn.commit()
    conn.close()

# Benutzerergebnisse abrufen
def get_user_results(username):
    conn = sqlite3.connect(DB_FILE)
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

## Funktion zum Anzeigen des Inhalts der Datei
#def display_file_contents(file_path):
    #try:
        #with open(file_path, 'r') as file:
            #contents = file.read()
            #st.text("Inhalt der Datei:")
            #st.text(contents)
    #except Exception as e:
        #st.write(f"Fehler beim Lesen der Datei: {e}")

## Zeige den Inhalt der Datei an
#display_file_contents(LOGIN_FILE)


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

# Prüfen, ob der Benutzer authentifiziert ist oder als Gast angemeldet ist
if not st.session_state['authenticated'] and not st.session_state['guest']:
    # Wenn der Benutzer sich registrieren möchte
    if st.session_state['register']:
        st.subheader("Registrieren")
        reg_username = st.text_input("Wähle einen Benutzernamen")
        reg_password = st.text_input("Wähle ein Passwort", type="password")
        reg_confirm_password = st.text_input("Passwort bestätigen", type="password")
        register_columns = st.columns((0.5,3,3,0.5))

        with register_columns[1]:
            if st.button("Registrieren", use_container_width=True):
                # Überprüfen, ob alle Felder ausgefüllt sind und die Passwörter übereinstimmen
                if reg_username and reg_password and reg_confirm_password:
                    if reg_password == reg_confirm_password:
                        if register_user(reg_username, reg_password):
                            st.success("Registrierung erfolgreich. Du kannst dich jetzt einloggen.")
                            st.session_state['register'] = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Benutzername existiert bereits. Bitte wähle einen anderen Benutzernamen.")
                    else:
                        st.error("Passwörter stimmen nicht überein.")
                else:
                    st.error("Bitte fülle alle erforderlichen Felder aus.")

        with register_columns[2]:
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['register'] = False
                st.rerun()
    # Wenn der Benutzer sich einloggen möchte
    else:
        st.subheader("Login")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        login_columns = st.columns((0.5,3,3,3,0.5))

        with login_columns[1]:
            if st.button("Login",use_container_width=True):
                # Überprüfen, ob Benutzername und Passwort ausgefüllt sind
                if username and password:
                    if verify_user(username, password):
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['results'] = get_user_results(username)
                        st.rerun()
                    else:
                        st.error("Ungültiger Benutzername oder Passwort.")
                else:
                    st.error("Bitte gib sowohl Benutzernamen als auch Passwort ein.")

        with login_columns[2]:
            if st.button("Registrieren",use_container_width=True):
                st.session_state['register'] = True
                st.rerun()

        with login_columns[3]:
            if st.button("Weiter als Gast",use_container_width=True):
                st.session_state['guest'] = True
                if 'guest_results' not in st.session_state:
                    st.session_state['guest_results'] = []
                    st.rerun()
# Wenn der Benutzer authentifiziert ist oder als Gast angemeldet ist
else:
    st.sidebar.header("Navigation")
    view = st.sidebar.radio("Ansicht wählen", ["Einführung", "Zählen", "Archiv", "Account"])

    # Initialisieren der Sitzungszustände
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

    # Funktion zum Erhöhen des Zählerwerts eines Knopfes
    def increment_button_count(name):
        total_count = sum(st.session_state[f'count_{name}'] for name in button_names)
        if total_count >= 100:
            st.error("Das Zählziel von 100 wurde bereits erreicht.")
        else:
            st.session_state[f'count_{name}'] += 1
            st.rerun()

    # Funktion zum Speichern des aktuellen Zustands
    def save_state():
        current_counts = {name: st.session_state[f'count_{name}'] for name in button_names}
        st.session_state['history'].append(current_counts)

    # Funktion zum Rückgängigmachen des letzten Schrittes
    def undo_last_step():
        if st.session_state['history']:
            last_state = st.session_state['history'].pop()
            for name in button_names:
                st.session_state[f'count_{name}'] = last_state[name]
            st.rerun()

    # Funktion zum Zurücksetzen der Zählerstände
    def reset_counts():
        for name in button_names:
            st.session_state[f'count_{name}'] = 0
        st.rerun()

    # Funktion zum Speichern der Zählergebnisse
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

    # Funktion zum Anzeigen der gespeicherten Ergebnisse
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
            st.download_button(label='Excel runterladen', data=excel_data, file_name=f'{selected_sample}.xlsx', key=f'download_{selected_sample}')

    # Anzeige der verschiedenen Ansichten basierend auf der Benutzerwahl
    if view == "Einführung":
        if st.session_state['guest']:
        # Hintergrund für die Einführung
            set_background('images/hintergrund.png')
            st.header("Einführung")
            st.write("""
            Willkommen bei der ZellZähler-App!
            
            **Funktionen:**
            - **Probenummer eingeben**: Gib eine eindeutige Probenummer ein, um eine neue Zählung zu starten.
            - **Zählen**: Führe die Zählungen durch, indem du die entsprechenden Knöpfe drückst.
            - **Neuen Zellentyp definieren**: Klicke auf diesen Knopf, um die unteren drei Knöpfe umzubenennen.
            - **Korrigieren**: Ermöglicht das manuelle Korrigieren der Zählerstände.
            - **Rückgängig**: Macht den letzten Schritt rückgängig.
            - **Zählung zurücksetzen**: Setzt alle Zählerstände auf Null zurück.
            - **Ergebnisse speichern**: Nach jeder Session die aktuellen Zählungsergebnisse speichern und archivieren.
            - **Archiv**: Zeigt alle gespeicherten Zählungsergebnisse an, die nach Probenummern durchsucht werden können.

            Diese App wurde für das Hämatologie Praktikum an der ZHAW erschaffen. Sie hilft beim Differenzieren des weissen Blutbildes. Entwickelt von Sarah 'Viki' Ramos Zähnler und Lucia Schweizer. Die Illustration ist von Sarah 'Viki' Ramos Zähnler.
            """)
        else:
            # Hintergrund für die Einführung
            set_background('images/hintergrund.png')
            st.header("Einführung")
            st.write(f"""
            Willkommen bei der ZellZähler-App, {st.session_state['username']}!

            **Funktionen:**
            - **Probenummer eingeben**: Gib eine eindeutige Probenummer ein, um eine neue Zählung zu starten.
            - **Zählen**: Führe die Zählungen durch, indem du die entsprechenden Knöpfe drückst.
            - **Neuen Zellentyp definieren**: Klicke auf diesen Knopf, um die unteren drei Knöpfe umzubenennen.
            - **Korrigieren**: Ermöglicht das manuelle Korrigieren der Zählerstände.
            - **Rückgängig**: Macht den letzten Schritt rückgängig.
            - **Zählung zurücksetzen**: Setzt alle Zählerstände auf Null zurück.
            - **Ergebnisse speichern**: Nach jeder Session die aktuellen Zählungsergebnisse speichern und archivieren.
            - **Archiv**: Zeigt alle gespeicherten Zählungsergebnisse an, die nach Probenummern durchsucht werden können.

            Diese App wurde für das Hämatologie Praktikum an der ZHAW erschaffen. Sie hilft beim Differenzieren des weissen Blutbildes. Entwickelt von Sarah 'Viki' Ramos Zähnler und Lucia Schweizer. Die Illustration ist von Sarah 'Viki' Ramos Zähnler.
            """)

    # Ansicht "Zählen"
    elif view == "Zählen":
        st.session_state['sample_number'] = st.text_input("Probenummer eingeben", value=st.session_state['sample_number'])
        
        # Warnung, wenn keine Probenummer eingegeben wurde
        if not st.session_state['sample_number']:
            st.warning("Bitte gib eine Probenummer ein, um zu beginnen.")
        else:
            # Anzeige der aktuellen Zählungssession
            st.subheader(f"Aktuelle Zählungssession: {st.session_state['count_session']}")

            top_columns = st.columns((2, 2, 3))

            # Rückgängig-Button: Macht den letzten Zählschritt rückgängig
            with top_columns[0]:
                if st.button('Rückgängig', key='undo_button', help="Macht den letzen Schritt rückgängig.", use_container_width=True):
                    undo_last_step()
                    st.rerun()
            # Korrigieren-Button: Ermöglicht die manuelle Korrektur der Zählerstände
            with top_columns[1]:
                if st.button('Korrigieren', help="Manuelle Korrektur der Zählerstände. Mit zweitem Klick den Korrekturmodus beenden.", use_container_width=True):
                    st.session_state['edit_mode'] = not st.session_state['edit_mode']
                    st.rerun()

            # Button für die Definition eines neuen Zellentyps: Ermöglicht die Umbenennung der unteren Zählerknöpfe
            with top_columns[2]:
                if st.button('Neuen Zellentyp definieren', help="Individuelle Umbenennung der unteren drei Zählerknöpfe. Die neue Benennung erscheint nicht auf der Tabelle.", use_container_width=True):
                    st.session_state['name_edit_mode'] = not st.session_state['name_edit_mode']
                    st.rerun()

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
                    if st.button("Speichern & weiter zur 2. Zählung", use_container_width=True):
                        if total_count == 100:
                            save_results()
                            reset_counts()
                            st.session_state['count_session'] = 2
                        else:
                            st.error("Die Gesamtzahl der Zellen muss 100 betragen.")

                if st.session_state['count_session'] == 2:
                    if st.button("Zählung beenden & archivieren", help="Die gespeicherten Ergebnisse sind im Archiv sichtbar.", use_container_width=True):
                        if total_count == 100:
                            save_results()
                            reset_counts()
                            st.session_state['count_session'] = 1
                        else:
                            st.error("Die Gesamtzahl der Zellen muss 100 betragen.")
    # Ansicht "Archiv"
    elif view == "Archiv":
        st.header("Archivierte Ergebnisse")
        if st.session_state['guest']:
            st.warning("Archivierte Daten im Gästelogin können verlorengehen.")
            display_results(st.session_state.get('guest_results', []))
        else:
            display_results(st.session_state.get('results', []))
            
    # Ansicht "Account"
    elif view == "Account":
        st.header("Account-Verwaltung")
        if st.session_state['guest']:
            st.warning("Nicht angemeldet. Achtung: Archivierte Daten im Gästelogin können verlorengehen.")
            if st.button("Zurück zum Login", key="guest_back_to_login"):
                st.session_state['authenticated'] = False
                st.session_state['guest'] = False
                st.session_state['register'] = False
                st.rerun()
        else:
            st.write(f"**Eingeloggter User:** {st.session_state['username']}")

            grid_columns = st.columns((2,2,1))

            with grid_columns[0]:
                if st.button("Passwort ändern", key="change_password_button", use_container_width=True):
                    st.session_state['change_password'] = True
                if st.button("Benutzernamen ändern", key="change_username_button", use_container_width=True):
                    st.session_state['change_username'] = True

            with grid_columns[1]:
                if st.button("Account löschen", key="delete_account_button", use_container_width=True):
                    st.session_state['delete_account'] = True
                if st.button("Abmelden", key="logout_button", use_container_width=True):
                    st.success(f"Auf Wiedersehen, {st.session_state['username']}!")
                    st.session_state['authenticated'] = False
                    st.session_state['guest'] = False
                    st.session_state['register'] = False
                    time.sleep(2)
                    st.rerun()

            # Passwort ändern
            if 'change_password' in st.session_state and st.session_state['change_password']:
                new_password = st.text_input("Neues Passwort", type="password", key="new_password")
                confirm_password = st.text_input("Passwort bestätigen", type="password", key="confirm_password")
                if st.button("Passwort ändern", key="confirm_change_password"):
                    if new_password and confirm_password:
                        if new_password == confirm_password:
                            users = load_user_data()
                            users.loc[users['username'] == st.session_state['username'], 'password'] = encrypt_password(new_password)
                            save_user_data(users)
                            st.success("Passwort erfolgreich geändert.")
                            st.session_state['change_password'] = False
                            time.sleep(4)
                            st.rerun()
                        else:
                            st.error("Passwörter stimmen nicht überein.")
                    else:
                        st.error("Bitte fülle alle Felder aus.")
                if st.button("Abbrechen", key="cancel_change_password"):
                    st.session_state['change_password'] = False
                    st.rerun()

            # Benutzername ändern
            if 'change_username' in st.session_state and st.session_state['change_username']:
                new_username = st.text_input("Neuer Benutzername", key="new_username")
                if st.button("Benutzernamen ändern", key="confirm_change_username"):
                    if new_username:
                        users = load_user_data()
                        if new_username not in users['username'].values:
                            users.loc[users['username'] == st.session_state['username'], 'username'] = new_username
                            save_user_data(users)
                            st.session_state['username'] = new_username
                            st.success("Benutzername erfolgreich geändert.")
                            st.session_state['change_username'] = False
                            time.sleep(4)
                            st.rerun()

                        else:
                            st.error("Benutzername existiert bereits.")
                    else:
                        st.error("Bitte gib einen neuen Benutzernamen ein.")
                if st.button("Abbrechen", key="cancel_change_username"):
                    st.session_state['change_username'] = False
                    st.rerun()

            # Account löschen
            if 'delete_account' in st.session_state and st.session_state['delete_account']:
                st.warning("Achtung: Alle archivierten Daten gehen verloren.")
                if st.button("Account löschen: bestätigen", key="confirm_delete_account"):
                    users = load_user_data()
                    users = users[users['username'] != st.session_state['username']]
                    save_user_data(users)
                    st.success("Account erfolgreich gelöscht. Du wirst automatisch zum Login weitergeleitet.")
                    st.session_state['authenticated'] = False
                    st.session_state['delete_account'] = False
                    time.sleep(4)
                    st.rerun()
                if st.button("Abbrechen", key="cancel_delete_account"):
                    st.session_state['delete_account'] = False