# Camocchio Mac 3.14.39, candidata

Partendo dalla 3.14.38, che rimane separata. Sorgenti e script, non una app macOS già compilata. Estrarre separatamente e usare CREA_APP_MAC.command per generare dist-native/Camocchio.app. La diagnostica sotto si può avviare anche senza compilare.

- Gallery: una sosta del puntatore di circa 650 ms sul riquadro «Anteprima non disponibile» genera la GIF di quel singolo MP4 locale. Se il puntatore esce prima, non parte. Le GIF esistenti non vengono sovrascritte. Basta cliccare nei dettagli e scegliere Crea anteprima per l'alternativa esplicita. Crea anteprime mancanti rimane disponibile. Se la coda è attiva, la creazione al passaggio del mouse attende una nuova azione dell'utente dopo che la coda è terminata.
- Registrazioni e Gallery: nuova icona del disco dalle linee orizzontali argentate, usando direttamente l'immagine fornita con la mela verde, ritagliata e ridotta. Icone SD e modalità GIF invariate.
- Player, Live, riproduzione microSD, finestra e generatori GIF non riscritti; test diagnostici in script separati, nessuna modifica a configurazione o Portachiavi.

Vedi docs/DIAGNOSTICA_8800.md per l'uso. Colloquio camera e decodifica verificati con simulazione locale TCP e media sintetici (H.264, HEVC cifrato con il formato candidato e AAC), non sul Mac o sulla telecamera fisica. Test browser: passaggio breve senza richiesta, passaggio prolungato per il solo MP4, nessuna richiesta successiva su una GIF già presente, caricamento icona e regressioni Gallery/SD. Regressioni batch, player SD audio, bridge, HTTP e sintassi.
