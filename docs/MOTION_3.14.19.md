# 3.14.19 - Anteprime Parti significative (da collaudare)

## Uso
Avviare con Avvia_V380_Mac.command nella radice di QUESTO pacchetto. Il launcher usa src/app.py accanto a se, senza cercare vecchie versioni in Downloads. Chiudere prima la vecchia app con Ferma Live e Esci. Lasciare aperto Terminale. Il bundle .app incluso non risolve il precedente problema di accesso rete: usare il .command per il Live.

Impostazioni > Anteprima > Modalita anteprima: Uniforme oppure Parti significative. Sensibilita Bassa/Media/Alta. Salvare. Default: Uniforme, per non cambiare il comportamento esistente. Numero fotogrammi (3-60) e durata GIF (1-60 secondi) restano configurabili.

L'analisi riguarda SOLTANTO l'intervallo Inizio/Fine configurato: per un filmato di 120 secondi impostare 0 e 120 per cercare in tutto il video. Non confondere durata animazione con durata sorgente. Massimo intervallo analisi 600 secondi; se superato o se l'analisi fallisce viene tentato il metodo uniforme.

Nella Gallery cliccare sulla card con MP4 e premere Rigenera anteprima. Le GIF gia presenti NON cambiano al salvataggio delle impostazioni e non vengono cancellate in massa. Se e rimasta solo la GIF serve prima riscaricare il video. Nessuna modifica all'MP4 o all'audio.

## Metodo e limiti
Analisi locale con FFmpeg a 2 fotogrammi/secondo, scala di grigi 160x90. Differenze fra immagini con compensazione della variazione media di luminosita e soglia antirumore. Sensibilita Alta abbassa la soglia e puo aumentare falsi positivi. Intervalli vicini raggruppati con breve margine. Budget di fotogrammi distribuito fra eventi separati, poi ordinato cronologicamente. Se ci sono piu eventi che fotogrammi, si seleziona un sottoinsieme distribuito lungo il tempo.

Non e rilevamento persone e non e un sistema di allarme: ombre, riflessi, vegetazione e rumore possono attivarlo; eventi brevi/piccoli/lenti possono essere persi. Non tutti i movimenti sono garantiti. Se non emerge movimento, torna al generatore uniforme originale.

La generazione puo essere piu lenta, fino a 60 estrazioni FFmpeg; un'anteprima alla volta. Un file <nome>.motion.json accanto alla GIF registra intervallo, eventi, secondi scelti e motivo dell'eventuale fallback. Non contiene immagini, ma e comunque metadato locale da non pubblicare. Nessuna analisi cloud o nuova dipendenza Python.

## Verifiche
Sintassi Python/JavaScript, salvataggio e rilettura HTTP delle nuove preferenze, confronto AST delle funzioni Live/autenticazione/download/audio rispetto al pacchetto allegato. Test su video SINTETICO con due intervalli di movimento: entrambi selezionati; GIF risultante di 12 frame e 3 secondi. Video sintetico statico: fallback uniforme verificato. Nessun test su macOS o filmato reale in questa sessione.

Test: python3 tests/test_motion_integration.py (richiede FFmpeg e FFprobe).

## Fuori perimetro
Playback progressivo microSD e riconoscimento presenza persone NON implementati. Il Live resta quello della 3.14.18, gia verificato dall'utente tramite Terminale. Conservare quella versione come rollback.
