---
name: infographic-builder
description: "Costruisce infografiche per le analisi del Centro Studi (CS) e di Cosmetica Italia Servizi (CIS): numeri chiave, grafici e testi in stile Centro Studi in un'unica pagina condivisibile. Usala quando Rob chiede un'infografica, una sintesi visiva, una scheda o un one-pager su dati di settore (fatturato, export, consumi, canali, categorie, imprese)."
---

# Infographic builder – Centro Studi / CIS

Trasforma un'analisi (dati, tabelle, report, slide) in un'infografica a pagina singola: un messaggio principale, 3–6 blocchi di evidenza, fonti dichiarate. L'infografica sintetizza; non aggiunge interpretazioni che il report non sostiene.

## Prima di iniziare
1. **Carica le skill collegate**, in quest'ordine:
   - `stile-testi-centro-studi` per tutti i testi (titolo, box, takeaway, fonti). Le sue regole valgono integralmente: qui sotto se ne richiamano solo le applicazioni all'infografica.
   - `dataviz` prima di scrivere qualsiasi grafico.
   - `artifact-design` (o la `quickstart` del tool Artifact) prima di scrivere la pagina.
2. **Raccogli i dati.** Lavora solo sui numeri forniti da Rob (file, tabelle, testo incollato, report). Non inventare, non completare serie mancanti, non arrotondare in modo diverso dalla fonte. Se un dato serve e manca, chiedilo o lascia il blocco fuori.
3. **Chiarisci solo se serve davvero**: destinatario (CS interno, soci, stampa, evento), formato (pagina web, PNG, slide) e se c'è una presentazione istituzionale con cui i numeri devono coincidere. Se non è indicato: pagina web pubblicata come Artifact, formato verticale.

## Struttura dell'infografica
Dall'alto verso il basso:

1. **Titolo-messaggio.** La tesi sta nel titolo, non la descrizione ("Nel 2026 il mercato interno sostiene la crescita, l'export rallenta", non "Dati del settore cosmetico 2026"). Sotto, un sottotitolo con perimetro e periodo: "(Industria cosmetica italiana, valori in miliardi di euro e var. % annue)".
2. **Numeri chiave (2–4 tile).** Un numero grande, un'etichetta breve, un confronto: "**18,1 mld** · fatturato 2026 (stima) · +1,0% sul 2025". Il confronto è obbligatorio: periodo precedente, media del settore, Europa.
3. **Blocchi di evidenza (2–4).** Ognuno ha:
   - un box insight di 1–2 frasi, 25–45 parole, spesso senza punto finale, con 2–5 parole chiave in **bold**;
   - un grafico o una piccola tabella che dimostra esattamente quella frase;
   - il titolo del grafico come messaggio, con unità e frequenza in sottotitolo.
   L'ordine segue i livelli del CS: contesto macro → scenario internazionale → industria → consumi → nuovi comportamenti della domanda. Si usano solo i livelli per cui ci sono dati.
4. **Key take-home message.** 2–4 etichette in MAIUSCOLO ("DIVERSIFICAZIONE", "NUOVO CONSUMATORE") con una frase di spiegazione in minuscolo. Devono coincidere con titolo e box.
5. **Piede.** Fonti e note metodologiche: "Elaborazione: Centro Studi – dati [Fonte], *mese anno*". Stime e preconsuntivi dichiarati come tali ("stima", "preconsuntivo marzo 2026"). Per CIS indicare "Cosmetica Italia Servizi" se è il soggetto che firma.

## Scelta del grafico
Un grafico per messaggio, il più semplice che regge il confronto:
- **Andamento nel tempo** → linea (serie lunghe) o colonne (≤ 8 anni). Evidenzia l'ultimo anno o la stima con un tratto/colore diverso e l'etichetta "stima".
- **Confronto fra canali, categorie, aree** → barre orizzontali ordinate per valore, etichette dirette sui valori.
- **Composizione** (quote di canale o di categoria) → barra 100% o barre orizzontali; torta/ciambella solo con ≤ 4 parti.
- **Variazioni** → barre divergenti attorno a zero, positivi e negativi con colori distinti.
- **Due misure sulla stessa entità** (es. 2024 vs 2025) → dumbbell o barre affiancate, non doppio asse.
- **Un solo numero** → tile, non grafico.
Etichette dei valori in formato italiano ("18,1", "+1,6 p.p.", "-0,4%"). Niente 3D, niente doppio asse Y, asse delle barre sempre da zero.

