# Staatsoper Unter den Linden Berlin – Opernkalender (iCal)

Ein **automatisch aktualisierbares Abonnement** für Opernvorstellungen an der Staatsoper Unter den Linden, Berlin. Nur Aufführungen vor Ort; keine Orchesterkonzerte, Ballette oder Führungen. Auch halbszenische Opern werden berücksichtigt.

## Installation auf GitHub

1. Neues **öffentliches** GitHub-Repository erstellen, z. B. `staatsoper-berlin-calendar`.
2. Den gesamten Inhalt dieses ZIP-Archivs ins Repository hochladen. **Wichtig:** `.github/workflows/update.yml` ist versteckt. Falls der Browser versteckte Ordner nicht zuverlässig hochlädt, auf GitHub nacheinander **Add file → Create new file** wählen und als Dateinamen `.github/workflows/update.yml` eingeben; den mitgelieferten Inhalt einfügen.
3. Unter **Actions → Update Staatsoper Berlin opera calendar → Run workflow** die erste Aktualisierung starten. Falls verlangt, Actions und Schreibrechte unter **Settings → Actions → General → Workflow permissions → Read and write permissions** erlauben.
4. Nach erfolgreichem Workflow den folgenden Link mit `DEIN_GITHUB_NAME` und gegebenenfalls dem Repository-Namen anpassen und **als Kalender-Abo** in Apple Kalender öffnen:

   `https://raw.githubusercontent.com/DEIN_GITHUB_NAME/staatsoper-berlin-calendar/main/staatsoper-berlin-opera.ics`

   Für iCal kann auch `webcal://raw.githubusercontent.com/DEIN_GITHUB_NAME/staatsoper-berlin-calendar/main/staatsoper-berlin-opera.ics` verwendet werden.

## Eigenschaften

- Offizielle Quelle: https://www.staatsoper-berlin.de/de/spielplan/
- Zeitzone `Europe/Berlin`; korrekte Sommer-/Winterzeit.
- Originale Uhrzeit, mit offizieller Dauer wo verfügbar. Sonst wird **nur als Platzhalter** ein 3-Stunden-Zeitblock gesetzt und ausdrücklich gekennzeichnet.
- Erinnerungen als vier VALARMs pro Vorstellung: 90, 30, 7 und 1 Tag vorher (90/30 Tage als Näherung für 3/1 Monate).
- Tägliche automatische Aktualisierung, bei neuen Spielzeiten fortlaufend.
- Bei fehlgeschlagenem Abruf bleibt die zuletzt veröffentlichte `.ics` unverändert. Diesen Fall unter **Actions** prüfen.
- Aktualisierung durch einen nicht-offiziellen Parser; Änderungen am offiziellen Website-Layout können eine Korrektur des Scrapers erforderlich machen. Termine und Besetzungen vor Buchung stets offiziell prüfen.

**Hinweis:** Es gibt hier keinen separaten Vorverkaufskalender, da Veröffentlichungstermine für einzelne Verkaufsfenster nicht aus dem Spielplan abgeleitet werden können. Der Kalender ist noch nicht live: Erst nach Upload und erfolgreichem GitHub-Workflow werden die abonnierten Daten aktualisiert.
