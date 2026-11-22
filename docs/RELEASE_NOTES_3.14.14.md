# V380 Mac 3.14.14 - Audio e operazioni massive (build da collaudare)

Base: pacchetto Mac 3.14.13 fornito dall'utente. Conservare quella copia.

## Audio
- Type 22: blocchi IMA ADPCM da 256 byte integri, intestazione di 4 byte inclusa.
- WAV IMA temporaneo: 8 kHz mono, 505 campioni per blocco.
- FFmpeg converte soltanto l'audio in AAC-LC a 16 kbit/s; video copiato HEVC, tag hvc1.
- Nessuna decifratura AES applicata all'audio di questo formato.
- Durata video ricostruita dal numero di frame ricevuti e dalla durata del segmento: verificare sincronizzazione reale.
- MP4 scritto prima come .partial.mp4, pubblicato solo a conversione riuscita.
- Dati temporanei rimossi al successo; conservati se la conversione fallisce.
- Se non arriva audio, produce un MP4 solo video. Se il formato audio e diverso dal campione validato, segnala errore.

## Scarica giornata
- Caricare la data desiderata e premere Scarica giornata; confermare.
- Usa l'elenco della giornata caricato, una registrazione alla volta.
- Salta gli MP4 gia presenti, anche quelli vecchi senza audio: per riscaricarli cestinarli prima o usare una cartella di prova diversa.
- Ferma coda termina il file in corso e non avvia il successivo.
- Non cambiare data durante la coda. Non vengono cancellate registrazioni dalla microSD.
- Nessun resume parziale: una nuova coda salta i file completati e riprova quelli mancanti.

## Cancellazione massiva
- Nella Gallery selezionare singoli MP4 o Seleziona video pagina.
- La selezione puo proseguire su piu pagine.
- Cestina selezionati richiede conferma e sposta soltanto gli MP4 nel Cestino del Mac (~/.Trash).
- Le GIF restano. Nessuna cancellazione sulla telecamera.
- Lo spazio disco viene liberato solo svuotando il Cestino.
- In caso di errore di permessi, alcuni file potrebbero essere gia stati spostati: controllare Gallery e Cestino prima di riprovare.
- I vecchi comandi di eliminazione singola conservano il comportamento della 3.14.13; il Cestino riguarda il nuovo comando massivo.

## Verifiche eseguite qui
- Sintassi Python e JavaScript.
- Confronto AST: pw, setpw, runtime, login, listrec e makegif identici alla base.
- Campione reale fornito: IMA -> AAC mono 8kHz, durata 120.001 s.
- Pipeline MP4 provata con video sintetico di test e blocchi audio reali: tracce HEVC e AAC presenti.
- Coda provata con chiamate simulate: serializzazione e salto dei file esistenti.
- Cestino provato in cartella temporanea, con conservazione GIF.
- NON eseguita l'app su macOS o sulla telecamera fisica. Non ancora baseline stabile.

## Anomalie/migliorie pregresse
- Non modificati login, Portachiavi, avvio, lingue, GIF, correzione oraria della base allegata.
- Non dichiarate risolte ulteriori anomalie pregresse: verificare avvio, salvataggio, lingua, focus Gallery paginata e numerazione.
- Timelapse aggregato giornaliero e timeline verticale restano sviluppi separati.
- Nessuna funzione cancella totale della microSD introdotta.

## Primo collaudo consigliato
1. Chiudere la vecchia app con Esci. Avviare questa copia.
2. Scaricare un filmato non gia presente con parlato. Controllare audio e sincronizzazione all'inizio e alla fine.
3. Provare una giornata con poche registrazioni, quindi Ferma coda.
4. Provare Cestina selezionati su un solo MP4 non importante; verificare GIF conservata e recuperabilita dal Cestino.

App e sorgente Python sono inclusi. Nessuna password o campione audio privato incluso.
