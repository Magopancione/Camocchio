# Diagnostica Live V380 su TCP 8800 (macOS)

**Non occorre compilare Camocchio.** Estrarre lo ZIP. Chiudere Camocchio e fermare la diretta dell'app ufficiale. Usare il Mac sulla stessa rete della propria telecamera. Nelle impostazioni già salvate di Camocchio devono esserci un IPv4 locale e TCP 8800. Se la porta salvata è 8880, lo script non la cambia e non invia richieste. Per la decodifica serve FFmpeg installato sul Mac (è lo stesso prerequisito di compilazione di Camocchio). Python 3.9 o successivo.

1. Dal Finder aprire `TEST_LIVE_8800_APPROFONDITO.command`. In alternativa, da Terminale nella cartella estratta, eseguire `bash TEST_LIVE_8800_APPROFONDITO.command`. Premere Invio per avviare. Autorizzare l'accesso alla voce Portachiavi di Camocchio se macOS lo chiede e si riconosce la richiesta. Non si riutilizza il ticket della sessione aperta: viene ottenuto un ticket nuovo con il login già usato per microSD.
2. Fare un suono breve vicino alla telecamera durante la prova, evitando conversazioni private. Si provano in sequenza due richieste documentate di profilo, basso e alto, con ricezione di massimo 12 secondi ciascuna (oltre a connessione, login e decodifica). Variante più breve: `TEST_LIVE_8800.command`, un profilo e fino a 6 secondi di ricezione.
3. Copiare soltanto il JSON stampato a fine prova. Non contiene credenziali, ticket, indirizzi o campioni. Non sono scritti file audio/video o catture di rete. Se macOS nega il Portachiavi, non aggirarne il controllo: verificare la voce e l'autorizzazione.

## Come leggere il risultato
- `login: true`: la telecamera accetta le credenziali. Non basta per dire che offre un Live.
- `setup.accettata` e `richiesta_live_inviata`: lo script distingue l'inizializzazione dalla richiesta di avvio effettivamente inviata.
- `pacchetti_per_tipo` e `frame_ricomposti`: il parser riconosce il formato a frammenti atteso; non provano da soli la decodifica.
- `frame_decodificati > 0`: FFmpeg ha prodotto fotogrammi H.264 o HEVC dai dati arrivati dopo l'avvio. Non è una misura di fluidità o latenza.
- `aac_campioni_decodificati > 0`: FFmpeg ha ricavato campioni PCM da AAC identificato. `blocchi_compatibili_ima` e relativo picco sono indizi di compatibilità, non una prova di ascolto corretto; non si classifica automaticamente audio sconosciuto come G.711. Un risultato negativo non esclude un altro formato/profilo/firmware.

## Ambito
Solo la telecamera IPv4 privata già configurata sulla 8800; nessuna scansione, RTSP, cloud, credenziale su riga di comando, tentativi di password, microSD, scrittura, PTZ o download di registrazioni. Chiusura del socket dopo il campione. Nessuna modifica al player del programma. Il parser diagnostico non è uno streamer di produzione.

Riferimenti pubblici: https://github.com/prsyahmi/v380/blob/master/v380/v380.cpp (richieste LAN, struttura dei frammenti), https://github.com/prsyahmi/v380/blob/master/v380/UtlSocket.cpp (dimensione dei buffer di risposta), https://github.com/denial19/v380-4g-openwrt-recorder/blob/main/docs/PROTOCOL.md (tipi ed esempi di firmware diversi; nessun relay viene contattato da questo script).
