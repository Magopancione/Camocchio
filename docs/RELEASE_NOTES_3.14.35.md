# Camocchio Mac 3.14.35 — candidata

Base: archivio sorgente 3.14.34 fornito dall'utente. Tenere separati i due ZIP e le due build. Android invariato. Nessuna .app precompilata.

Estrarre in una cartella nuova, lanciare CREA_APP_MAC.command, aprire dist-native/Camocchio.app dopo il completamento. Configurazione e Portachiavi restano condivisi tra le build: per tornare al Live precedente lasciare vuoto Percorso audio RTSP separato.

## Interfaccia
- Orario a sinistra, stato al centro, azioni a destra. Su finestre strette l'orario usa una riga propria. Sidebar e logica microSD invariati.
- Uniforme: pellicola a riquadri azzurri. Parti significative: mirino con onda ambra. Il ripiego uniforme usa il simbolo della pellicola con tooltip esplicito; un metodo sconosciuto non viene indovinato.
- Il conteggio degli intervalli compare sotto le icone in Registrazioni e Gallery se il report della GIF contiene gli intervalli. Nessuna rigenerazione automatica. Zero significa che il report non ha intervalli; una GIF uniforme priva di analisi non mostra un falso zero.
- Filtri Tutte / Solo microSD / Sul Mac. La timeline rappresenta la giornata intera; un segnaposto nascosto dal filtro ripristina Tutte. Download in blocco invariato e riferito all'intera giornata.

## Live
In Live > Diagnostica Live usa Verifica tracce RTSP dopo aver fermato Live e operazioni microSD. FFprobe esamina solo i profili salvati; timeout per profilo 9 secondi. La verifica riporta codec trovati, senza riportare URL, password o output grezzo. Una traccia elencata non prova che il microfono produca suono.
Un eventuale percorso audio RTSP noto sullo stesso host/porta si può salvare in Telecamera > Connessione Live / RTSP. Il Live HLS combina il video principale e l'audio del secondo profilo. Nessuna ricerca automatica di percorsi. Lasciare il campo vuoto per mantenere il percorso precedente. Se il profilo separato non offre audio o non risponde, svuotare il campo e riprovare.
La porta TCP 8800 raggiungibile non identifica un profilo RTSP né il protocollo Live proprietario. Questa release non implementa il Live proprietario 8800. HLS ha buffering e non è istantaneo; latenza, sincronismo e udibilità reali sul Mac non sono misurati.

## Collaudo Mac
1. Avviare, verificare menu fermo e filtri; aprire una GIF per metodo e controllare gli indicatori.
2. Ripetere due volte Avvia / Ferma Live con percorso separato vuoto. Provare Verifica tracce RTSP a Live fermo.
3. Solo se disponibile un profilo audio documentato per la telecamera, inserirlo, ripetere Avvia / Ferma e confrontare un suono noto con il video; controllare ritardo e sincronismo per almeno un minuto.
4. Riprovare microSD interna da Registrazioni e da Gallery; un solo riquadro, audio e stop con Chiudi/Esc.

Verifiche locali: vedere TEST_REPORT_3.14.35.txt. Test in Linux: browser con risposte simulate, media sintetici e FFmpeg reale. Non eseguiti sul Mac o sulla telecamera dell'utente.
