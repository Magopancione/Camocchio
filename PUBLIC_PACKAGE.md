# Pacchetto pubblico separato

Sorgenti senza IP, Device ID, username o nome della telecamera personale. Compilare i campi al primo utilizzo. Bundle .app pubblico incluso in dist/, senza configurazioni personali, log, filmati, anteprime o campioni audio. Le costanti del protocollo V380 sono generiche e non identificano la telecamera personale. La porta 8800 e un parametro del protocollo, non un identificativo personale.

Il codice legge la configurazione locale gia esistente sul computer: non includerla nel repository. Verificare sempre i file aggiunti prima del commit. Nessuna licenza scelta automaticamente.


## Bundle pubblico incluso
Aprire `dist/V380 Mac 3.14.16.app`. Generato dai sorgenti pubblici inclusi, senza IP, Device ID o username personali precompilati. Il Device ID neutro e 0 (da configurare), IP e username sono vuoti. App non firmata e non notarizzata; richiede Python 3 e FFmpeg installati. Non e un eseguibile autonomo con Python incorporato.

Su un Mac gia configurato legge il config.json e il Portachiavi esterni gia esistenti: eventuali valori mostrati non provengono dal pacchetto. Il .gitignore continua a escludere dist dai commit normali; distribuire il bundle come allegato di release se desiderato. Nessun caricamento Git effettuato automaticamente.
