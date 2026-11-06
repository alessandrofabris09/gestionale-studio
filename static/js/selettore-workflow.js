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
            const selezione = elenco.value;
            const parole = normalizza(ricerca.value.trim()).split(/\s+/);
            const filtrate = opzioni.filter((opzione) => opzione.value
                && (!categoria || opzione.dataset.categoria === categoria)
                && parole.every((parola) => normalizza(opzione.textContent).includes(parola)));
            const visibili = new Set(filtrate);
            elenco.replaceChildren(...opzioni.filter((opzione) => !opzione.value
                || opzione.value === selezione || visibili.has(opzione)));
            elenco.value = selezione;
            const corrispondenze = filtrate.length;
            risultati.textContent = corrispondenze === 0 ? 'Nessun modello corrispondente.'
                : corrispondenze === 1 ? '1 modello trovato.' : `${corrispondenze} modelli trovati.`;
        };
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
        elenco.size = 7;
        filtri.hidden = false;
        risultati.hidden = false;
        ricerca.addEventListener('input', aggiorna);
        elenco.addEventListener('change', aggiorna);
        aggiorna();
    }
})();
