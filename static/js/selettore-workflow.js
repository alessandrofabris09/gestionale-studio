(() => {
    const normalizza = (testo) => testo.toLocaleLowerCase('it')
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '');

    for (const contenitore of document.querySelectorAll('[data-selettore-workflow]')) {
        const filtri = contenitore.querySelector('.selettore-workflow-filtri');
        if (!filtri.hidden) continue;
        const elenco = contenitore.querySelector('select');
        const ricerca = contenitore.querySelector('[data-ricerca]');
        const apriCategorie = contenitore.querySelector('[data-apri-categorie]');
        const categoriaAttiva = contenitore.querySelector('[data-categoria-attiva]');
        const categorieElenco = contenitore.querySelector('[data-categorie]');
        const risultati = contenitore.querySelector('[data-risultati]');
        const modelli = contenitore.querySelector('[data-modelli]');
        const modelloScelto = contenitore.querySelector('[data-modello-scelto]');
        const opzioni = Array.from(elenco.options);
        const categorie = new Set(opzioni.map((opzione) => opzione.dataset.categoria).filter(Boolean));
        let categoria = '';

        const mostraCategorie = (aperte) => {
            categorieElenco.hidden = !aperte;
            apriCategorie.setAttribute('aria-expanded', String(aperte));
        };
        apriCategorie.addEventListener('click', () => mostraCategorie(categorieElenco.hidden));
        apriCategorie.parentElement.addEventListener('keydown', (evento) => {
            if (evento.key === 'Escape' && !categorieElenco.hidden) {
                mostraCategorie(false);
                apriCategorie.focus();
            }
        });

        const aggiorna = () => {
            const parole = normalizza(ricerca.value.trim()).split(/\s+/);
            const filtrate = opzioni.filter((opzione) => opzione.value
                && (!categoria || opzione.dataset.categoria === categoria)
                && parole.every((parola) => normalizza(opzione.textContent).includes(parola)));
            modelli.replaceChildren(...filtrate.map((opzione) => {
                const pulsante = document.createElement('button');
                pulsante.type = 'button';
                pulsante.textContent = opzione.textContent;
                pulsante.setAttribute('aria-pressed', String(opzione.selected));
                pulsante.addEventListener('click', () => {
                    elenco.value = opzione.value;
                    elenco.dispatchEvent(new Event('change', {bubbles: true}));
                    confermaModello();
                    modelloScelto.focus();
                });
                return pulsante;
            }));
            modelli.hidden = filtrate.length === 0;
            const corrispondenze = filtrate.length;
            risultati.textContent = corrispondenze === 0 ? 'Nessun modello corrispondente.'
                : corrispondenze === 1 ? '1 modello trovato.' : `${corrispondenze} modelli trovati.`;
        };
        const confermaModello = () => {
            modelli.hidden = true;
            modelloScelto.hidden = false;
            modelloScelto.textContent = `Modello selezionato: ${elenco.selectedOptions[0].textContent.trim()} · Cambia`;
            risultati.textContent = '';
        };
        modelloScelto.addEventListener('click', () => {
            aggiorna();
            ricerca.focus();
        });
        elenco.addEventListener('invalid', (evento) => {
            evento.preventDefault();
            ricerca.focus();
            risultati.textContent = 'Seleziona un modello prima di continuare.';
        });
        const nomi = ['', ...[...categorie].sort((a, b) => a.localeCompare(b, 'it'))];
        for (const nome of nomi) {
            const pulsante = document.createElement('button');
            pulsante.type = 'button';
            pulsante.textContent = nome || 'Tutte le categorie';
            pulsante.setAttribute('aria-pressed', String(nome === categoria));
            pulsante.addEventListener('click', () => {
                categoria = nome;
                categoriaAttiva.textContent = pulsante.textContent;
                categorieElenco.querySelector('[aria-pressed="true"]').setAttribute('aria-pressed', 'false');
                pulsante.setAttribute('aria-pressed', 'true');
                mostraCategorie(false);
                apriCategorie.focus();
                aggiorna();
            });
            categorieElenco.append(pulsante);
        }
        elenco.hidden = true;
        filtri.hidden = false;
        risultati.hidden = false;
        ricerca.addEventListener('input', aggiorna);
        if (elenco.value) confermaModello();
        else aggiorna();
    }
})();
