# V380 Mac 3.14.16

Applicazione sperimentale per macOS per consultare e scaricare le registrazioni microSD di una telecamera V380 sulla rete locale. Interfaccia web locale, sorgente Python incluso e modificabile.

## Stato della versione

**Release candidata, in collaudo: non dichiarata baseline stabile.** Deriva dalla copia 3.14.13 fornita dall'utente. Il campione audio originale è stato decodificato come IMA ADPCM e confermato all'ascolto dall'utente. La nuova integrazione completa e le operazioni massive richiedono ancora prova sul Mac e sulla telecamera.

## Funzioni

- Login proprietario TCP 8800 e lettura indice microSD.
- Registrazioni per data, navigazione giornaliera e timeline.
- Download HEVC/H.265 e creazione MP4.
- Audio type 22: blocchi IMA ADPCM integri da 256 byte, conversione in AAC mono 8 kHz.
- Gallery paginata, GIF su richiesta, intervallo/fotogrammi/durata configurabili.
- Nome telecamera, player selezionabile e credenziali nel Portachiavi macOS.
- Download giornata in coda sequenziale; salto degli MP4 già presenti e arresto dopo il file in corso.
- Selezione multipla MP4 e spostamento nel Cestino locale con conferma; GIF conservate.

## Requisiti

macOS, Python 3.9 o successivo, FFmpeg e FFprobe disponibili sul Mac. Nessun pacchetto Python di terze parti richiesto dal codice attuale. Le operazioni Portachiavi e apertura player dipendono dagli strumenti macOS. FFmpeg non è incluso nel repository.

## Avvio dal sorgente

```bash
python3 src/app.py
```

Il server ascolta su `127.0.0.1` e apre il browser. Configurare IP, Device ID, username e password nelle Impostazioni. I valori di rete precompilati nel sorgente sono quelli dell'ambiente di sviluppo: modificarli per altri dispositivi.

## Ricreare il bundle .app

```bash
python3 scripts/build_macos.py
```

Il risultato è `dist/V380 Mac 3.14.16.app`. Il bundle non è firmato né notarizzato. Per usarlo occorrono i requisiti sopra indicati. Nel pacchetto pubblico dist contiene il bundle generato dai sorgenti pubblici.

## Dati e credenziali

- Configurazione: `~/Library/Application Support/V380 Mac 2/config.json`.
- Password: Portachiavi macOS; non nel repository.
- Log: `~/Library/Logs/V380Mac2.log`.
- Video predefiniti: `~/Movies/V380`; GIF nella sottocartella `Thumbnails`.
- Il repository non contiene filmati, campioni audio, password o chiavi di sessione.
- Prima di pubblicare controllare comunque IP/identificativi precompilati nel sorgente: possono essere rimossi o sostituiti per un repository pubblico.

## Operazioni massive: perimetro

**Cestina selezionati riguarda soltanto gli MP4 sul Mac. Non cancella la microSD.** Le anteprime restano. Il Cestino va svuotato separatamente per liberare spazio. Le vecchie azioni di eliminazione singola conservano il comportamento preesistente: non confonderle con il nuovo comando Cestina.

Scarica giornata usa la giornata attualmente caricata. Non cambiare data durante la coda. Gli MP4 esistenti, anche senza audio, vengono saltati. Non esiste ancora ripresa di un file parziale.

## Verifiche

```bash
python3 -m unittest discover -s tests -v
```

Controlli statici e di confezionamento non sostituiscono il collaudo sul dispositivo. I test audio eseguiti durante lo sviluppo sono descritti in `docs/RELEASE_NOTES_3.14.16.md`. Sincronizzazione audio/video e stabilità della coda vanno confermate sul Mac.

## Prossime release

Vedere [ROADMAP.md](ROADMAP.md): anteprime concentrate sui movimenti e sulla presenza di persone; anteprima progressiva senza attendere l'intero download. **Non implementate in questa versione.**

## Struttura

- `src/`: sorgente effettivo, HTML/CSS/JavaScript incorporati in `app.py`, file lingue e risorse.
- `macos/`: metadati e launcher.
- `scripts/`: ricostruzione bundle.
- `tests/`: controlli statici.
- `docs/`: note di rilascio e collaudo.
- `dist/`: copia dell'app pronta, esclusa da Git.

## Git

```bash
git init
git add .
git commit -m "V380 Mac 3.14.16: audio IMA ADPCM e operazioni massive, in collaudo"
```

Non viene inizializzato né pubblicato automaticamente alcun repository remoto. Nessuna licenza open source è stata scelta per conto dell'autore: definirla prima della distribuzione pubblica e verificare la provenienza delle risorse incluse.

## Novità interfaccia 3.14.16
Controlli Gallery nella schermata principale: multipli di 3 o Tutti e filtro per giorno selezionato. Palette in Impostazioni con salvataggio automatico. Dettagli in `docs/RELEASE_NOTES_3.14.16.md`. Il LED conferma l’ultimo accesso riuscito, non una connessione permanente.

## Distribuzione pubblica
Questo ZIP contiene solo sorgenti e risorse senza identificativi personali precompilati. IP, Device ID e username vanno inseriti nelle Impostazioni. Bundle pubblico incluso in dist/; ricostruibile con lo script.


## Bundle pubblico incluso
Aprire `dist/V380 Mac 3.14.16.app`. Generato dai sorgenti pubblici inclusi, senza IP, Device ID o username personali precompilati. Il Device ID neutro e 0 (da configurare), IP e username sono vuoti. App non firmata e non notarizzata; richiede Python 3 e FFmpeg installati. Non e un eseguibile autonomo con Python incorporato.

Su un Mac gia configurato legge il config.json e il Portachiavi esterni gia esistenti: eventuali valori mostrati non provengono dal pacchetto. Il .gitignore continua a escludere dist dai commit normali; distribuire il bundle come allegato di release se desiderato. Nessun caricamento Git effettuato automaticamente.
