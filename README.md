# ZellZaehler
ZellZähler ist eine Streamlit-basierte Anwendung um manuell Zellen zu zählen. Die App bietet Funktionen zur Benutzerregistrierung und -anmeldung, Speicherung von Zählungsergebnissen und deren Export in Excel-Dateien.

## Funktionen

- **Hintergrundbild setzen**: Anpassung des Hintergrundbildes der Anwendung.
- **Benutzerregistrierung und -anmeldung**: Sichere Speicherung von Benutzerdaten mit verschlüsselten Passwörtern.
- **Zählungsergebnisse speichern**: Speichern und Abrufen von Zellzählungsergebnissen in einer SQLite-Datenbank.
- **Datenexport**: Export der Ergebnisse in Excel-Dateien.

## Installation

1. Klonen Sie das Repository:
    ```bash
    git clone https://github.com/IhrBenutzername/ZellZähler.git
    cd ZellZähler
    ```

2. Erstellen Sie eine virtuelle Umgebung und aktivieren Sie sie:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Installieren Sie die Abhängigkeiten:
    ```bash
    pip install -r requirements.txt
    ```

## Verwendung

1. Starten Sie die Streamlit-Anwendung:
    ```bash
    streamlit run app.py
    ```

2. Öffnen Sie Ihren Webbrowser und gehen Sie zu `http://localhost:8501`, um die ZellZähler-App zu verwenden.

## Konfigurationsdateien

- **`hintergrund.png`**: Das Hintergrundbild für die Anwendung.
- **`login_hashed_password_list.csv`**: Die Datei zur Speicherung der Benutzeranmeldedaten.
- **`zellzaehler.db`**: Die SQLite-Datenbank zur Speicherung der Zählungsergebnisse.

## Funktionsübersicht

### set_background(png_file)

Legt das Hintergrundbild der Anwendung fest. Das Hintergrundbild wurde von namifish selbst gestaltet.

### init_db()

Initialisiert die SQLite-Datenbank und erstellt die Tabelle für die Zählungsergebnisse.

### init_user_data()

Initialisiert die Benutzeranmeldedaten. Erstellt eine CSV-Datei, falls diese nicht existiert.

### load_user_data()

Lädt die Benutzeranmeldedaten aus der CSV-Datei.

### save_user_data(data)

Speichert die Benutzeranmeldedaten in der CSV-Datei.

### encrypt_password(password)

Verschlüsselt ein Passwort mit bcrypt.

### verify_password(password, hashed)

Überprüft ein Passwort gegen einen verschlüsselten Hash.

### verify_user(username, password)

Überprüft die Anmeldedaten eines Benutzers.

### register_user(username, password)

Registriert einen neuen Benutzer.

### save_user_results(username, sample_number, count_session, date_time, current_counts)

Speichert die Zählungsergebnisse eines Benutzers in der SQLite-Datenbank.

### get_user_results(username)

Ruft die Zählungsergebnisse eines Benutzers aus der SQLite-Datenbank ab.

### to_excel(df)

Konvertiert ein DataFrame in eine Excel-Datei.

## Beitrag

Beiträge + Pull-Requests sind willkommen!
