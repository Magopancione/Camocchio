# V380 Mac 3.14.31 - candidata Mac

Base: sorgenti 3.14.30 riallegati dall'utente. Android messo da parte e non modificato.
Conservare separatamente 3.14.29 e 3.14.30 fino al collaudo.

## Correzioni
- Gallery: eliminato il selettore Video/Anteprime. Ogni checkbox seleziona la registrazione/card una sola volta. I due cestini operano sulla stessa selezione: il cestino video sposta soltanto gli MP4 presenti; il cestino anteprima sposta soltanto GIF e relativi .motion.json/PNG presenti. L'altro tipo resta. Elementi senza quel tipo vengono semplicemente ignorati dal relativo comando. I pulsanti sono disabilitati se, nella selezione, non esiste alcun file del tipo richiesto.
- Device ID unico e username derivato: comportamento 3.14.30 conservato.
- Impostazioni anteprima: struttura 3.14.30 conservata per non introdurre regressioni; resta da rifinire sulla base del prossimo feedback.
- Player esterni: rimossa la lista presunta VLC/IINA/QuickTime/Anteprima. Per video e GIF c'e ora Scegli applicazione..., che apre il selettore applicazioni nativo macOS tramite osascript e salva il percorso .app scelto. Predefinita ripristina l'associazione macOS. I due tipi restano indipendenti. Player interni invariati. Streaming microSD e pulsante Live VLC restano invariati.
- Barra titolo: la strategia full-size/trasparente 3.14.30 non colorava visivamente la fascia sul Mac dell'utente. Questa versione torna alla finestra Cocoa normale e prova a colorare direttamente la titlebar/theme-frame nativa, mantenendo i tre pulsanti. Il testo Impostazioni non dichiara piu "integrata" sulla sola base della chiamata API.

## Barra titolo: stato reale
Apple documenta che titlebarAppearsTransparent mostra il contenuto sottostante solo assieme a full-size content; nella prova 3.14.30 cio non ha prodotto la resa attesa. 3.14.31 usa quindi una strategia diversa: colora direttamente le viste native della titlebar della NSWindow creata da pywebview. Questa parte NON e collaudabile in Linux e deve essere valutata sul Mac. Se resta grigia, non considerare il messaggio dell'interfaccia come prova visiva e conservare screenshot + log TITLEBAR.

## Test
PASS sintassi Python 3.9, Bash e JavaScript.
PASS test locali local_media, Live AV, movimento, audio SD, playback SD, Gallery backend, override profilo e profili anteprima.
PASS browser Chromium simulato: selezione unica, assenza selettore Video/Anteprime, due cestini sulla stessa selezione, richiesta anteprima con GIF corretta, picker applicazioni presenti, nessun errore JS.
PASS confronto: live_av.py, sd_playback.py, motion_preview.py identici alla 3.14.30; login/listrec/save_recording/begin_download/makegif/Live invariati via AST.
NON TESTATO: resa titlebar su macOS, AppleScript application picker su macOS reale, apertura delle app scelte, telecamera reale.

## Primo collaudo
1. Compilare con CREA_APP_MAC.command e avviare dist-native/V380 Mac.app.
2. Controllare subito la barra superiore con almeno due palette e fare screenshot se resta grigia.
3. Gallery: selezionare una card che abbia MP4+GIF, premere prima un cestino e verificare che l'altro file resti. Per prudenza farlo su una copia non importante/recuperabile dal Cestino.
4. Impostazioni > Riproduzione: usare Scegli applicazione... per un MP4 e per una GIF; provare apertura esterna e Predefinita.
5. Verificare brevemente player interni, distribuzione giornaliera e RTSP, che non sono stati modificati intenzionalmente.
