(() => {
    const normalizza = (testo) => testo.toLocaleLowerCase('it')
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '');

    for (const contenitore of document.querySelectorAll('[data-selettore-workflow]')) {
        const filtri = contenitore.querySelector('.selettore-workflow-filtri');
        if (!filtri.hidden) continue;
        const elenco = contenitore.querySelector('select:not([data-categoria])');
        const ricerca = contenitore.querySelector('[data-ricerca]');
        const categoria = contenitore.querySelector('[data-categoria]');
        const risultati = contenitore.querySelector('[data-risultati]');
        const opzioni = Array.from(elenco.options).filter((opzione) => opzione.value);
        const categorie = new Set(opzioni.map((opzione) => opzione.dataset.categoria).filter(Boolean));
        for (const nome of [...categorie].sort((a, b) => a.localeCompare(b, 'it'))) {
            categoria.add(new Option(nome, nome));
        }

        const aggiorna = () => {
            const selezione = elenco.value;
            const parole = normalizza(ricerca.value.trim()).split(/\s+/);
            let corrispondenze = 0;
            for (const opzione of opzioni) {
                const coincide = (!categoria.value || opzione.dataset.categoria === categoria.value)
                    && parole.every((parola) => normalizza(opzione.textContent).includes(parola));
                opzione.hidden = !coincide && opzione.value !== selezione;
                if (coincide) corrispondenze += 1;
            }
            risultati.textContent = corrispondenze === 0 ? 'Nessun modello corrispondente.'
                : corrispondenze === 1 ? '1 modello trovato.' : `${corrispondenze} modelli trovati.`;
        };
        elenco.size = 7;
        filtri.hidden = false;
        risultati.hidden = false;
        ricerca.addEventListener('input', aggiorna);
        categoria.addEventListener('change', aggiorna);
        elenco.addEventListener('change', aggiorna);
        aggiorna();
    }
})();
