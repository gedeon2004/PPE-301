from django import forms
from .models import Categorie, Produit, Vente, ArticleVendu
from django.contrib.auth.models import User


from django.contrib.auth.models import User

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model, authenticate

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User



class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")
    telephone = forms.CharField(max_length=15, required=True, label="Numéro de téléphone")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'telephone', 'username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data



class CustomLoginForm(forms.Form):
    login = forms.CharField(
        label="Nom d'utilisateur ou Email",
        max_length=255,
        widget=forms.TextInput(attrs={
            'id': 'id_login',
            'autofocus': True,
            'required': True,
            'placeholder': 'Nom d\'utilisateur ou email'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'id': 'id_password',
            'required': True,
            'placeholder': 'Mot de passe'
        })
    )
    remember_me = forms.BooleanField(
        label="Se souvenir de moi",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        login_input = cleaned_data.get('login')
        password = cleaned_data.get('password')

        if not login_input or not password:
            return cleaned_data  # Les erreurs de champ requis seront gérées automatiquement

        # Essayer d'abord avec le nom d'utilisateur
        user = authenticate(request=self.request, username=login_input, password=password)

        # Si échec, essayer avec l'email
        if user is None:
            try:
                user_obj = User.objects.get(email__iexact=login_input)
                user = authenticate(
                    request=self.request,
                    username=user_obj.username,
                    password=password
                )
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass

        if user is None:
            raise ValidationError("Identifiants incorrects. Veuillez réessayer.")
        
        if not user.is_active:
            raise ValidationError("Ce compte est désactivé.")

        cleaned_data['user'] = user
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
