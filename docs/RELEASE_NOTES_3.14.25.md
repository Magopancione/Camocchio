# V380 Mac 3.14.25 - Comandi compatti, cambio anteprima e correzione audio SD

## Avvio
Chiudere la precedente istanza con Ferma Live e Esci. Estrarre in una nuova cartella e avviare Avvia_V380_Mac.command di QUESTO pacchetto. Conservare la 3.14.24. Bundle .app incluso, non firmato/non notarizzato, problema di avvio Finder NON dichiarato risolto. Richiede Python 3.9+, FFmpeg/FFprobe e VLC per playback SD.

## Interfaccia
- Testata menu con icona accanto al nome telecamera/spia, come riferimento fornito. Navigazione con icone lineari e testo Live/Registrazioni/Gallery/Impostazioni/Esci.
- Tabella: Scaricato diventa spunta verde di stato (non un pulsante); download e riproduzione SD diventano icone con descrizione grafica al passaggio mouse o focus tastiera.
- Comandi Scarica giornata, Ferma coda, Scarica selezionato, Avvia/Ferma Live, Ferma SD, selezione/deselezione/Cestino Gallery diventano icone con tooltip e nome accessibile. Conferme distruttive e download massivo conservate. Date, campi e navigazione menu restano leggibili.
- Tavolozza in alto e tooltip delle anteprime conservati.

## Modalita per singola anteprima
Nel pannello Anteprima c'e un selettore Uniforme / Parti significative. Scegliere una modalita rigenera subito SOLO quella GIF usando il relativo profilo gia salvato. Non cambia la preferenza globale ne i parametri delle altre anteprime. Rigenera riusa la modalita selezionata nel pannello. Senza MP4 il selettore e disabilitato: scaricare prima il video. Una sola GIF per registrazione, non due copie simultanee. Per metodi storici non registrati il selettore non inventa un valore.

## Audio microSD: bug concreto corretto
Nella base allegata il flag sd_stream_audio veniva letto dal dizionario runtime(), che contiene solo dati connessione/password/cartella e NON quel flag. Il playback reale quindi restava senza audio anche quando l'opzione era salvata. I vecchi test sintetici passavano il flag direttamente nel runtime simulato e non intercettavano il difetto.

Ora Playback legge il flag dalla configurazione completa separatamente, senza modificare login o download. Test di regressione aggiornato per riprodurre la situazione reale (flag assente dal runtime, presente in cfg).

Per provare: Impostazioni > Altro > Audio sperimentale in Riproduci dalla microSD (VLC), Salva; fermare la vecchia sessione e riavviare una registrazione con parlato. Lo stato mostra Audio attivo/disattivo, blocchi decodificati, campioni, picco PCM e blocchi non validi. Picco 0 puo indicare silenzio; valori non zero NON garantiscono da soli ascolto corretto o sincronizzazione. Nessun campione audio salvato dalla diagnostica.

Corretto il passaggio dell'opzione; ascolto e sincronizzazione reale ancora da verificare. Se problemi disattivare flag e tornare al solo video. Live RTSP resta senza audio. Frame rate playback ancora ipotizzato 20 fps, timestamp non interpretati: offset/deriva possibili.

## Stato / cosa manca
- Download, Gallery, operazioni massive e anteprime movimento implementati; nessuna nuova cancellazione SD.
- Playback microSD video confermato dall'utente nelle versioni precedenti; audio da ricollaudare con questa correzione.
- Live video tramite .command confermato; audio Live non implementato.
- Bundle .app da correggere/validare; firma/notarizzazione non effettuate.
- Seek remoto e player SD integrato browser non implementati.
- Rilevamento persone distinto dal movimento non implementato.
- Traduzione completa dei nuovi controlli IT/EN ancora da completare; alcune descrizioni nuove restano in italiano.
- Timelapse aggregato giornaliero e timeline verticale 00-24 restano richieste separate.

## Verifiche
Sintassi Python/JS; confronto AST login, Live, download e MP4 audio invariati; regressioni movimento e playback con video/audio sintetici; audio flag cfg vs runtime; contatori audio e tracce H264+AAC verificate con FFprobe; cambio modalita singola senza mutazione configurazione; browser Chromium con API simulate per menu, icone, tooltip, selettore e disabilitazione senza MP4. Non collaudato sul Mac o sulla telecamera reale.

## Pacchetto pubblico
Sorgenti completi, risorse, launcher, bundle in dist, script, test e checksum. Nessun IP/Device ID/username personale precompilato, config, log, video o campione privato. Configurazione e Portachiavi gia sul Mac restano esterni. Nessuna licenza assegnata automaticamente; icona fornita dall'utente, verificarne i diritti prima della pubblicazione. dist ignorato da Git, allegabile alle release.

```bash
python3 scripts/build_macos.py
python3 -m unittest discover -s tests -v
node tests/test_preview_profiles.cjs
```

Test browser opzionale tests/browser_gallery.py richiede Playwright e Chromium, non necessari all'app.
