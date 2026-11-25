# V380 Mac 3.14.30 - correzioni mirate, candidata da compilare

Base: sorgenti 3.14.29 riallegati dall'utente, non ricostruiti da una vecchia release.
Conservare la 3.14.29: player interni e distribuzione giornaliera confermati funzionanti.
Android non modificato. Nessuna .app precompilata inclusa.

## Avvio
1. Chiudere la vecchia app con Ferma Live/SD ed Esci.
2. Estrarre questo archivio in una nuova cartella, senza sovrascrivere la 3.14.29.
3. Aprire CREA_APP_MAC.command e attendere la compilazione sul Mac.
4. Aprire dist-native/V380 Mac.app. Per il nuovo titolo usare questa .app,
   non Avvia_V380_Mac.command (fallback browser senza cornice Cocoa dell'app).
Prerequisiti di build invariati: Python 3.9+, Internet, FFmpeg e FFprobe.
Il Terminale serve alla compilazione, non all'avvio quotidiano della .app.

## 1. Barra del titolo
La 3.14.29 rendeva trasparente la barra ma non attivava full-size content.
Ora il codice attiva NSFullSizeContentViewWindowMask sulla NSWindow di pywebview,
rende trasparente il titolo, nasconde solo il testo del titolo e conserva i tre
pulsanti nativi. Lo sfondo HTML esistente si estende sotto la cornice superiore.
Una fascia superiore di 44 px e riservata: nessun comando dell'app sotto i pulsanti.
La fascia e una regione di trascinamento pywebview; easy_drag globale disattivato.
Il colore segue la palette. Configurazione sul thread AppKit dopo caricamento WKWebView.
Il bridge restituisce il risultato dopo l'applicazione, non un successo anticipato.
Impostazioni > Interfaccia > Aspetto finestra mostra attivazione o motivo del fallback.

IMPORTANTE: testato il contratto con AppKit simulato e la riserva HTML in Chromium.
NON verificati qui la resa nativa, trascinamento, ridimensionamento e fullscreen
su macOS. Non dichiarare risolta visivamente la barra prima della prova sul Mac.
Se resta standard, comunicare il testo di Aspetto finestra e l'eventuale log TITLEBAR,
senza dati di connessione. Il meccanismo e cambiato rispetto alla 3.14.29.

## 2. Gallery: cestinare solo le anteprime scelte
- Scegliere Seleziona > Anteprime nella barra della Gallery.
- Spuntare le card desiderate: anche GIF senza MP4 sono selezionabili.
- Seleziona pagina rispetta filtro e paginazione. La selezione puo continuare su altre pagine.
- Premere il cestino dedicato alle anteprime selezionate e leggere il riepilogo.
- Confermare oppure Annulla. Solo le GIF scelte e i relativi .motion.json/PNG
  vengono spostati nel Cestino; gli MP4 e le GIF non scelte restano.
- Selezione video e selezione anteprime sono separate; il contatore mostra entrambe.
- Deseleziona agisce sul tipo attualmente scelto.
- I cestini sono disabilitati quando la relativa selezione e vuota.
- Le operazioni su tutte le anteprime o tutti i file locali restano soltanto
  in Impostazioni > Archiviazione, separate dalla selezione Gallery.
Nessuna cancellazione sulla microSD. Prima prova su copie non importanti.
Il Cestino non viene svuotato. I file cambiati dopo la conferma non vengono spostati.

## 3. Identificativo unico
Un solo campo visibile Device ID, modificabile. Username viene ricavato dallo stesso
numero al salvataggio, come richiesto per questa telecamera. Rimossa la casella
Modifica identificativi telecamera. Password e Portachiavi invariati.
La configurazione esistente non viene riscritta all'avvio. Premere Salva applica
la corrispondenza Device ID/username. Non adatto senza modifiche a modelli che
richiedano uno username diverso dal Device ID.

## 4. Impostazioni anteprima
Sezioni compatte: Generazione, Animazione creata, Intervallo sorgente,
Visualizzazione nella Gallery. Spiegazione breve dipendente dalla modalita.
Parti significative mostra sensibilita e intervallo automatico 1-fine effettiva,
non i due campi disabilitati 1/120. Uniforme mostra Da/A e nasconde sensibilita.
Numero fotogrammi, durata GIF, profili indipendenti e Default contestuale conservati.
Le note sulle GIF esistenti sono in un dettaglio espandibile.
Nessuna rigenerazione automatica delle anteprime esistenti.

## 5. Player esterni
Scelte tutte visibili, non soltanto un menu chiuso che mostra VLC.
Video: VLC, IINA, QuickTime, predefinito macOS.
Anteprime: predefinita macOS, Anteprima, VLC, IINA.
Due preferenze indipendenti, una per tipo; non significa aprire piu player insieme.
Le app devono essere installate e supportare il formato; non vengono installate.
Gli errori di apertura ora sono segnalati, non ignorati.
Riquadri interni video/GIF conservati; la scelta interno/esterno resta separata.
Streaming diretto microSD e Apri Live in VLC restano specifici per VLC.
Non dichiarato risolto il problema audio VLC segnalato in precedenza.

## Conservazione funzioni
live_av.py, sd_playback.py e motion_preview.py identici byte per byte alla 3.14.29.
Login, runtime, indice SD, download, conversione MP4, generazione GIF e Live
confrontati via AST e invariati. Distribuzione giornaliera e player interni conservati.
Nessun dato personale, configurazione, credenziale, log o filmato utente incluso.

## Verifiche e primo collaudo
Vedere TEST_REPORT_3.14.30.txt per test effettivamente eseguiti.
Prima prova: barra titolo e trascinamento, cambio palette, tre pulsanti nativi;
poi selezione di UNA GIF senza MP4, conferma/annulla e conservazione video;
poi impostazioni anteprima e scelta indipendente dei player, salvataggio e riapertura.
Non sostituire la 3.14.29 fino al collaudo. Nessun test su telecamera reale qui.

## Riferimenti tecnici consultati
https://developer.apple.com/documentation/appkit/nswindow/stylemask-swift.struct/fullsizecontentview
https://pywebview.flowrl.com/api/
Implementazione Cocoa e drag-region ispezionate nel wheel pywebview 6.2.1
scaricato per verifica; wheel non incluso nel pacchetto.
