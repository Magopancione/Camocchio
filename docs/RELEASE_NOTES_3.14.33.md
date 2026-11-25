# Camocchio 3.14.33 - candidata Mac
Base: sorgenti 3.14.32 riallegati dall'utente. Android non modificato.

## Correzioni
- Nome applicazione: Camocchio nel titolo HTML, barra personalizzata, bundle .app, eseguibile e metadati macOS. Percorso configurazione e servizio Portachiavi V380 Mac 2 restano intenzionalmente invariati per conservare password e impostazioni esistenti.
- Rimossa la sezione Impostazioni > Interfaccia > Aspetto finestra. Lingua spostata in Telecamera.
- Chiusura: il pulsante rosso chiama prima /api/quit, arresta Live e microSD, poi distrugge la finestra; fallback nativo performClose_ se l'API HTTP fallisce.
- Eliminazione singola video/GIF: conferma in dialog compatto sovrapposto, non piu pannello inline che allarga il dialog dei dettagli.
- Rimossi i tre chip microSD/Mac/Anteprima accanto allo stato Ferma.
- Icone: nuovi SVG ispirati ai riferimenti forniti: scheda SD blu, disco locale verde, file anteprima arancio. Tooltip e nomi accessibili restano disponibili.
- Sidebar desktop resa sticky a 58 px sotto la barra, altezza viewport e scorrimento interno; su schermi <=650 px torna nel flusso per usabilita.
- Live: quando la diagnostica restituisce audio=false, il controllo Live con audio viene disabilitato e l'interfaccia dichiara che il flusso RTSP non contiene audio. Non viene piu promesso audio che la sorgente non offre.

## Stato del Live audio
Gli screenshot reali mostrano running=true, ready=true, audio=false e video HEVC con errori RPS/NALU. FFmpeg non rileva quindi alcuna traccia audio nel profilo RTSP configurato. Questa release non inventa una traccia e non dichiara il problema risolto. La microSD audio usa invece il protocollo proprietario type22 e risulta funzionante secondo il collaudo utente. Per avere audio Live serve individuare un profilo/URL della telecamera che esponga audio oppure implementare il protocollo Live proprietario Macrovideo; i sorgenti attuali documentano soltanto playback registrazioni via porta 8800, non il comando Live proprietario.

## Test eseguiti
PASS grammatica Python 3.9, Bash e JavaScript.
PASS test Live sintetico H264/AAC, microSD video/audio sintetici, movimento, Gallery backend, anteprime e local media.
PASS test browser Chromium: titolo Camocchio, sidebar sticky, rimozione Aspetto finestra e chip, dialog eliminazione <250 px, stato RTSP senza audio; nessun errore JavaScript.
PASS confronto AST: login, listrec, download/save_recording, coda, GIF e vecchio Live JPEG invariati dalla 3.14.32.
NON TESTATI: bundle macOS, chiusura Cocoa reale, sticky/resize nella .app, audio Live reale (la sorgente osservata dichiara audio=false).

## Primo collaudo
1. Conservare 3.14.32. Compilare CREA_APP_MAC.command e aprire dist-native/Camocchio.app.
2. Provare subito rosso/giallo/verde; il rosso deve chiudere dopo la pulizia delle sessioni.
3. Scorrere Registrazioni/Gallery e verificare sidebar ferma.
4. Aprire dettagli, Elimina, verificare dialog piccolo e Annulla.
5. Live: aspettarsi video. Se Dettagli tecnici resta audio=false, nessun player puo produrre il suono da quel flusso RTSP.