## Regole di testo (dallo stile CS, applicate all'infografica)
- Ogni frase interpretativa poggia su un numero visibile nello stesso blocco.
- Associazione, non causalità: "si associa a", "si accompagna a"; evita "grazie a", "trainato da", "determina" se il nesso non è dimostrato.
- "Strutturale" solo con evidenza pluriennale nei dati mostrati.
- Tono misurato sulle previsioni: "potrebbe raggiungere", "è atteso", "segnale da monitorare".
- Niente enfasi ("boom", "record", "straordinario") se il dato non lo giustifica.
- Lessico di settore: categorie (cura pelle, detergenza, cura capelli, make-up, fragranze), canali (GDO, farmacia, profumeria, erboristeria, monomarca, e-commerce, acconciatura, estetica), aree (Asia Pacifico, Europa, Nord America, America latina, Medio Oriente e Africa).
- Sigle sciolte alla prima occorrenza, salvo quelle d'uso comune nel settore.

## Aspetto
- Parti da `assets/template.html`: contiene la struttura (testata, tile, blocchi, take-home, piede), i token colore e i modi chiaro/scuro.
- **Palette istituzionale** (dalle slide CS, già nei token del template):

  | Ruolo | Colore | Token |
  |---|---|---|
  | Sfondo dominante (beige) | `#f2efe6` | `--bg` |
  | Titoli (blu notte) | `#2a3054` | `--title` |
  | Testo | `#303143` | `--text` |
  | Contesto macroeconomico (blu ardesia) | `#58798a` | `--brand-1` / `.s1` |
  | Scenari internazionali (bordeaux) | `#891a2d` | `--brand-2` / `.s2` |
  | Settore beauty Italia (verde oliva) | `#616936` | `--brand-3` / `.s3` |
  | Trend di consumo (terracotta) | `#b2603b` | `--brand-4` / `.s4` |

  Il colore segue il **livello dell'analisi**, non l'ordine dei blocchi: un blocco sui canali è sempre verde, uno sull'e-commerce sempre terracotta. Il colore di sezione colora fascia, bordo, bold del box e serie principale del grafico; le serie secondarie usano tinte più chiare dello stesso colore o grigio (`--muted`), non gli altri colori di sezione. Lo sfondo resta beige: niente bianco puro come sfondo pagina. Le fasce di sezione (`.band`) hanno la forma a freccia delle slide e testo bianco.
- **Font:** Segoe UI, con fallback `system-ui, -apple-system, Roboto, Arial`. Non va caricato da Google Fonts (non c'è): chi non ha Windows vede il fallback. Per un PNG da consegnare, rendere su una macchina con Segoe UI o dichiarare che il font è un sostituto.
- Larghezza massima ~900 px, una colonna su mobile, due colonne per i blocchi da desktop. Nessuno scroll orizzontale.
- Nessun logo o marchio di Cosmetica Italia o di terzi, a meno che Rob non fornisca il file e chieda di usarlo.

## Consegna
- **Pagina web (predefinito):** scrivi l'HTML nello scratchpad e pubblicalo con il tool Artifact (icona `chart`). Dai il link e una riga su cosa contiene.
- **PNG:** rendi la pagina con Playwright/Chromium (`executablePath: '/opt/pw-browsers/chromium'` se serve) a 2× e invia il file.
- **Slide:** usa il tipo Slides di Artifact (o la skill `pptx` se Rob chiede un .pptx), una slide per l'infografica, stessa struttura.

## Checklist prima della consegna
- Il titolo dice la tesi? Titolo, box e take-home dicono la stessa cosa?
- Ogni numero è identico alla fonte fornita (valore, unità, arrotondamento, periodo)?
- Ogni box ha 25–45 parole e un dato nello stesso blocco?
- Ci sono verbi causali senza prova, "strutturale" su un anno, enfasi o formule logore?
- Stime e preconsuntivi sono etichettati come tali, nel grafico e nel piede?
- Fonti presenti per ogni blocco, nel formato CS?
- Leggibile in modo chiaro e scuro e a larghezza telefono?
- Se esiste una presentazione istituzionale collegata, numeri e messaggi coincidono?
