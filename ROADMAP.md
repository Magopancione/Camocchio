# Prossime release: richieste accantonate, non implementate

## 1. Anteprime significative dopo il download

Obiettivo: mostrare i passaggi con movimento, soprattutto quando una persona si avvicina alla telecamera, anziché campionare uniformemente il video.

Distinguere due funzioni: rilevamento movimento (può includere ombre, luci, vegetazione) e rilevamento presenza persone (senza identificazione). Non promettere equivalenza tra movimento e persona.

Studio proposto: analisi locale del filmato, punteggio movimento, soglia e area d'interesse configurabili, intervalli con margine prima/dopo, limite fotogrammi e durata GIF. Valutare successivamente un rilevatore di persone con dipendenze/licenza dichiarate. Prevedere fallback al campionamento normale e falsi positivi/negativi. Nessuna analisi cloud prevista.

## 2. Anteprima progressiva dalla microSD

Obiettivo: visualizzare il playback prima di aver trasferito tutto il filmato, come esperienza d'uso dell'app ufficiale.

Fattibilità da verificare sul protocollo: avvio playback, ricezione progressiva, accesso ai keyframe HEVC, buffering, decodifica e formato riproducibile nel browser. Il browser non può leggere direttamente il protocollo TCP proprietario: serve il backend locale. La visualizzazione può richiedere ricezione e cache temporanea di una parte del video, anche se non si salva l'MP4 completo. Compatibilità HEVC del browser da verificare; non confondere playback registrato e live camera.

Non ancora garantiti seek remoto, basso traffico o assenza totale di file temporanei. Non dedurre il supporto di queste funzioni dal solo comportamento dell'app ufficiale.

## 3. Collaudo prima di nuove modifiche

Confermare audio/sincronizzazione inizio-fine, download giornata, stop coda, gestione errori e Cestino. Conservare la 3.14.13 come rollback fino alla conferma della 3.14.14. Android fuori dal perimetro di questo pacchetto.
