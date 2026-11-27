# Camocchio Mac 3.14.42, candidata

Base: sorgenti 3.14.41 allegati, verificati con manifest SHA-256 prima delle modifiche. Conservare separatamente 3.14.41, 3.14.40 e il tag mac-v3.14.39. Nessuna modifica ad Android, menu laterale, codec, trasporto, backend microSD o algoritmo delle anteprime.

## Live

- La finestra apre la vista Live e richiede automaticamente **TCP 8800, Alta, con audio** quando è disponibile la configurazione. Il pulsante passa a **Ferma Live** già durante la connessione. Se Safari o WKWebView blocca la riproduzione automatica con audio, premere **Riproduci** nel riquadro. Alla prima configurazione salvare i dati e premere **Avvia Live**, oppure riaprire l’app.
- Riquadro ispirato al rendering: stato, selettori grandi **TCP 8800 / RTSP** e **Bassa / Alta** (solo TCP 8800), video con badge di stato, barra con play/pausa, volume, 1×/2× e schermo intero, pulsante Avvia/Ferma, salti di +2/+5/+10/+30 s, Torna in diretta e diagnostica richiudibile. L’anteprima del rendering non è inclusa: il player mostra soltanto lo stream reale. Per l’aspetto blu del rendering usare la palette blu già disponibile. La qualità scelta durante la sessione non cambia l’avvio successivo, che resta sempre in Alta.
- Selezionare un’altra sorgente avvia il nuovo flusso dopo aver fermato il precedente; nessun fallback automatico. Passare a Registrazioni o Gallery dal Live ferma la diretta per liberare la sessione prima dell’uso della microSD. Tornare alla pagina Live non la riavvia da solo: premere Avvia Live. I salti rispettano il tratto navigabile. In modalità RTSP senza audio (anteprima JPEG) il player non ha i controlli temporali del flusso HLS.
- Rimossa la scelta 4× dai controlli personalizzati dei player interni (Live, MP4 e microSD); i controlli nativi ed esterni non sono modificati.
- Nulla cambia nella pipeline audio/video. Il primo fotogramma può attendere il buffer HLS; non è implementato l’avvio anticipato del solo video né una correzione automatica del ritardo. La diagnostica distingue tempi del player e misure manuali della scena.

## Registrazioni: correzione -1 ora

Il valore salvato non veniva propagato dal runtime alla lettura della microSD. Ora l’elenco, la distribuzione oraria e gli orari mostrati seguono l’opzione. Esempio verificato: 08:01:56–08:03:56 senza correzione, 07:01:56–07:03:56 con correzione. La modifica si applica al salvataggio e al ricaricamento dell’elenco; non muta i timestamp originari usati dal protocollo né rinomina i file esistenti. La ricerca del giorno in telecamera non cambia.

## Primo collaudo

Estrai in una cartella nuova e locale, fuori da iCloud, ad esempio ~/Developer/Camocchio_Mac_3.14.42. Chiudi le versioni già aperte e il Live dell’app ufficiale. Per provare senza build avvia Avvia_V380_Mac.command e usa Safari; per la .app esegui bash CREA_APP_MAC.command e apri dist-native/Camocchio.app. Lo ZIP contiene sorgenti, non la .app precompilata.

1. Apri e verifica che parta Live via TCP 8800 in Alta e si senta l’audio; se macOS lo chiede, consenti rete locale e Portachiavi. Prova cambio Bassa/Alta, passaggio RTSP, torna al TCP 8800 e prova Ferma Live.
2. Entra in Registrazioni e prova la spunta Correzione ora video (-1 ora) in Impostazioni > Telecamera, con Salva. Confronta gli orari prima e dopo e prova una registrazione con audio.
3. Controlla Play/Pausa, volume, tasto schermo intero, 1×/2× e i salti nel buffer. Per valutare il ritardo, usa il cronometro inquadrato e un battito visibile a inizio prova e dopo 3 minuti.

Verificati in Linux: startup e comandi in Chromium con API simulate, selettori e visibilità, 1×/2×, salti consentiti, ritorno al bordo, diagnostica, errore e configurazione assente; test HTTP del flag orario con risposta microSD sintetica, invarianti dei timestamp originali; pipeline TCP 8800 e RTSP simulati, audio microSD e playback, Gallery, batch, profili GIF. Build macOS, autoplay nativo, audio, fullscreen e latenza sulla telecamera reale restano da collaudare.
