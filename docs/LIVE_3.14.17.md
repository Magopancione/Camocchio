# Live sperimentale 3.14.17

Nuova sezione Live. Usa host configurato, porta RTSP 554, percorso /11. Nessun IP personale incluso. Se richiesto dal dispositivo, attivare RTSP usa username e password della telecamera. Non presumere che le credenziali RTSP coincidano sempre con quelle TCP 8800.

FFmpeg riceve RTSP TCP e decodifica in JPEG: anteprima nel browser senza audio, fino a 8 fps e larghezza 960. Il flusso sorgente puo essere 1080p/20fps; l'anteprima e ridotta per contenere carico CPU. Nessun MP4 Live salvato, solo ultimo fotogramma in RAM. Latenza non garantita. Credenziali non inviate al browser, ma eventualmente visibili nella riga di comando FFmpeg agli utenti locali autorizzati. Non pubblicare diagnostica dei processi senza rimuoverle.

Avvia/Ferma espliciti. Un solo flusso condiviso fra le schede. Ferma Live prima di chiudere il browser; Esci arresta il processo. Chiusura della sola scheda non garantisce arresto. Usare solo sulla LAN; non aprire porte del router.

Build non firmata/non notarizzata, richiede Python e FFmpeg. Non testata sulla telecamera reale. Movimento/presenza persone e playback progressivo microSD NON implementati qui, restano nella roadmap. Audio MP4 e protocollo download invariati.
