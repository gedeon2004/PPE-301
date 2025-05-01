from django import forms
from .models import Categorie, Produit, Vente, ArticleVendu
from django.contrib.auth.models import User

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description']

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'description', 'prix', 'quantite_en_stock', 'categorie', 'image']

    def clean_quantite_en_stock(self):
        quantite = self.cleaned_data.get('quantite_en_stock')
        if quantite is None or quantite < 0:
            raise forms.ValidationError("La quantité en stock ne peut pas être vide ou négative.")
        return quantite

class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = ['total'] 
        
class ArticleVenduForm(forms.ModelForm):
    class Meta:
        model = ArticleVendu
        fields = ['vente', 'produit', 'quantite', 'sous_total']
