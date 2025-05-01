# boutique/utils.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse
from functools import wraps
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Produit, Categorie

# Decorators
def user_owns_product(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est propriétaire du produit
    """
    @wraps(view_func)
    def _wrapped_view(request, produit_id, *args, **kwargs):
        produit = get_object_or_404(Produit, id=produit_id)
        if produit.utilisateur != request.user:
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce produit")
        return view_func(request, produit_id, *args, **kwargs)
    return _wrapped_view

def user_owns_category(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est propriétaire de la catégorie
    """
    @wraps(view_func)
    def _wrapped_view(request, categorie_id, *args, **kwargs):
        categorie = get_object_or_404(Categorie, id=categorie_id)
        if categorie.utilisateur != request.user:
            raise PermissionDenied("Vous n'avez pas la permission de modifier cette catégorie")
        return view_func(request, categorie_id, *args, **kwargs)
    return _wrapped_view

def staff_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est membre du staff
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Accès réservé aux administrateurs")
            return redirect('accueil')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Utility functions
def check_product_owner(produit_id, user):
    """
    Vérifie si l'utilisateur est propriétaire du produit
    Retourne le produit si ok, sinon lève une exception
    """
    produit = get_object_or_404(Produit, id=produit_id)
    if produit.utilisateur != user:
        raise PermissionDenied
    return produit

def check_category_owner(categorie_id, user):
    """
    Vérifie si l'utilisateur est propriétaire de la catégorie
    """
    categorie = get_object_or_404(Categorie, id=categorie_id)
    if categorie.utilisateur != user:
        raise PermissionDenied
    return categorie

def filter_user_products(queryset, user):
    """
    Filtre un queryset de produits pour ne retourner que ceux de l'utilisateur
    """
    return queryset.filter(utilisateur=user)

def filter_user_categories(queryset, user):
    """
    Filtre un queryset de catégories pour ne retourner que celles de l'utilisateur
    """
    return queryset.filter(utilisateur=user)

# Form utilities
def add_user_to_form(form, user):
    """
    Ajoute l'utilisateur aux données du formulaire avant sauvegarde
    """
    instance = form.save(commit=False)
    instance.utilisateur = user
    instance.save()
    return instance

# Image handling
def validate_image_size(image, max_size=2):
    """
    Valide que l'image ne dépasse pas la taille maximale (en MB)
    """
    if image.size > max_size * 1024 * 1024:
        raise ValidationError(f"La taille de l'image ne doit pas dépasser {max_size}MB")

# Pagination
def paginate_queryset(request, queryset, items_per_page=10):
    """
    Utilitaire de pagination standard
    """
    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

# Permissions
class UserOwnsProductMixin:
    """
    Mixin pour les vues basées sur les classes qui vérifie la propriété du produit
    """
    def dispatch(self, request, *args, **kwargs):
        self.produit = get_object_or_404(Produit, id=kwargs['produit_id'])
        if self.produit.utilisateur != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class UserOwnsCategoryMixin:
    """
    Mixin pour les vues basées sur les classes qui vérifie la propriété de la catégorie
    """
    def dispatch(self, request, *args, **kwargs):
        self.categorie = get_object_or_404(Categorie, id=kwargs['categorie_id'])
        if self.categorie.utilisateur != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

def generate_pdf(data):
    """
    Generates a PDF with the provided data and returns it as an HTTP response.
    """
    # Create a bytes buffer for storing the PDF
    buffer = BytesIO()

    # Create a PDF canvas
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add content to the PDF (this is just an example)
    c.drawString(100, height - 100, "Generated PDF Example")
    c.drawString(100, height - 120, f"Data: {data}")

    # Save the PDF
    c.showPage()
    c.save()

    # Get the PDF from the buffer
    buffer.seek(0)

    # Return the PDF as an HTTP response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="generated_pdf.pdf"'
    return response
    