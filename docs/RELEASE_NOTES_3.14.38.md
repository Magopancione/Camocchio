# Camocchio Mac 3.14.38, candidata

Base: archivio allegato 3.14.37. Conservare le due versioni separatamente. Android e modulo di riproduzione microSD invariati. Sorgenti, non una .app precompilata. Sul Mac estrarre separatamente, eseguire CREA_APP_MAC.command, aprire dist-native/Camocchio.app.

## Interfaccia
- Tooltip dei pulsanti disegnati sopra il contenuto scrollabile, con posizione limitata alla finestra e chiusura su scroll/Esc. Vale anche per Scarica giornata.
- Trascinamento solo dalla fascia superiore vuota. Disabilitato easy_drag globale. Pulsanti della finestra conservati. Tolto il testo visibile dalla barra, non il nome dell'app. Fluidità nativa da verificare sul Mac.
- Indicatori SD, disco e anteprima in Registrazioni a 38 px, pittogrammi a 31 px. Gallery usa la stessa SD al posto del disco rosso se manca MP4, senza presumere che il file sia ancora sulla scheda.
- Stato/stop SD visibili mentre la riproduzione è attiva o il buffer è utilizzabile. Diagnostica disponibile durante la sessione o per l'ultimo esito non inattivo. Eliminato testo esplicativo permanente. Chiudi ed Esc nel player conservati.
- Device ID e Password Portachiavi con allineamento e altezze identiche; rimossa la nota sullo username. Nessun cambio al salvataggio della password o all'identificativo.

## Crea anteprime mancanti
Gallery > Crea anteprime mancanti > Conferma. Include tutti gli MP4 Camocchio scaricati nella cartella configurata, indipendentemente da pagina e giorno. Esclude parziali, file di altro tipo e link simbolici. Usa il profilo salvato all'avvio, una GIF alla volta, senza toccare i video o sovrascrivere GIF già esistenti. Le anteprime non partono più solo passando sopra una card priva di GIF. Ferma dopo il file in corso interrompe la coda fra due file. Le GIF completate restano. Generazione singola ancora disponibile.

## Live: bridge locale sperimentale
Il test 8800 ha confermato l'autenticazione sulla telecamera, non il Live. Questa versione aggiunge solo il percorso dal bridge al player integrato: un bridge esterno già funzionante può fornire FLV audio/video a Camocchio su http://127.0.0.1:PORTA/live.flv, senza RTSP. Scegli Bridge Live locale, inserisci l'URL del servizio già avviato, poi Avvia Live. Il bridge non è incluso né avviato da Camocchio. Nessuna connessione a host remoti dal nuovo lettore, nessun redirect, nessun fallback automatico a RTSP. Ferma Live ferma il lettore Camocchio, non il bridge esterno. Fonte tecnica per un possibile bridge compatibile: https://github.com/AetherKnowledge/v380-nodejs (supporto dichiarato per alcuni firmware H.264, non verificato sul modello dell'utente). Il prossimo passo è verificare un bridge compatibile con la telecamera reale e la presenza di audio decodificabile. Non inserire password nel campo URL. Non esporre servizi su Internet.

## Test eseguiti
Chromium con API simulate: tooltip, impostazioni, altezza icone, Gallery e coda, player microSD, sidebar. FFmpeg: GIF vera da un MP4 sintetico, nessuna sovrascrittura/prelievo di parziali, errore di file gestito. Bridge: due conversioni FLV sintetiche in HLS H.264/AAC, pulizia e rifiuto redirect/URL estranei. Regressioni Live RTSP, microSD HLS con AAC, profili GIF, HTTP e filtri. Sintassi Python 3.9 e Bash. Non testati: build reale, trascinamento Cocoa, riproduzione su WKWebView e Live video/audio della telecamera reale.
