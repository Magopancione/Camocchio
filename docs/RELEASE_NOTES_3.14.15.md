# 3.14.15 - Gallery e palette

- Elementi per pagina spostati in Gallery: 6, 12, 18, 24, 30, 36, 48, 60, Tutti. Valori legacy 8/16 migrano visivamente a 12.
- Flag Mostra solo il giorno selezionato: filtra video e GIF usando la data mostrata nella card. Si riferisce alla data del calendario registrazioni, non necessariamente a oggi.
- Controlli Gallery salvati automaticamente, senza premere Salva nelle Impostazioni.
- Seleziona video pagina rispetta filtro e paginazione. Le selezioni gia fatte restano anche se nascoste dal filtro: il contatore mostra il totale da cestinare.
- Clic dalla timeline apre la pagina corretta della Gallery; se il filtro nasconde la card, viene disattivato solo nella sessione.
- LED verde dopo risposta riuscita di login/indice SD, indipendente dalla palette. Non e un monitor continuo. Giallo = verifica/non confermato, rosso lampeggiante = test login fallito.
- Palette in Impostazioni: viola originale, verde bosco, magenta, arancio ambra, blu indaco, turchese petrolio. Cambio immediato e salvataggio automatico. Ispirazione cromatica dalle immagini, senza includere le immagini del prodotto esterno.
- Audio, login, protocollo, download e Cestino invariati rispetto alla 3.14.14.
- Nessuna nuova analisi movimento o anteprima streaming.
- Build ancora da collaudare su macOS/telecamera.

Verifiche locali superate: sintassi Python/JavaScript, test statici, test logica filtro/data/Tutti e test HTTP di persistenza preferenze con configurazione temporanea. Nessuna prova sulla telecamera o sul browser del Mac.
Con Tutti molte GIF possono aumentare uso memoria/CPU: preferire 12 o 18 su raccolte grandi.
