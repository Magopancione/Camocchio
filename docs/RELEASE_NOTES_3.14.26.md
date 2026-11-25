# V380 Mac 3.14.26 - Registrazioni e navigazione riorganizzate

## Avvio
Conservare la 3.14.25: l'utente ha confermato audio e video streaming microSD corretti. Chiudere la precedente istanza con Ferma Live e Esci, estrarre in una nuova cartella e avviare Avvia_V380_Mac.command di QUESTO pacchetto. Il problema del vecchio avvio .app non e dichiarato risolto. Bundle incluso non firmato/non notarizzato, Python/FFmpeg non incorporati.

## Nuova interfaccia
- Vista iniziale Registrazioni, con card compatte collegate da linea verticale/nodi alla giornata. La distribuzione oraria orizzontale rimane disponibile sopra le card.
- 100% verde se l'MP4 locale esiste; durante download progressione percentuale. 100% indica presenza locale, non una nuova verifica di integrita del file. Il valore durante ricezione conserva la stima del backend precedente.
- Se video locale: Apri video locale, Apri/Genera anteprima, Dettagli. Nessuno streaming SD ridondante nella card scaricata.
- Se manca video: Scarica, Riproduci dalla microSD; se c'e GIF, anche Apri anteprima e Dettagli.
- Clic sulla card con file locale apre Gallery ed evidenzia l'elemento. Card senza file locale seleziona la registrazione per il comando Scarica selezionato. Pulsanti interni non attivano il clic della card.
- Data unica nella sidebar sotto testata e sopra Live, con frecce. Sempre disponibile nelle tre viste. Cambiare data durante SD/download viene rifiutato dal backend come prima e la UI ripristina la giornata caricata.
- Gallery e Live sono viste separate, non mostrate contemporaneamente a Registrazioni. Il cambio vista non ferma automaticamente Live o SD: usare i comandi Ferma.
- Aggiorna nella testata Registrazioni. Comandi giornata nella stessa sezione.
- Icona colori vettoriale coerente, chiusura dopo scelta, clic fuori o Esc. Se salvataggio fallisce resta il messaggio di errore gia esistente.
- Impostazioni: categorie a sinistra e campi a destra, Telecamera / Anteprime / Riproduzione / Archiviazione / Interfaccia. Su schermi piccoli categorie sopra. Audio SD e RTSP in Riproduzione, cartella in Archiviazione. Salva continua a salvare tutti i campi, anche categorie nascoste.
- Stato SD compatto; contatori audio e MB sotto Dettagli tecnici espandibile.

## Conservazione funzioni
sd_playback.py e motion_preview.py identici alla 3.14.25 allegata. Login, Live, download e MP4 audio confrontati via AST e invariati. Nessun nuovo protocollo o codec. Profili anteprime e cambio modalita singola conservati. Nessuna cancellazione sulla microSD. Preferenze locali e Portachiavi restano esterni e vengono riutilizzati.

## Test
Sintassi Python/JS; test browser Chromium con API simulate per viste, card, 100%, assenza stream ridondante, data sidebar, categorie impostazioni e chiusura colori; regressioni con audio/video sintetici, test profili anteprime e backend Gallery. Non eseguito collaudo su Mac/telecamera in questa sessione. La nuova UI richiede prova utente.

## Stato sviluppi
Audio streaming SD confermato funzionante dall'utente nella 3.14.25, preservato. Rilevamento persone rimosso dalle richieste: il movimento e sufficiente per l'utente. Restano aperti audio Live RTSP, seek remoto SD, bundle Finder, firma/notarizzazione e completamento traduzioni IT/EN. Timelapse giornaliero e timeline verticale 00-24 restano separati: la linea a nodi di questa release non e una scala temporale proporzionale 00-24.

## Distribuzione
Pacchetto pubblico con sorgenti completi, risorse, launcher, bundle in dist, script e test. Nessun IP/Device ID/username personale precompilato, config, log, video o campione privato. Richiede Python 3.9+, FFmpeg/FFprobe e VLC. Nessuna licenza assegnata automaticamente; icona fornita dall'utente. dist ignorato da Git e allegabile alle release.

```bash
python3 scripts/build_macos.py
python3 -m unittest discover -s tests -v
node tests/test_preview_profiles.cjs
```

Il test opzionale browser richiede Playwright e Chromium, non necessari per usare l'app.
