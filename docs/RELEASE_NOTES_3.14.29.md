# V380 Mac 3.14.29 - candidata, sorgenti da compilare

## Provenienza e limiti
L'allegato piu recente contiene la .app compilata 3.14.28, non i sorgenti.
Questa candidata usa i sorgenti 3.14.27 ancora disponibili, ricostruendo gli
adeguamenti di compilazione Python 3.9 della 3.14.28. Non e una modifica binaria
della .app allegata. Conservare intatta la 3.14.28 funzionante.
Nessuna .app precompilata inclusa. Build macOS, firma, aspetto Cocoa, codec HEVC
nel WebKit del Mac e telecamera reale NON collaudati in questo ambiente Linux.
Android non modificato.

## Installazione
1. Chiudere la vecchia app con Ferma Live/SD ed Esci.
2. Estrarre questo archivio in una nuova cartella, senza sovrascrivere la 3.14.28.
3. Aprire CREA_APP_MAC.command. Richiede Internet, FFmpeg e FFprobe sul Mac.
4. A compilazione completata aprire dist-native/V380 Mac.app.
5. Conservare la vecchia app separatamente fino al collaudo.
Lo script preferisce /usr/bin/python3 e ammette Python 3.9 o successivo.
PYTHON_BUILD consente di scegliere un altro interprete. Dipendenze principali
fissate alle versioni riportate nell'app compilata fornita dall'utente.
Il Terminale serve alla compilazione, non all'avvio quotidiano della .app.

## Nuove impostazioni
- Impostazioni > Riproduzione > Apri video locali: esterno oppure riquadro interno
  sperimentale, con Play/Pausa, volume, ricerca temporale e schermo intero nativi.
- Impostazioni > Riproduzione > Apri anteprime: esterno oppure riquadro interno.
- Ogni riquadro mantiene Apri esternamente. Chiudendo il riquadro si ferma il video.
- I valori predefiniti restano esterni per non cambiare il comportamento esistente.
- La scelta riguarda MP4 locali e GIF, non la riproduzione diretta dalla microSD.
- Impostazioni > Anteprima > Animazione GIF nella Gallery: sempre, solo al passaggio
  del mouse/focus, oppure ferme. In modalita hover si anima una sola miniatura.
  L'anteprima aperta esplicitamente resta animata. Le GIF non contengono audio.
- Per la modalita ferma/hover si genera un primo fotogramma PNG in Thumbnails/.posters.
  La prima visualizzazione puo richiedere qualche istante; i PNG sono riutilizzati.
- Device ID e Username protetti in sola lettura dopo la configurazione; modifica
  possibile soltanto con la casella avanzata. Prima configurazione ancora consentita.
- Parametri RTSP spostati in Telecamera > Connessione Live / RTSP (avanzate).

## Interfaccia
- Segnaposto temporali ridotti da 14x25 a 7x17 pixel, con focus visibile.
- Barra di scorrimento in tinta con la palette, nei limiti del rendering macOS.
- Barra del titolo: integrazione Cocoa per colore coerente con la palette, mantenendo
  i tre pulsanti nativi. Da verificare sul Mac; non e una sfumatura estesa identica
  al mockup. Se l'API nativa non e disponibile resta la barra standard e viene scritto
  un messaggio TITLEBAR nel log. Nessun cambio frameless o trascinamento personalizzato.

## Pulizia locale
Nuovo pulsante dedicato alle anteprime accanto al cestino video in Gallery.
Impostazioni > Archiviazione offre anche Cestina video e anteprime locali.
Prima di procedere vengono mostrati numero file, categorie e spazio occupato.
Annulla non modifica file. La conferma scade dopo due minuti.
Le nuove operazioni spostano i file nel Cestino del Mac, in una cartella V380-pulizia-*.
Non svuotano il Cestino. Per ripristinare, spostare manualmente gli MP4 nella cartella
video, GIF e .motion.json in Thumbnails, PNG in Thumbnails/.posters.
Ambito: tutte le date nella sola cartella configurata, non solo il giorno selezionato.
Sono inclusi esclusivamente MP4 V380 completi, GIF V380, report .motion.json e PNG
riconosciuti. Non vengono rimossi file estranei, parziali, cartelle arbitrarie,
password, configurazione, log o registrazioni della microSD. I vecchi comandi singoli
di eliminazione non sono stati trasformati in operazioni di Cestino.
File cambiati dopo la conferma non vengono spostati; eventuali errori sono mostrati.

## Messaggio HEVC e audio
Skipping invalid undecodable NALU: 1 indica che il decoder scarta una unita video
HEVC non decodificabile. Il numero 1 e il tipo NAL, non un codice di errore audio.
La causa non e determinabile dal solo screenshot. Il messaggio viene ora distinto
come warning, disponibile in Live > Diagnostica Live, non come errore fatale.
Questo non ripara il bitstream e non elimina eventuali artefatti video.
Il percorso audio Live integrato e la conversione H264/AAC non sono stati cambiati.
Il problema audio VLC segnalato dall'utente NON e dichiarato risolto: occorre una
prova sulla telecamera reale. Traccia rilevata non significa suono udibile.

## Collaudo consigliato sul Mac
1. Compilazione e apertura della nuova app; chiusura e riapertura.
2. Cambiare palette e verificare barra del titolo e scrollbar.
3. Attivare video interno, salvare, aprire un MP4, Play/Pausa, seek e audio.
4. Chiudere il video e aprire subito una GIF: il riquadro deve restare visibile.
5. Provare Apri esternamente e poi tornare alla modalita esterna nelle impostazioni.
6. Provare GIF sempre/hover/ferme; chiudere e riaprire l'app per verificare persistenza.
7. Provare prima la pulizia su una cartella di COPIE, verificando conteggi, Annulla,
   Cestino e conservazione dei file estranei. Non usare l'archivio unico per il primo test.
8. Verificare login, indice SD, download, generazione GIF e Live audio integrato.
9. Solo dopo verificare VLC; segnalare se e muto su Live, MP4 scaricato o entrambi.

## Verifiche eseguite qui
Vedere TEST_REPORT_3.14.29.txt. I test usano fixture sintetiche e cartelle temporanee,
non video reali dell'utente. Nessun accesso alla telecamera o cancellazione di file utente.

## Riferimenti tecnici
https://ffmpeg.org/pipermail/ffmpeg-cvslog/2024-June/143655.html
https://developer.apple.com/documentation/appkit/nswindow/titlebarappearstransparent
https://github.com/r0x0r/pywebview/discussions/1500
