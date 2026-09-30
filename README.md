# Monitor anomalie di prezzo → email Gmail

Controlla ogni ora le offerte di **telefonia** su MediaWorld, Euronics, Unieuro e
Amazon.it e ti invia una **email** quando un prodotto costa **almeno il 50% in
meno** del suo prezzo medio di riferimento.

## Come funziona

1. Una GitHub Action (`.github/workflows/price-monitor.yml`) parte ogni ora.
2. Scarica le pagine elencate in `config.yaml` (prima con HTTP semplice, poi con
   Chromium headless se il sito richiede JavaScript o blocca la richiesta).
3. Estrae nome, prezzo e prezzo barrato di ogni prodotto (parser Amazon dedicato,
   dati strutturati schema.org, stato JSON della pagina, schede HTML).
4. Calcola il **prezzo di riferimento** come media tra:
   - il prezzo di listino/barrato mostrato dal negozio, se presente;
   - la media dei prezzi rilevati negli ultimi 30 giorni (dopo almeno 3 rilevazioni).
5. Se `prezzo attuale ≤ riferimento × 0,5` ti invia una email (una sola per esecuzione, con tutte le anomalie in tabella).
6. Salva lo storico in `data/history.json` (commit automatico) ed evita di
   ri-notificare lo stesso prodotto allo stesso prezzo per 24 ore.

Esempio di oggetto: `Anomalia prezzo -59%: Apple iPhone 15 128GB (Amazon.it) e altre 2`.
Il corpo contiene una tabella con negozio, prodotto (con link), prezzo, riferimento e sconto.

## Configurazione Gmail

L'invio usa il server SMTP di Gmail con una **password per le app** (la password
normale dell'account non funziona).

1. Attiva la verifica in due passaggi sull'account Google, se non l'hai già fatto.
2. Vai su <https://myaccount.google.com/apppasswords>, crea una password per l'app
   (es. "Price monitor") e copia il codice di 16 caratteri.
3. Nel repository GitHub: *Settings → Secrets and variables → Actions → New repository secret*:
   - `GMAIL_USER` = il tuo indirizzo Gmail
   - `GMAIL_APP_PASSWORD` = il codice di 16 caratteri
   - `EMAIL_TO` *(facoltativo)* = destinatario diverso; se assente l'email arriva a `GMAIL_USER`

Consiglio: crea un filtro Gmail sull'oggetto "Anomalia prezzo" per etichettarle o
ricevere una notifica dedicata sul telefono.

## Avvio

- Automatico: una volta configurati i secret, l'Action gira ogni ora.
- Manuale: tab *Actions → Monitor anomalie di prezzo → Run workflow*.
- In locale:

  ```bash
  pip install -r requirements.txt
  python -m price_monitor --dry-run   # stampa l'email senza inviarla
  python -m pytest                    # test
  ```

## Personalizzazione (`config.yaml`)

| Chiave | Significato |
|---|---|
| `threshold` | sconto minimo (0.50 = -50%) |
| `min_history_samples`, `history_days` | quando e su quale finestra usare la media storica |
| `renotify_after_hours` | intervallo anti-duplicati |
| `min_price`, `exclude_keywords` | filtri per ignorare accessori e usato |
| `sources` | pagine da monitorare (aggiungi altre categorie o ricerche) |

## Limiti noti

- I siti (in particolare Amazon e MediaWorld) usano protezioni anti-bot: dai server
  GitHub alcune richieste possono essere bloccate. Il log dell'Action riporta quanti
  prodotti sono stati letti per ogni fonte; se una fonte resta a 0, aggiorna l'URL o
  valuta di eseguire lo script da un PC/Raspberry di casa (es. con `cron`).
- I negozi cambiano spesso il markup: se un parser smette di funzionare va adattato.
- Le prime ore senza prezzo barrato non generano avvisi finché non si accumulano
  almeno 3 rilevazioni storiche per prodotto.
