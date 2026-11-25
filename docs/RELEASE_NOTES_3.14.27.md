# V380 Mac 3.14.29: finestra dedicata e Live audio/video

CANDIDATA DA COMPILARE E COLLAUDARE. La 3.14.26 approvata dall'utente resta il riferimento stabile. Questo ZIP contiene sorgenti e build script, NON una .app nativa gia compilata. Preparato su Linux: non e possibile compilare o collaudare qui un bundle macOS. Nessuna firma Developer ID o notarizzazione effettuata.

## Finestra indipendente
Il nuovo ingresso src/desktop.py apre una finestra Cocoa con WKWebView tramite pywebview: nessuna scheda Safari/Chrome, nessuna barra indirizzi e nessun Terminale nell'uso quotidiano. L'interfaccia HTML approvata e mantenuta, non riscritta in controlli AppKit. Il backend resta un server locale su 127.0.0.1 e porta casuale; non e accessibile dalla LAN. Chiusura normale della finestra: arresto Live/SD, chiusura server e pulizia buffer HLS. Conferma prima di chiudere. Non chiudere durante un download importante: la chiusura del processo puo interrompere il file corrente, non cancella quelli completi.

## Creare la .app sul Mac (una volta)
Prerequisiti SOLO per compilare: Python 3.10+ con venv/pip, FFmpeg e FFprobe funzionanti (libx264 e AAC), connessione Internet per scaricare le dipendenze Python. Lo script non installa Homebrew, Python o FFmpeg e non cambia Gatekeeper. Preferisce Python disponibile nel PATH; PYTHON_BUILD puo indicare un interprete preciso.

1. Chiudere la vecchia app con Ferma Live/SD e Esci.
2. Estrarre questo archivio in una nuova cartella, conservando la 3.14.26.
3. Aprire CREA_APP_MAC.command. In alternativa, da Terminale nella cartella estratta:

```bash
bash CREA_APP_MAC.command
```

4. Lo script crea un ambiente build separato, raccoglie runtime Python, pywebview/PyObjC, FFmpeg/FFprobe e dipendenze binarie tramite PyInstaller. Esegue controlli Mach-O, strumenti multimediali e firma ad-hoc. Il primo build puo richiedere diversi minuti. La compatibilita del bundle completo e da verificare sul Mac, non garantita da test Linux.
5. A successo, la finestra Finder mostra dist-native/V380 Mac.app. Copiarla in Applicazioni e aprirla dal Finder/Dock. Viene anche prodotto V380_Mac_3.14.29_NATIVE.zip.

Dopo il build non e previsto Python/Homebrew esterno per il backend o FFmpeg. VLC resta necessario per lo streaming SD gia funzionante e per il fallback Live. Il pacchetto e dell'architettura del Mac di build, NON universal2. Testare sul Mac destinatario prima di distribuirlo. La firma ad-hoc locale non equivale a firma Developer ID/notarizzazione. Il build registra le versioni risolte in build-notices; le dipendenze hanno intervalli di versione, non un lock riproducibile.

Avvia_V380_Mac.command rimane SOLO come fallback del vecchio avvio browser, non e l'avvio della finestra indipendente. scripts/build_macos.py richiama il build nativo, non crea piu una finta app con shell launcher. Nessun vecchio bundle dist e incluso.

## Live con audio
Nuovo percorso RTSP -> FFmpeg -> HLS locale con H264/AAC. Audio incluso se il flusso RTSP contiene una traccia decodificabile. Non aggiunge audio alla vecchia sequenza JPEG. Usa host, porta, percorso, autenticazione e trasporto gia salvati. Non cambia lo streaming SD.

Aprire Live, lasciare selezionato Live con audio e premere Avvia. Attendere alcuni secondi di buffering. Se il sistema blocca l'autoplay, premere Play nel player. Volume e mute sono nei controlli video. La scritta traccia audio rilevata NON prova che il microfono contenga suono. Ascolto e sincronizzazione reale restano da verificare sulla telecamera.

Apri Live in VLC usa lo stesso HLS locale, non un secondo RTSP. Nella modalita browser di fallback HLS e previsto su Safari; browser senza supporto HLS nativo richiedono VLC. Togliendo Live con audio si torna al precedente player JPEG senza audio.

Video convertito a 960 px/20 fps, audio AAC mono 24 kHz. Latenza reale non misurata; CPU potenzialmente maggiore. Nessun filmato aggiunto alla Gallery, ma HLS usa segmenti TEMPORANEI su disco: playlist di 5 segmenti da circa 2 secondi, cancellazione dei vecchi e watchdog oltre 64 MB. Ferma Live e chiusura normale eliminano la cartella temporanea. Crash/kill puo lasciare v380_live_ nella directory temporanea di sistema. Non promettiamo assenza di scritture su disco.

## Dati e permessi
Configurazione e servizio Portachiavi conservano i nomi della 3.14.26. Non sono inclusi nello ZIP. Il nuovo eseguibile puo richiedere nuovamente accesso Portachiavi/rete locale. Consentire la rete locale alla nuova app se richiesto. Non esporre porte sul router. Credenziali RTSP non inviate all'interfaccia o all'URL HLS, ma possono essere visibili nella riga di comando FFmpeg a utenti locali autorizzati. Non pubblicare processi/log senza revisione.

## Verifiche e limiti
Eseguiti qui: sintassi Python/JS; test browser Chromium con API simulate; regressioni Gallery, profili e anteprime; HLS reale con video/audio sintetici, tracce H264+AAC verificate con FFprobe, token e rifiuto traversal, pulizia; regressioni streaming SD sintetico. Confronto con archivio allegato: sd_playback.py e motion_preview.py identici, funzioni login/listrec/download/save_recording/makegif/begin_download invariate via AST.

NON eseguiti: build .app su macOS, prova WKWebView/HLS/audio reale, permessi di rete e Portachiavi, prova su telecamera, firma Developer ID/notarizzazione. Il funzionamento audio SD gia confermato dall'utente non e una conferma del nuovo Live.

Prima prova: aprire .app, controllare configurazione, elenco SD e Live audio; fermare Live e riprovare SD audio; verificare download/anteprima; chiudere e riaprire dal Dock. Se il build fallisce, conservare l'errore senza credenziali e non modificare la baseline.

Restano fuori: seek remoto SD, player SD incorporato (rimane VLC), traduzioni complete, timelapse e timeline proporzionale 00-24. Rilevamento persone non richiesto.

## Terze parti
Icona fornita dall'utente, nessuna nuova licenza assegnata al progetto. Il build raccoglie FFmpeg-license, buildconf e elenco pacchetti; questi non sostituiscono gli obblighi di licenza delle dipendenze prima di redistribuire il bundle. Riferimenti tecnici consultati: https://pywebview.flowrl.com/api/ e https://pyinstaller.org/en/stable/feature-notes.html .
