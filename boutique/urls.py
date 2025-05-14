from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import ajouter_produit, gestion_produits
from .views import client_order_view
from .utils import generate_pdf
from django.conf.urls.static import static
from django.conf import settings
from .views import modifier_produit 
from .views import produit_detail_clients
from .views import afficher_panier, ajouter_au_panier, retirer_du_panier
from .views import recherche_produits
from .views import components_alerts
from .views import modifier_produit, supprimer_produit
from .views import confirmation_suppression 
from .views import modifier_produit, supprimer_produit, restaurer_produit, supprimer_definitivement, corbeille_produits
from django.urls import path
#from .views import CustomLoginView, CustomPasswordResetView, CustomPasswordResetConfirmView

urlpatterns = [
    # Routes liées à l'admin
    path('admin/', admin.site.urls),

    # Routes liées à la gestion des produits
    
    
    path ('', views.index, name='index'),
    
   
    
    
    
    #path('', views.liste_produits, name='liste_produits'),
    path('ajouter_produit/', views.ajouter_produit, name='ajouter_produit'),
    path('produits/ajouter/', ajouter_produit, name='ajouter_produit'),
    path('produits/gestion/', gestion_produits, name='gestion_produits'),
    path('produits/<int:produit_id>/', views.produit_detail, name='produit_detail'),
    path('produit/<int:produit_id>/', produit_detail_clients, name='produit_detail_clients'),
    path('electronics/', views.liste_electronique, name='liste_electronique'),
    path('vetements/', views.liste_vetements, name='liste_vetements'),
    path('chaussures/', views.liste_chaussures, name='liste_chaussures'),
    path('sacs & maroquineries/', views.liste_sacs, name='liste_sacs'),
    
    
    
    # Modifier et supprimer produits
    path('produit/<int:pk>/modifier/', modifier_produit, name='modifier_produit'),
    path('produit/<int:pk>/supprimer/', supprimer_produit, name='supprimer_produit'),
    path('produits/corbeille/', corbeille_produits, name='corbeille_produits'),
    path('produit/<int:produit_id>/supprimer/', confirmation_suppression, name='confirmation_suppression'),
    path('produit/<int:pk>/restaurer/', restaurer_produit, name='restaurer_produit'),
    path('produit/<int:pk>/supprimer-definitivement/', supprimer_definitivement, name='supprimer_definitivement'),

    # Routes liées aux ventes
    path('ventes/', views.liste_ventes, name='liste_ventes'),
    path('vente/enregistrer/', views.enregistrer_vente, name='enregistrer_vente'),

    # Routes liées au dashboard et à la gestion des produits
    path('dashboard/', views.dashboard, name='dashboard'),
    path ('dashboard/index', views.index2, name='admin'),
    
    path('dashboard/components-alerts/', views.components_alerts, name='components_alerts'),
    path('produits/', views.liste_produits, name='liste_produits'),
    path('produits/gestion/', views.gestion_produits, name='gestion_produits'),
    
    #Routes liées aux clients
    path('client/', views.client, name='client'),
    

    # Authentification
    
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/accueil/', views.accueil, name='accueil'),  # URL de la page d'accueil
    path ('accounts/hisprofile/', views.hisprofile, name='hisprofile'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),  # URL de déconnexion
    
    # Réinitialisation de mot de passe (optionnel)
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Vérification du mot de passe
    path('check-password/', views.check_user_password, name='check_user_password'),
    
    path('signup/', views.signup, name='signup'),  # URL pour accéder à la page d'inscription
    
    
     
     
    path('produit/<int:id>/', views.produit_detail, name='produit_detail'),  # URL pour accéder à la page de détail d'un produit (connexion vendeur)
    path('produit/<int:id>/ajouter/', views.ajouter_panier, name='ajouter_panier'),  # URL pour ajouter un produit au panier
    path('recu/<int:commande_id>/', client_order_view, name='client_order'),
    path('recu/<int:commande_id>/pdf/', generate_pdf, name='generate_pdf'),
    
    path('panier/', afficher_panier, name='panier'),
    path('panier/ajouter/<int:produit_id>/', ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/retirer/<int:produit_id>/', retirer_du_panier, name='retirer_du_panier'),
    
    path('recherche/', recherche_produits, name='recherche_produits'),
    
    path('buy/<int:product_id>/', views.buy_now, name='buy_now'),
    path('order/success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('order/cancel/<int:order_id>/', views.payment_cancel, name='payment_cancel'),

    path('api/payment-webhook/', views.PaymentWebhookView.as_view(), name='payment_webhook'),  
    path('api/payment-webhook/', views.payment_webhook, name='payment_webhook'), 
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
