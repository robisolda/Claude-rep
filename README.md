# Monitor anomalie di prezzo → WhatsApp

Controlla ogni ora le offerte di **telefonia** su MediaWorld, Euronics, Unieuro e
Amazon.it e invia un messaggio WhatsApp quando un prodotto costa **almeno il 50% in
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
5. Se `prezzo attuale ≤ riferimento × 0,5` invia il messaggio WhatsApp.
6. Salva lo storico in `data/history.json` (commit automatico) ed evita di
   ri-notificare lo stesso prodotto allo stesso prezzo per 24 ore.

Esempio di messaggio:

```
⚠️ Anomalie di prezzo rilevate

🚨 *Amazon.it* -59%
Apple iPhone 15 128GB
💶 399.00 € (rif. 979.00 € – prezzo di listino)
https://www.amazon.it/dp/B0...
```

## Configurazione WhatsApp

### Opzione A — CallMeBot (gratuito, consigliato per uso personale)

1. Salva in rubrica il numero **+34 694 29 84 96** (CallMeBot).
2. Inviagli su WhatsApp il messaggio: `I allow callmebot to send me messages`.
3. Riceverai la tua **API key**.
4. Nel repository GitHub: *Settings → Secrets and variables → Actions → New repository secret*:
   - `WHATSAPP_PHONE` = il tuo numero con prefisso, es. `+393331234567`
   - `CALLMEBOT_APIKEY` = la API key ricevuta

> Verifica il numero aggiornato di CallMeBot su <https://www.callmebot.com/blog/free-api-whatsapp-messages/>.

### Opzione B — Twilio

Aggiungi i secret `WHATSAPP_PHONE`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_WHATSAPP_FROM` (es. `+14155238886` per la sandbox). Se presenti, Twilio ha
la precedenza su CallMeBot.

## Avvio

- Automatico: una volta configurati i secret, l'Action gira ogni ora.
- Manuale: tab *Actions → Monitor anomalie di prezzo → Run workflow*.
- In locale:

  ```bash
  pip install -r requirements.txt
  python -m price_monitor --dry-run   # stampa i messaggi senza inviarli
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
