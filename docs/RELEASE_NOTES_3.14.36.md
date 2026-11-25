# Camocchio Mac 3.14.36, candidata

Base 3.14.35 allegata, da conservare separatamente. Android e riproduzione microSD invariati. Estrarre in una cartella nuova, eseguire CREA_APP_MAC.command e aprire dist-native/Camocchio.app. Nessuna .app precompilata.

## Interfaccia
- Gallery: modalità anteprima invariata e monitor con mela dopo l’orario, sulla stessa riga. Verde = MP4 locale; rosso = MP4 non presente sul Mac. Il titolo usa l’ellissi se necessario ed è disponibile per intero nel tooltip. Nessun omino sulla card Gallery.
- Registrazioni e pannello dettagli anteprima: un omino per intervallo di movimento, fino a cinque; oltre, +N indica quelli ulteriori. Nessun omino equivale a una persona rilevata. 0 solo se l’analisi ha effettivamente restituito zero intervalli.
- Palette sotto l’icona e la testata del menu; DATA sostituisce Giornata.

## TCP 8800 e RTSP
Live apre con TCP 8800 • test selezionato. Avvia Live in questa modalità effettua soltanto il login diagnostico già usato per la microSD. Non invia richieste di riproduzione o registrazione, non scrive sulla scheda e non include password o ticket nel risultato. Non avvia RTSP. Per il Live precedente selezionare esplicitamente RTSP opzionale. Nessun fallback automatico. L’accesso alla microSD sulla stessa porta non identifica il comando Live. Il Live proprietario e le sue tracce audio/video restano da verificare.

## Verifiche locali
- Mock di telecamera su TCP loopback: risposta accettata, rifiutata e incompleta; timeout simulato; blocco durante uso microSD e nuova prova dopo errore. Nessun invio di comandi media.
- Chromium con API simulate: indicatori verdi/rossi, cinque omini, loro assenza dalla card, palette/Data, default 8800 e RTSP solo su selezione, sidebar e player SD da entrambe le viste.
- Regressioni FFmpeg sintetiche: microSD interna H.264/AAC e percorso RTSP/HLS; test HTTP e Gallery. Sintassi Python 3.9, Bash e JavaScript.
- Nessuna compilazione o prova fisica su macOS/telecamera eseguita qui.
