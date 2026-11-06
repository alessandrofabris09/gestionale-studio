const praticaForm = document.querySelector('#form-pratica');
const clientePratica = praticaForm.elements.cliente;
const immobilePratica = praticaForm.elements.immobile;
const clienteImmobile = document.querySelector('#immobile-rapido select[name="cliente"]');
const esitoCreazione = document.querySelector('#esito-creazione-rapida');

function aggiungiOpzione(select, id, label) {
    const value = String(id);
    if (!Array.from(select.options).some(option => option.value === value)) {
        select.add(new Option(label, value));
    }
}

for (const button of praticaForm.querySelectorAll('[data-apri]')) {
    const dialog = document.getElementById(button.dataset.apri);
    if (typeof dialog.showModal !== 'function') continue;
    button.parentElement.hidden = false;
    button.addEventListener('click', () => {
        if (dialog.id === 'immobile-rapido') {
            clienteImmobile.value = clientePratica.value;
        }
        dialog.showModal();
    });

    const form = dialog.querySelector('form');
    const salva = form.querySelector('[type="submit"]');
    const errori = form.querySelector('[role="alert"]');
    form.querySelector('[data-chiudi]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('cancel', event => {
        if (salva.disabled) event.preventDefault();
    });
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (salva.disabled) return;
        salva.disabled = true;
        form.querySelector('[data-chiudi]').disabled = true;
        errori.hidden = true;

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: { Accept: 'application/json' },
                body: new FormData(form),
            });
            if (!response.headers.get('Content-Type')?.includes('application/json')) {
                throw new Error('Salvataggio non riuscito. Verifica di essere ancora connesso.');
            }
            const data = await response.json();
            if (response.status !== 201) {
                const messaggi = Object.values(data.errors || {}).flat().map(error => error.message);
                throw new Error(messaggi.join(' ') || 'Salvataggio non riuscito.');
            }

            if (form.dataset.creazione === 'cliente') {
                aggiungiOpzione(clientePratica, data.id, data.label);
                if (clienteImmobile) aggiungiOpzione(clienteImmobile, data.id, data.label);
                clientePratica.value = data.id;
                immobilePratica.value = '';
                esitoCreazione.textContent = 'Cliente aggiunto e selezionato.';
            } else {
                aggiungiOpzione(clientePratica, data.cliente_id, data.cliente_label);
                aggiungiOpzione(immobilePratica, data.id, data.label);
                clientePratica.value = data.cliente_id;
                immobilePratica.value = data.id;
                esitoCreazione.textContent = 'Immobile aggiunto e selezionato.';
            }
            form.reset();
            dialog.close();
        } catch (error) {
            errori.textContent = error.message;
            errori.hidden = false;
        } finally {
            salva.disabled = false;
            form.querySelector('[data-chiudi]').disabled = false;
        }
    });
}
