# V380 Mac 3.14.24 - Pannello Video / Anteprima e tooltip

## Avvio
Chiudere la precedente istanza con Ferma Live e Esci. Estrarre il pacchetto in una nuova cartella e avviare Avvia_V380_Mac.command nella radice. Conservare la 3.14.23 come rollback. Il problema del vecchio avvio .app non e dichiarato risolto: il bundle incluso resta non firmato/non notarizzato e richiede Python/FFmpeg installati.

## Novita
- Pannello separato in due sezioni Video e Anteprima, ognuna con informazioni e azioni proprie.
- Video locale: due pulsanti su una riga, Apri ed Elimina. Se MP4 assente: Scarica dalla SD e Riproduci dalla SD.
- Anteprima: tre pulsanti compatti con icone su una riga, Apri / Rigenera / Elimina. Rigenera disabilitato senza MP4; azioni non applicabili disabilitate. Eliminazione mantiene la conferma preesistente.
- Secondi visualizzati come interi arrotondati per eccesso: intervallo 1-119.999633 diventa 1-120 s; GIF 6.90 diventa 7 s. Nessuna modifica ai tempi effettivi o al file. Dimensioni MB mantengono i decimali per utilita.
- Sensibilita low/medium/high mostrata come Bassa/Media/Alta.
- Tavolozza colori: pulsante con icona in alto a sinistra; clic per aprire la scelta, senza etichetta Palette permanente. Salvataggio automatico gia esistente conservato.
- Icona applicazione ingrandita quasi a tutta larghezza della sidebar. Il launcher .command continua ad aprire Terminale e non ne cambia l'icona Dock.
- Occhio vettoriale e simbolo a punti con tooltip grafico al passaggio mouse, focus tastiera o clic/tap. Il tooltip si arricchisce con numero fotogrammi e durata misurati nella GIF; nessun punto interrogativo sostitutivo.
- Per GIF senza report storico si usa l'occhio ma il testo dichiara Metodo non registrato, senza inventare la modalita. Fallback uniforme dichiarato. I dettagli sono caricati su richiesta, non con una scansione FFprobe di tutta la Gallery.

## Funzioni conservate
Login, protocollo, download/audio, generazione movimento e Live invariati. Modulo sd_playback.py e motion_preview.py identici alla base allegata. Nessun nuovo algoritmo o comando sulla microSD. Profili Default restano Uniforme 50 frame/10s/intervallo 10-60 e Parti significative 30 frame/7s/intervallo 1-fine. Nessuna rigenerazione automatica delle GIF esistenti.

## Verifiche
Sintassi Python/JavaScript, confronto AST delle funzioni principali, regressioni con video/audio sintetici e protocollo simulato, test browser Chromium con API simulate: tooltip, arrotondamento, due sezioni, 2/3 pulsanti, disabilitazione Rigenera senza MP4, colori e azione stream da GIF. Non collaudato sul Mac o sulla telecamera reale. Usare .command come nelle versioni funzionanti.

## Distribuzione pubblica
Sorgenti completi, risorse, launcher, bundle in dist, script e test. Nessun IP/Device ID/username personale precompilato, nessun config/log/video/campione audio privato. Configurazione e Portachiavi gia presenti sul Mac restano esterni. Richiede Python 3.9+, FFmpeg/FFprobe, VLC per stream SD. Nessuna licenza assegnata automaticamente; icona fornita dall'utente, verificarne i diritti prima della pubblicazione. dist escluso da Git tramite .gitignore; distribuibile come allegato di release.

```bash
python3 scripts/build_macos.py
python3 -m unittest discover -s tests -v
node tests/test_preview_profiles.cjs
```

Il test opzionale tests/browser_gallery.py richiede Playwright e Chromium, non necessari all'app.
