# Lancio della demo pubblica

La demo è un servizio Django separato con una simulazione nel browser. Il checkout, la registrazione degli studi, il pannello amministrativo e i dati del gestionale non sono disponibili su questo servizio. Il contatore misura indirizzi email distinti confermati per la beta, non verifica l’identità degli studi. L’obiettivo pubblico è 100 candidature. Le richieste precedenti per ricevere un avviso sul PRO richiedono una nuova candidatura confermata.

La pagina presenta la beta per i primi 15 studi ammessi, gratuita per sei mesi dall’attivazione e con 500 MB di allegati per studio. La candidatura non attiva il PRO e non riserva un posto.

## Prova locale su SQLite

Dalla radice della copia di lavoro, con le dipendenze di requirements.txt installate, eseguire:

```powershell
python manage.py test demo --settings=gestionale.settings_demo
python manage.py migrate --settings=gestionale.settings_demo
python manage.py collectstatic --noinput --settings=gestionale.settings_demo
python manage.py runserver localhost:8000 --settings=gestionale.settings_demo
```

Aprire http://localhost:8000. Per provare la lista d’attesa usare un indirizzo fittizio e aprire i link stampati nella console. L’email locale non viene spedita. Fuori da Render o dalla modalità pubblica, il modulo di impostazioni usa solo il suo SQLite locale.

## Pubblicazione su Render

Creare un Web Service dedicato. Collegarlo al ramo che contiene questa modifica e usare un hostname dedicato. Il database deve essere un progetto Neon separato, creato vuoto, con credenziali proprie e senza copie dei dati degli studi. Scegliere una regione UE disponibile per applicazione e database.

Impostare sul solo servizio demo:

- `DEMO_SITE_URL` con l’origine HTTPS effettiva, senza percorso.
- `DEMO_SECRET_KEY` con un segreto casuale di almeno 50 caratteri.
- `DEMO_DATABASE_URL` con la connessione del database della demo.
- `DEMO_RESEND_API_KEY` con una chiave di solo invio.
- `DEMO_FROM_EMAIL` con un mittente verificato in Resend.

Configurare un solo processo Gunicorn per mantenere il limite locale degli invii condiviso tra i thread. Comando di build:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput --settings=gestionale.settings_demo && python manage.py migrate --settings=gestionale.settings_demo
```

Comando di avvio:

```bash
gunicorn gestionale.wsgi_demo:application --workers 1 --threads 4
```

Configurare un’esecuzione giornaliera sul database demo con un pianificatore fidato. Il comando elimina i record scaduti e mostra il totale attivo, senza stampare indirizzi. Su Render usare le variabili della demo anche nel servizio cron.

```bash
python manage.py pulisci_lista_pro --settings=gestionale.settings_demo
```

## Verifiche prima di diffondere il link

- Verificare con il commercialista l’inquadramento della fase gratuita e l’indicazione della partita IVA già in uso. Verificare che nome, recapito e indirizzo nei testi siano corretti.
- Confermare i contratti sul trattamento dei dati (DPA) di Render, Neon e Resend, le regioni effettive, gli eventuali trasferimenti, i tempi dei log e delle copie e il modo di gestire cancellazioni e ripristini. Aggiornare l’informativa se la configurazione effettiva differisce. Annotare queste scelte e il bilanciamento per i log di sicurezza.
- Disabilitare il tracciamento di aperture e clic nelle impostazioni del dominio mittente Resend. Evitare di registrare gli URL completi dei link di conferma e ritiro in log applicativi. Verificare i log effettivi del provider e la loro conservazione.
- Provare da browser pulito home, simulazione, collegamenti legali, cookie, richiesta, conferma e ritiro. Verificare la consegna reale con una casella autorizzata, il funzionamento da due connessioni distinte e che il pianificatore abbia eseguito la pulizia. Controllare che gli URL del gestionale restituiscano 404 sul dominio demo.
- Pubblicizzare il link solo dopo il collaudo. L’ammissione alla beta è una fase successiva. Per comunicare l’esito usare solo candidature confermate ancora attive, includere il link di ritiro e chiudere la raccolta quando non serve più. Definire adempimenti, prezzo e condizioni prima di aprire ordini o pagamenti.

## Attivazione degli studi ammessi

La migrazione `studi.0005_betastudio` riguarda solo il gestionale. Applicarla prima in collaudo su un database separato con dati fittizi. L’amministratore della piattaforma può selezionare gli studi Free ammessi nell’elenco **Studi** del pannello admin e scegliere **Attiva la beta PRO per gli studi selezionati**. Lo studio deve essere attivo, avere un titolare con email e non avere un abbonamento o un checkout Stripe in corso. Verificare l’identità dello studio e la corrispondenza con la candidatura confermata prima di attivarlo.

L’assegnazione è registrata per studio. I sei mesi decorrono dall’attivazione e la data di fine è il primo giorno di sola lettura. Dopo 30 giorni termina l’accesso alle aree operative. Durante quei 30 giorni il titolare trova il download ZIP in **Abbonamento**. L’archivio contiene dati operativi e allegati del suo studio. Per file grandi, verificare tempi di preparazione, spazio temporaneo e download in collaudo. Dopo la chiusura, la cancellazione dei dati e delle copie segue le condizioni concordate con lo studio e la procedura del gestore.

Impostare `BETA_PRO_CONDIZIONI_USCITA` con il prezzo e le condizioni effettive, quando definiti. Pianificare l’esecuzione giornaliera di questo comando con le impostazioni del gestionale e il mittente autorizzato:

```bash
python manage.py avvisa_scadenza_beta
```

Provare prima l’avviso, il passaggio in sola lettura e il download su uno studio fittizio. L’eventuale acquisto del PRO richiede un’adesione separata e dipende dal canale di vendita scelto. Prima di ospitare dati reali, confermare l’inquadramento con il commercialista, predisporre l’accordo sul trattamento dei dati con gli studi e definire la conservazione dopo la chiusura.

Fonti di riferimento

- [GDPR, in particolare artt. 5, 6, 7, 13 e 28](https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32016R0679)
- [Garante, linee guida cookie](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9677876)
- [Garante, Codice privacy e art. 130](https://www.garanteprivacy.it/documents/10160/0/Codice%20in%20materia%20di%20protezione%20dei%20dati%20personali%20%28Testo%20coordinato%29)
- [DPA Render](https://render.com/dpa), [GDPR Neon](https://neon.com/blog/gdpr-compliance-and-neon), [GDPR Resend](https://resend.com/security/gdpr/)
