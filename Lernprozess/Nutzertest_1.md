# 1. Nutzertest

## Hypothesen

- Wir wollen den Nutzertest in 15min machen, starten aber eine Stoppuhr, weil es wahrscheinlich eher länger dauern wird.

- Um die Situation im Hämatologie-Praktikum zu simulieren, genügt folgendes:
  - Hämatologie-Protokoll + Stift = ausgedrucktes Hämatologie-Protokoll + Stift
  - App auf Smartphone = 4 ausgedruckte Wireframes in Smartphone-Bildschirmgröße
  - Mikroskop + Blutausstrich = Bilder von Leukozyten am Laptop
  - 10 Zellen zu zählen genügt, es braucht nicht 100

- Das Design der Wireframes ist ziemlich ästhetisch und schlicht.
- Wir haben wenig Knöpfe.
- Alle Knöpfe sind selbsterklärend.
- Knöpfe sind gut sichtbar.
- Nutzer verstehen, dass es einen Knopf gibt, um das 2. 100 zu zählen.
- Nutzer verstehen, dass die Ergebnistabelle 1x1 zum Protokoll vom Praktikum passt.

- Nutzer verstehen und schätzen, dass es 9 Knöpfe gibt und man 3 neue Knöpfe hinzufügen kann.
  - Es gibt eine Undo-Taste.
  - Nach 200 gezählten Zellen wird der Durchschnitt automatisch berechnet.

- Nutzer wissen überhaupt nicht, wie lange sie pro Blutbild brauchen.
- Nutzer schreiben sich nicht regelmäßig auf, wie lange sie pro BB brauchen, haben also keine Daten.
- Nutzer würden Daten zu ihrer 'Zählgeschwindigkeit' schätzen.

- Nutzer würden eine Vibration beim Antippen einer Taste einem Piepston bevorzugen.
- Ein Piepston nach 100 ausgezählten Zellen ist ein klares Zeichen, dass man fertig ist.

- Der größte Nutzen der App ist die Zeiteinsparung.
- Die ZellZähler App ist besser als die Verwendung von Papier und Stift zum Zählen.
- Die ZellZähler App ist besser als die CellCounter App.

## Was war gut?

- Die App ist effektiver als von Hand zu zählen und sie kann bereits den Durchschnitt berechnen.
- Es ist praktisch, dass man das Protokoll als Dokument abspeichern und versenden kann.
- Die Funktion mit der Zeitmessung, mit der man seine Fortschritte über einen Zeitraum festhalten kann, ist gut.

## Was war schlecht?

- Es wurde erwartet, dass man noch ein Archiv mit vorherigen Daten hat.
  - Dieses Archiv könnte man über das Benutzer-Icon erreichen, wenn man eingeloggt ist.
  - Diese Funktion hatten wir in unserem Wireframe noch nicht implementiert.
- Ebenso war noch unklar, wo man die Nummer des Blutbildes notieren kann, damit man weiß, zu was die Zählung gehört.
- Bei „gespeicherte Resultate“ ist der Knopf für die zweite Zählung nicht intuitiv.

## Neue Ideen

- Die „Benutzer“-Seite überarbeiten.
  - Statt Knopf für letzte Zählung zurück, eine intuitivere, praktischere Funktion z.B. Knopf „Bearbeiten“, dadurch gehen alle Zählerknöpfe in den Bearbeitungsmodus und können mit + und – Tasten bearbeitet werden.

## Neue Probleme

- Bei der Zeitzählung die Knöpfe vereinfachen (3 Knöpfe unnötig).
- Die beiden Knöpfe „Zähler“ und „gespeicherte Resultate“ anders gestalten/entfernen.
- Bei den gespeicherten Resultaten den Knopf „2. 100“ verbessern (ist verwirrend).
- Die Größe vom Handybildschirm könnte ein Problem sein, für das es keine Lösung gibt.
- Papierkorb strategisch verwenden, damit der Nutzer keine Angst hat, aus Versehen seine gespeicherten Daten zu löschen.
