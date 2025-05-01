from django.contrib import admin
from .models import Categorie, Produit, Vente, ArticleVendu,  Client



admin.site.register(Categorie)
admin.site.register(Produit)
admin.site.register(Vente)
admin.site.register(ArticleVendu)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'date_joined', 'last_updated')
    search_fields = ('full_name', 'email')

# Register your models here.
