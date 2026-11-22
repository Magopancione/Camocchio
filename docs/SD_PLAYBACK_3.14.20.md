# 3.14.20 - Riproduci dalla microSD (sperimentale)

## Avvio e uso
Conservare la 3.14.19 come rollback. Chiudere la precedente istanza con Ferma Live e Esci. Avviare il .command nella radice di QUESTO pacchetto. Il vecchio avvio .app resta non validato per Live/anteprime.

Installare VLC in /Applications oppure ~/Applications. Caricare il giorno e premere Riproduci dalla microSD sulla riga della registrazione. VLC viene aperto con un URL HTTP locale temporaneo. Il backend usa il playback proprietario TCP 8800, non RTSP Live, e inoltra il video mentre arriva. Non attende intenzionalmente la fine della registrazione. Attendere il buffering; latenza da verificare sulla telecamera.

Ferma riproduzione SD interrompe ricezione e FFmpeg. Esci arresta anche il playback. La finestra VLC puo restare aperta con buffer gia ricevuto: chiuderla manualmente. Un solo player/sessione, niente seek remoto. Non cambiare data durante la riproduzione. Download singoli e giornalieri bloccati fino alla fine/stop del playback. Per il primo test fermare anche il Live per ridurre carico sulla camera.

## Limiti dichiarati
- SOLO VIDEO, senza audio in questa prima prova. L'audio dei download MP4 non cambia.
- Frame rate di ingresso ipotizzato 20 fps: velocita temporale da verificare; non sono ancora interpretati i timestamp sorgente.
- FFmpeg converte HEVC/H264 in H264 MPEG-TS, larghezza 960: usa CPU, richiede encoder libx264. Nessuna accelerazione hardware configurata.
- Buffer nelle pipe/RAM e nel player, nessun file multimediale scritto dal nuovo backend e nessuna aggiunta alla Gallery. VLC puo avere proprie preferenze/cache indipendenti.
- La telecamera puo trasferire piu velocemente del tempo reale: anche l'intero clip potrebbe essere ricevuto rapidamente. Non e garantito un risparmio di traffico o una partenza prima dell'ultimo byte per ogni clip.
- Nessun avanzamento remoto, ripresa o audio. Timeout attesa player 30s, socket 15s, sessione massima 15 minuti.
- Token casuale nell'URL locale, nessuna password o chiave nell'URL. Server solo loopback. Non esporre porte del router.
- La connessione viene chiusa per interrompere il playback; non viene inviato un comando di cancellazione SD.

## Verifiche eseguite
Confronto AST: funzioni Live, movimento, download, login e audio invariate. Sintassi Python/JS. Test con video HEVC SINTETICO, trasporto camera simulato e FFmpeg reale: uscita MPEG-TS H264 valida, rilascio socket/processo/lock; sessioni concorrenti bloccate; stop idempotente. Test regressione movimento superati. Non eseguito VLC su macOS o protocollo su telecamera fisica. Testare con una registrazione non importante e riportare stato/MB ricevuti se non parte.
