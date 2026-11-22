# V380 Mac 3.14.22 - Indicatori anteprima e audio SD sperimentale

Avviare **Avvia_V380_Mac.command** nella radice di QUESTO pacchetto. Chiudere prima la vecchia app con Ferma Live e Esci. Conservare la versione funzionante precedente. Il problema del vecchio avvio .app non e dichiarato risolto.

## Card Gallery
Indicatore modalita a sinistra sopra l'immagine: occhio per Parti significative, griglia per Uniforme. Tooltip al passaggio del mouse con descrizione. Stato MP4 verde/rosso a destra, sopra l'immagine. La selezione multipla resta disponibile.

La modalita e letta dal metadato della GIF effettiva, NON dalle impostazioni attuali. Per GIF precedenti senza metadati compare Modalita da verificare: usare Rigenera anteprima. Le GIF movimento della release precedente hanno gia un report e possono essere riconosciute. Se richiesto movimento ma usato fallback uniforme, viene indicato esplicitamente.

## Default separati
- Uniforme: 50 fotogrammi, durata GIF 10 secondi, sorgente 10-60 secondi.
- Parti significative: 30 fotogrammi, durata GIF 7 secondi, sorgente dal secondo 1 fino alla fine reale.
- In modalita movimento il campo numerico Fine mostra 120: e il riferimento convenzionale per fine video, NON un taglio fisso a 120 se il video ha altra durata. Campi Inizio/Fine disabilitati per rendere esplicita la modalita automatica.
- Default ripristina SOLO il profilo attualmente selezionato. Cambiare modalita conserva fotogrammi/durata dell'altra. Durate salvate separatamente (preview_seconds e motion_seconds).
- Valori gia salvati sono conservati. Per adottare 30/7 nella configurazione esistente selezionare Parti significative, premere Default e poi Salva.
- Le GIF esistenti non vengono rigenerate automaticamente. Usare Rigenera anteprima nel pannello del video.
- Analisi movimento max 600 secondi, oltre tale limite fallback uniforme sull'intervallo 1-fine. Non identifica persone.

## Prova audio in stream
Interpretazione: audio di **Riproduci dalla microSD in VLC**, non audio del Live RTSP. In Impostazioni > Altro attivare **Audio sperimentale in Riproduci dalla microSD (VLC)** e Salva. Fermare una eventuale riproduzione precedente e riavviare dalla riga del filmato.

Decodifica blocchi type22 IMA ADPCM da 256 byte, 505 campioni per blocco, 8kHz mono. Video e PCM vengono inviati in pipe separate a FFmpeg, che produce H264 + AAC MPEG-TS verso VLC. Nessun MP4 scritto o aggiunto alla Gallery. Coda limitata in memoria. Flag disattivato per default: disattivarlo per tornare alla prova solo video.

**Sperimentale:** video ancora ipotizzato 20 fps, timestamp sorgente non ancora interpretati. Offset iniziale e deriva audio/video non compensati; verificare sincronizzazione all'inizio e alla fine. Se il clip non contiene audio compatibile o il formato differisce, la prova puo non partire o terminare: disattivare il flag e riprovare solo video. Il Live RTSP resta senza audio. Download MP4, login e Live invariati.

## Verifiche locali
Sintassi Python/JS; test cambio profilo e Default contestuale; persistenza HTTP; badge dai metadati; regressioni movimento e playback solo video. Decoder IMA confrontato con FFmpeg su audio SINTETICO: campioni PCM identici. Test end-to-end con camera simulata e FFmpeg reale: tracce H264 e AAC mono 8kHz presenti. Nessuna prova sulla telecamera reale/macOS in questa sessione.

## Pacchetto pubblico
Sorgenti, risorse, launcher, app non firmata/non notarizzata in dist, script e test. Nessun IP/Device ID/username personale precompilato. Configurazione e Portachiavi gia presenti sul Mac restano esterni. Richiede Python 3.9+, FFmpeg/FFprobe e VLC. Nessuna licenza scelta automaticamente. I report .motion.json sono locali e ignorati da Git.

```bash
python3 scripts/build_macos.py
python3 -m unittest discover -s tests -v
node tests/test_preview_profiles.cjs
```
