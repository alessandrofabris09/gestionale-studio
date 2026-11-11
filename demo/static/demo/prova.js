'use strict';

const pratica = document.querySelector('#pratica');
const voci = Array.from(document.querySelectorAll('.voce'));
const data = document.querySelector('#scadenza');
const esempi = JSON.parse(document.querySelector('#esempi-pratiche').textContent);
const stati = Object.fromEntries(Object.entries(esempi).map(([chiave, esempio]) => [
    chiave, { voci: esempio.checklist.map(() => false), data: '' },
]));
const formatoData = new Intl.DateTimeFormat('it-IT', { dateStyle: 'long' });

function mostraRiepilogo() {
    const completate = voci.filter((voce) => voce.checked).length;
    document.querySelector('#pratica-corrente').textContent = pratica.selectedOptions[0].textContent;
    document.querySelector('#avanzamento').textContent = completate + ' di ' + voci.length + ' voci completate';
    document.querySelector('#prossima-scadenza').textContent = data.value
        ? 'Scadenza ' + formatoData.format(new Date(data.value + 'T12:00:00'))
        : 'Nessuna scadenza impostata';
}

pratica.addEventListener('change', () => {
    const stato = stati[pratica.value];
    voci.forEach((voce, indice) => {
        voce.checked = stato.voci[indice];
        voce.nextElementSibling.textContent = esempi[pratica.value].checklist[indice];
    });
    data.value = stato.data;
    mostraRiepilogo();
});
voci.forEach((voce, indice) => voce.addEventListener('change', () => {
    stati[pratica.value].voci[indice] = voce.checked;
    mostraRiepilogo();
}));
data.addEventListener('change', () => {
    stati[pratica.value].data = data.value;
    mostraRiepilogo();
});
