# V380 Mac 3.14.32 - candidata Mac
Base esatta: sorgenti 3.14.31 riallegati dall'utente. Android resta fuori perimetro.

## Correzioni 3.14.32
- Barra superiore: abbandonata la titlebar nativa grigia. La finestra pywebview e ora frameless e l'app disegna una propria fascia da 42 px con la palette e controlli rosso/giallo/verde. Le azioni sono collegate a chiusura, minimizzazione e maximize/restore della finestra pywebview. E il primo tentativo che rimuove realmente la titlebar Cocoa visibile, quindi va collaudato su macOS per trascinamento, resize, fullscreen e VoiceOver.
- Device ID e Password Portachiavi sulla stessa riga; su finestre strette tornano verticali. Username continua a derivare dal Device ID.
- Anteprima: rimossa la nota dentro il disclosure Quando si applicano le modifiche?; la nota breve e sempre visibile.
- Stato registrazione: niente piu SD/100% come unico indizio. Le card mostrano microSD oppure Mac con colori e tooltip; sopra lo stato SD e presente una legenda microSD / salvato sul Mac / anteprima locale.
- Player esterni: tornano le scelte note VLC, IINA, QuickTime e Predefinita; per GIF anche Anteprima. Aggiunta Altra applicazione... che usa il selettore .app del Mac.
- Riproduzione microSD: nuova scelta Riquadro interno / VLC / IINA / QuickTime / Predefinita / Altra applicazione. Default nuova installazione: riquadro interno. Il riquadro usa lo stesso endpoint progressivo locale e i controlli video HTML; Ferma SD chiude stream e riquadro.
- Audio microSD: etichetta non piu legata a VLC. La pipeline IMA ADPCM -> PCM -> AAC gia validata rimane; test sintetico produce H264+AAC mono 8 kHz. Ascolto reale sul Mac/telecamera da verificare.

## H.265/HEVC
Il download non ricodifica il video: la funzione save_recording e byte/logica invariata dalla 3.14.31. Il flusso elementare H264/HEVC viene rimuxato in MP4 con -c:v copy; per HEVC imposta hvc1. Se audio type22 e presente, solo l'audio viene convertito in AAC. Quindi non introduciamo una conversione video inutile nei file salvati.
Live RTSP e playback progressivo microSD restano diversi: per compatibilita con HLS/MPEG-TS e con il player web, il percorso progressivo continua a produrre H264; non e lo stesso problema del contenitore MP4. La diagnostica utente mostrava anche HEVC Error constructing frame RPS / invalid NALU e audio=false sul Live RTSP: non viene dichiarato risolto.

## Verifiche eseguite in Linux
PASS grammatica Python 3.9, Bash, JavaScript.
PASS source/local-media/HTTP/Gallery/profile/motion/Live test esistenti.
PASS SD audio sintetico: decoder IMA max error 0 rispetto a FFmpeg, uscita H264+AAC 8 kHz mono.
PASS SD video sintetico HEVC: protocollo simulato -> FFmpeg -> MPEG-TS H264, stop e lock.
PASS AST: download, save_recording, login, listrec, makegif, begin_download invariati dalla 3.14.31.
NON TESTATI qui: frameless Cocoa sul Mac, pulsanti finestra reali, trascinamento/ridimensionamento, scelta app AppleScript, audio telecamera reale, HEVC WebKit diretto.

## Primo collaudo sul Mac
1. Conservare 3.14.31. Compilare con CREA_APP_MAC.command e avviare dist-native/V380 Mac.app.
2. Controllare subito la fascia superiore: non deve piu esistere una seconda barra grigia nativa. Provare drag, rosso, giallo, verde e resize.
3. Controllare Device ID/Password, nota Anteprima e nuovi stati microSD/Mac.
4. In Riproduzione lasciare microSD=Riquadro interno e Audio microSD attivo; provare una registrazione con suono noto, volume del player alto. Riportare Dettagli tecnici se audio non si sente.
5. Provare un player locale fra VLC/IINA/QuickTime e poi Altra applicazione. Non testare cancellazioni su materiale unico.
