from django import forms


class SelettoreWorkflow(forms.Select):
    template_name = 'workflow/selettore.html'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        opzione = super().create_option(name, value, label, selected, index, subindex, attrs)
        modello = getattr(value, 'instance', None)
        categoria = modello.get_categoria_display() if modello else getattr(self, 'categorie', {}).get(value)
        if categoria:
            opzione['attrs']['data-categoria'] = categoria
        return opzione
