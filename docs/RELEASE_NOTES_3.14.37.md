# Camocchio Mac 3.14.37: candidata di fine sessione

Base 3.14.36, da conservare separatamente. Android invariato.

- Indicatori allineati a sinistra nella colonna Stato, comandi a destra.
- microSD: immagine originale ritagliata e ridotta; disco Mac: adattamento vettoriale del riferimento argentato. Mela verde per MP4 locale, rossa per MP4 assente in Gallery. Omini e simboli Uniforme/Parti significative conservati.
- Pulsante a quattro riquadri (palette) in basso a destra della barra laterale; si apre verso l’alto. Voce Gallery invariata.

## Ripresa Live
L’utente conferma che l’autenticazione funziona e che la porta è usata dalla microSD. Ha scritto 8880; la verifica della 3.14.36/37 è vincolata a 8800. Verificare la porta salvata prima della prossima prova, senza cambiarla alla cieca. Prossimo test: individuare e usare una richiesta Live compatibile con il firmware, quindi verificare dati video/audio ricevuti e decodifica. Non confondere playback microSD e Live. RTSP rimane opzionale, senza fallback automatico. Non eseguita prova di streaming proprietario.

## Verifiche e avvio
Passati Chromium con API simulate (allineamento, icona SD, palette, Gallery e microSD), controllo sintassi/versione, filtri e test autenticazione in loopback. Logica backend invariata salvo stringa versione nel log. Nessun collaudo Mac. Estrarre separatamente, eseguire CREA_APP_MAC.command e aprire dist-native/Camocchio.app. Nessuna app precompilata.
