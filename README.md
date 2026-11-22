# V380 Mac 3.14.23 - Gallery compatta e informazioni anteprime

Avviare **Avvia_V380_Mac.command** nella radice di QUESTO pacchetto. Chiudere prima la vecchia app con Ferma Live e Esci. Conservare la versione precedente come rollback. Il problema del vecchio avvio .app non e dichiarato risolto.

## Gallery
- Checkbox a sinistra del titolo, in alto. Titolo su UNA RIGA con carattere ridotto. Su spazi molto stretti compare ellissi; il tooltip conserva il titolo completo.
- Immagine al centro, indicatori in basso: occhio per Parti significative, simbolo a punti per Uniforme, spia MP4 verde/rossa a destra.
- Nessun testo Seleziona video, Parti significative o Video salvato ripetuto nella card. Tooltip e pannello contengono i dettagli.
- Se resta solo la GIF il checkbox e disabilitato: la selezione massiva riguarda gli MP4, non le GIF.
- Palette colori spostata nella sidebar, fra V380 Mac e Live.

## Pannello al clic sull'immagine
Mantiene azioni video/GIF e aggiunge dati della GIF: nome, percorso, dimensione effettiva, data di modifica del file, risoluzione, numero fotogrammi e durata misurati con FFprobe, metodo/intervallo/sensibilita/eventi/fallback quando disponibili nel report di generazione. I vecchi file senza report non vengono classificati a intuito. Data modifica NON e necessariamente data di creazione. Se FFprobe manca, rimangono i dati filesystem e il report.

Se l'MP4 manca, compaiono Scarica video dalla SD (con conferma) e Riproduci dalla SD. Non viene ricostruito il filmato originale dalla GIF: viene cercata la registrazione originale nella microSD usando il timestamp del nome. Si controllano anche giorni adiacenti per compatibilita con correzione oraria/mezzanotte. Se non e piu presente, si segnala errore senza scaricare un altro filmato a caso. La data/elenco attualmente caricati non vengono sostituiti dalla ricerca.

Riproduci dalla SD usa il player progressivo VLC gia presente e non aggiunge un MP4 alla Gallery. Scarica invece salva il video. Audio opzionale come nella 3.14.22. Non eseguire contemporaneamente altre operazioni SD. La nuova risoluzione da GIF va collaudata sulla telecamera reale, soprattutto per registrazioni vecchie/correzione oraria.

## Icona
Icona macOS ICNS generata dall'immagine legno/ottone fornita dall'utente, inclusa nel bundle e PNG nella sidebar. Il launcher .command apre Terminale: l'icona Dock di Terminale non viene cambiata. Il bundle resta non firmato/non notarizzato e non autonomo.

## Profili e funzioni conservati
Uniforme: Default 50 frame, GIF 10s, sorgente 10-60s. Parti significative: Default 30 frame, GIF 7s, dal secondo 1 alla fine effettiva; campo numerico 120 come convenzione fine video. Default contestuale, profili separati. Le GIF esistenti non vengono rigenerate automaticamente. Movimento non equivale a persone.
Live RTSP e generazione anteprime/audio download invariati. Nessuna nuova funzione Live o riconoscimento persone introdotta qui.

## Pacchetto pubblico
Sorgenti completi, risorse, launcher, app in dist, script e test. Nessun IP/Device ID/username personale precompilato, nessun log, filmato o campione privato. Configurazione e Portachiavi sul Mac restano esterni. Richiede Python 3.9+, FFmpeg/FFprobe e VLC. Nessuna licenza assegnata automaticamente; l'immagine icona e quella fornita dall'utente, verificarne i diritti prima della pubblicazione.

## Verifiche locali
Sintassi Python/JS, regressioni movimento e audio playback con video/audio sintetici, test backend con ricerca SD simulata, metadati di una GIF di prova, download su snapshot senza modificare elenco corrente. Test browser Chromium con API simulate: card compatta, checkbox, palette sidebar, dialog informazioni e azione stream da GIF, nessun errore JavaScript. Non testato su macOS/telecamera fisica. Nessuna garanzia di sincronizzazione audio nuova.

```bash
python3 scripts/build_macos.py
python3 -m unittest discover -s tests -v
node tests/test_preview_profiles.cjs
```

Il test opzionale browser `python3 tests/browser_gallery.py` richiede Playwright e Chromium installati; BROWSER_PATH puo indicare un eseguibile locale. Non necessario per usare l'app.
