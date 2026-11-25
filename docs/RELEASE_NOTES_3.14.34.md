# Camocchio Mac 3.14.34, candidata

Base: sorgenti allegati della 3.14.33. Conservare separatamente 3.14.33 e 3.14.34. Android e percorso Live RTSP invariati.

## Avvio
Estrarre in una nuova cartella e aprire CREA_APP_MAC.command sul Mac. Aprire dist-native/Camocchio.app dopo la compilazione. Lo ZIP contiene sorgenti, non una app precompilata. Richiede Python 3.9+, FFmpeg e FFprobe per la compilazione.

## Interfaccia
- Il contenuto a destra scorre in un'area propria; la sidebar rimane ferma e scorre solo al suo interno se la finestra e bassa.
- Registrazioni: azioni e stati piu vicini all'orario, riquadri e segnaposto piu compatti. La distribuzione oraria conserva scala e azioni.
- Icone di stato: microSD blu se manca la copia locale; disco verde con mela stilizzata per MP4 presente sul Mac; immagine arancio con Play se l'anteprima e disponibile. Icone con etichette accessibili. I due cestini della Gallery rimangono distinti.
- Il contatore Eventi diventa Intervalli di movimento: gruppi di variazioni visive durante l'analisi dell'anteprima, non un conteggio di persone o allarmi. L'algoritmo non cambia.
- Proposta per una fase successiva: filtri rapidi Tutte / Solo microSD / Sul Mac e pannello dettagli a destra su finestre ampie; mantenere il dialog compatto sulle finestre piccole. Non implementati qui.

## microSD
Il backend 3.14.33 apriva VLC anche con la scelta Riquadro interno. In modalita interna la 3.14.34 non lancia applicazioni esterne: compone una playlist HLS con FFmpeg e la apre nel riquadro, sia da Registrazioni che da Gallery. L'opzione audio esistente resta valida. Non crea MP4 nella Gallery. I segmenti temporanei sono rimossi alla chiusura o alla sostituzione della sessione; il watchdog blocca buffer eccessivi. Un arresto anomalo puo lasciare file temporanei di sistema. La modalita esterna rimane separata. Chiusura del riquadro e tasto Esc arrestano la sessione.

## Live e porta 8800
In Live > Diagnostica Live, Verifica porta TCP 8800 apre e richiude una sola connessione all'host salvato. Non invia comandi proprietari, non acquisisce credenziali o media, non scansiona la rete. Il risultato riguarda la raggiungibilita TCP, non la presenza di uno stream o della traccia audio. Il Live proprietario non e implementato in questa versione e non e stato verificato sulla telecamera. Il prossimo passo e validare un client Live autenticato compatibile con il modello/firmware, separatamente dal playback microSD. Non esporre la porta su Internet.

## Verifiche effettuate
- Chromium con API simulate: menu immobile durante scorrimento effettivo in due dimensioni finestra, distanza fra ora e azioni, badge, contatore comprensibile, apertura SD da entrambe le viste e stop con Esc/Chiudi.
- FFmpeg/FFprobe con camera e media sintetici: HLS interno H.264/AAC, nessun avvio esterno, controllo del token e rimozione del buffer. Regressione MPEG-TS esterno video/audio, blocco concorrenza e stop.
- Test Live sintetico, profili e generazione movimento, Gallery backend, preferenze HTTP e sintassi.
- Aggiornato il controllo post-compilazione al nome effettivo dell'eseguibile Camocchio.
- Non eseguiti: build macOS, riproduzione reale WKWebView, verifica della porta sulla LAN dell'utente o audio Live reale.
