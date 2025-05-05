from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from .models import Categorie, Produit, Vente, ArticleVendu, Order, Notification, Avis
from .forms import ProduitForm, CategorieForm, VenteForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import authenticate
from .forms import SignupForm
from .models import Commande
from .models import Panier 
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserProfile 
from .models import Panier, PanierProduit
from django.contrib import messages
from django.http import JsonResponse
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q
from datetime import timedelta
from django.utils import timezone
from django.http import Http404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django.db.models import Sum
import stripe




stripe.api_key = settings.STRIPE_SECRET_KEY


def buy_now(request, product_id):
    stripe.api_key = 'sk_test_51RDmi8QoYqHOvimMbYF6M8UcNkUp7nJGKHk1YzI1PClBf9WuPcXlKATOVmrjVB0cB2pbLetF1q5LFsaZMezjHJzk00gJ0VQtk7'
    product = get_object_or_404(Produit, id=product_id)

    # Gestion des données initiales (pour pré-remplissage)
    initial_data = {
        'nom': request.user.last_name if request.user.is_authenticated else '',
        'prenom': request.user.first_name if request.user.is_authenticated else '',
        'email': request.user.email if request.user.is_authenticated else '',
    }

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            nom = request.POST.get('nom', '').strip()
            prenom = request.POST.get('prenom', '').strip()
            telephone = request.POST.get('telephone', '').strip()
            email = request.POST.get('email', '').strip()

            # Validation minimale des champs
            if not all([nom, prenom, telephone, email]):
                messages.error(request, "Veuillez remplir tous les champs obligatoires")
                return render(request, 'boutique/checkout.html', {
                    'product': product,
                    'initial_data': request.POST  # Réafficher les données saisies
                })

            # Création de la commande
            order = Order.objects.create(
                client=request.user if request.user.is_authenticated else None,
                client_nom=nom,
                client_prenom=prenom,
                client_telephone=telephone,
                client_adresse=request.POST.get('adresse', ''),
                client_email=email,
                produit=product,
                vendeur=product.vendeur,
                quantite=quantity,
                total=product.prix * quantity,
                status='pending'
            )

            # Notification au vendeur
            Notification.objects.create(
                user=product.vendeur,
                message=f"Nouvelle commande pour {product.nom}",
                order=order
            )

            # Paiement Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'xof',
                        'product_data': {
                            'name': product.nom,
                        },
                        'unit_amount': int(product.prix * 100),
                    },
                    'quantity': quantity,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(f'/order/success/{order.id}/'),
                cancel_url=request.build_absolute_uri(f'/order/cancel/{order.id}/'),
                metadata={
                    "order_id": order.id,
                    "client_email": email
                }
            )
            return redirect(checkout_session.url)

        except ValueError:
            messages.error(request, "Quantité invalide")
        except stripe.error.StripeError as e:
            order.delete()
            messages.error(request, f"Erreur de paiement: {str(e)}")
        except Exception as e:
            if 'order' in locals():
                order.delete()
            messages.error(request, f"Une erreur est survenue: {str(e)}")
            return redirect('product_detail', product_id=product.id)

    return render(request, 'boutique/checkout.html', {
        'product': product,
        'initial_data': initial_data
    })
    
    
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'processing'
    order.save()
    
    # Mettre à jour la notification
    Notification.objects.filter(order=order).update(message=f"Paiement reçu pour {order.produit.nom}")
    
    return render(request, 'boutique/payment_success.html', {'order': order})

def payment_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'cancelled'
    order.save()
    
    return render(request, 'boutique/payment_cancel.html', {'order': order})



@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.metadata.get('order_id')
        
        if order_id:
            order = Order.objects.get(id=order_id)
            order.status = 'processing'
            order.transaction_id = session.payment_intent
            order.save()
            
            # Mettre à jour le stock
            order.produit.quantite_en_stock -= order.quantite
            order.produit.save()
            
            # Mettre à jour la notification
            Notification.objects.create(
                user=order.vendeur,
                message=f"Paiement confirmé pour la commande #{order.id}",
                order=order
            )

    return HttpResponse(status=200)



@login_required
def profile_view(request):
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            user_profile = request.user.profile  
            user_profile.profile_picture = request.FILES['profile_picture']
            user_profile.save()
            return JsonResponse({'success': True})
    
    return render(request, 'registration/hisprofile.html')  


# Ajouter un nouveau produit
@login_required
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        print("Formulaire soumis !")
        if form.is_valid():
            produit = form.save(commit=False)  # Ne pas encore sauvegarder dans la DB
            produit.vendeur = request.user  # Assignez le vendeur
            produit.save()  # Maintenant, sauvegardez dans la DB
            messages.success(request, 'Le produit a été ajouté avec succès.')
            return redirect('gestion_produits')
        
    else:
        form = ProduitForm()
        
    return render(request, 'boutique/ajouter_produit.html', {'form': form})


def profile(request):
    
    return render(request, 'registration/accueil.html')  # Renvoyer le template de l'accueil

def accueil(request):
    return render(request, 'registration/accueil.html')  # Renvoyer le template de l'accueil

def hisprofile(request):
    return render(request, 'registration/hisprofile.html')  


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Chiffrer le mot de passe
            user.save()
            return redirect('login')  # Rediriger vers la page de connexion
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def check_user_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Vérifier si le mot de passe correspond à l'utilisateur connecté
        user = authenticate(username=request.user.username, password=password)
        
        if user is not None:
            # Si le mot de passe est correct
            return JsonResponse({'status': 'success', 'message': 'Mot de passe correct.'})
        else:
            # Si le mot de passe est incorrect
            return JsonResponse({'status': 'error', 'message': 'Mot de passe incorrect.'})
    
    return render(request, 'check_password.html')




def index(request):
    # Tous les produits (pour le premier carrousel)
    produits = Produit.objects.filter(est_supprime=False)[:12]  # Limité à 12 produits
    
    # Produits par catégorie
    vetements = Produit.objects.filter(categorie__nom__iexact='Vêtements', est_supprime=False)[:9]
    chaussures = Produit.objects.filter(categorie__nom__iexact='Chaussures', est_supprime=False)[:9]
    electronique = Produit.objects.filter(categorie__nom__iexact='Electronique', est_supprime=False)[:9]
    accessoires = Produit.objects.filter(categorie__nom__iexact='Accessoires', est_supprime=False)[:9]
    maison = Produit.objects.filter(categorie__nom__iexact='Maison', est_supprime=False)[:9]

    context = {
        'produits': produits,
        'vetements': vetements,
        'chaussures': chaussures,
        'electronique': electronique,
        'accessoires': accessoires,
        'maison': maison,
    }
    return render(request, 'theme1/index.html', context)


#def electronic (request):
    #return render (request, 'theme1/electronic.html')

#def fashion (request):
    #return render (request, 'theme1/fashion.html')

#def jewellery (request):
    #return render (request, 'theme1/jewellery.html' )


# Liste des produits du vendeur connecté
@login_required
def liste_produits(request):
    produits = Produit.objects.all()  # Récupérer tous les produits
    return render(request, 'store/liste_produits.html', {'produits': produits})
    produits = Produit.objects.filter(vendeur=request.user)  # Filtrer par vendeur
    return render(request, 'store/liste_produits.html', {'produits': produits})


# Modifier un produit existant
@login_required
def modifier_produit(request, pk):  
    # Récupère le produit uniquement s'il appartient à l'utilisateur connecté
    produit = get_object_or_404(Produit, pk=pk, vendeur=request.user)
    
    if request.method == "POST":
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.vendeur = request.user
            produit.save()
            messages.success(request, "Le produit a été mis à jour avec succès.")
            return redirect("gestion_produits")
    else:
        form = ProduitForm(instance=produit)

    context = {
        "form": form,
        "produit": produit,
        "title": f"Modifier {produit.nom}"
    }
    
    return render(request, "boutique/modifier_produit.html", context)

# Supprimer un produit
@login_required
def supprimer_produit(request, pk):
    try:
        produit = Produit.objects.get(pk=pk, vendeur=request.user)
    except Produit.DoesNotExist:
        raise Http404("Produit non trouvé ou vous n'avez pas la permission")
    
    if request.method == 'POST':
        produit.delete()
        messages.success(request, 'Produit déplacé dans la corbeille avec succès.')
        return redirect('gestion_produits')
    
    return render(request, 'boutique/confirmation_suppression.html', {'produit': produit})

@login_required
def confirmation_suppression(request, produit_id):
    # Récupère le produit uniquement s'il appartient à l'utilisateur connecté
    produit = get_object_or_404(Produit, id=produit_id, vendeur=request.user)
    
    if request.method == 'POST':
        # Si confirmation reçue, supprime le produit
        produit.delete()
        messages.success(request, f'Le produit "{produit.nom}" a été supprimé avec succès.')
        return redirect('gestion_produits')
    
    context = {
        'produit': produit,
        'title': f'Supprimer {produit.nom}'
    }
    return render(request, 'boutique/confirmation_suppression.html', context)

# Afficher la corbeille des produits
@login_required
def corbeille_produits(request):
    produits_supprimes = Produit.objects.filter(vendeur=request.user, est_supprime=True)
    return render(request, 'boutique/corbeille_produits.html', {'produits': produits_supprimes})

# Restaurer un produit supprimé
@login_required
def restaurer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk, vendeur=request.user, est_supprime=True)

    if request.method == 'POST':
        produit.est_supprime = False  # Marquer comme non supprimé
        produit.save()
        messages.success(request, 'Produit restauré avec succès.')
        return redirect('gestion_produits')  # Redirige vers la page de gestion des produits

    return render(request, 'boutique/confirmation_restoration.html', {'produit': produit})

# Supprimer définitivement un produit
@login_required
def supprimer_definitivement(request, pk):
    produit = get_object_or_404(Produit, pk=pk, vendeur=request.user, est_supprime=True)

    if request.method == 'POST':
        produit.delete()  # Supprimer le produit définitivement
        messages.success(request, 'Produit supprimé définitivement.')
        return redirect('corbeille_produits')  # Redirige vers la corbeille

    return render(request, 'boutique/confirmation_suppression_definitive.html', {'produit': produit})

# Enregistrer une vente
@login_required
def enregistrer_vente(request):
    if request.method == 'POST':
        form = VenteForm(request.POST)
        if form.is_valid():
            vente = form.save()
            return redirect('liste_ventes')
    else:
        form = VenteForm()
    return render(request, 'store/enregistrer_vente.html', {'form': form})

# Liste des ventes
@login_required
def liste_ventes(request):
    ventes = Vente.objects.all()  # Liste toutes les ventes
    return render(request, 'store/liste_ventes.html', {'ventes': ventes})

# Tableau de bord du vendeur (produits du vendeur connecté)
@login_required
def dashboard(request):
    # Récupère tous les produits du vendeur connecté
    produits = Produit.objects.filter(vendeur=request.user)
    
    # Commandes
    commandes = Commande.objects.filter(vendeur=request.user)
    
    # Statistiques principales
    total_produits = produits.count()
    commandes_du_mois = commandes.filter(
        date_commande__month=timezone.now().month,
        date_commande__year=timezone.now().year
    )
    
    # Calcul des revenus
    revenus_mois = commandes_du_mois.aggregate(total=Sum('montant_total'))['total'] or 0
    revenus_total = commandes.aggregate(total=Sum('montant_total'))['total'] or 0
    
    # Commandes par statut
    commandes_en_attente = commandes.filter(statut='en_attente').count()
    commandes_en_cours = commandes.filter(statut='en_cours').count()
    commandes_terminees = commandes.filter(statut='terminee').count()
    
    # Produits en rupture de stock
    produits_rupture = produits.filter(quantite_en_stock__lte=5)
    
    # Commandes récentes (7 derniers jours)
    date_limite = timezone.now() - timedelta(days=7)
    commandes_recentes = commandes.filter(
        date_commande__gte=date_limite
    ).order_by('-date_commande')[:5]
    
    # Avis récents
    avis_recents = Avis.objects.filter(
        produit__vendeur=request.user
    ).order_by('-date_creation')[:3]
    
    # Notifications non lues
    notifications_non_lues = Notification.objects.filter(
        user=request.user,
        lue=False
    ).order_by('-created_at')[:5]
    
    # Données pour les graphiques
    # Ventes des 30 derniers jours
    ventes_30j = []
    dates_30j = []
    for i in range(30, -1, -1):
        date = timezone.now() - timedelta(days=i)
        total_jour = commandes.filter(
            date_commande__date=date,
            statut='terminee'
        ).aggregate(total=Sum('montant_total'))['total'] or 0
        ventes_30j.append(float(total_jour))
        dates_30j.append(date.strftime('%d/%m'))
    
    # Catégories les plus vendues
    categories_vendues = produits.annotate(
        total_vendu=Sum('panierproduit__quantite')  
    ).order_by('-total_vendu')[:5]

    # Récupérer les noms de catégories et les totaux vendus
    categories_labels = [cat.categorie.nom for cat in categories_vendues if cat.categorie]
    categories_data = [cat.total_vendu or 0 for cat in categories_vendues]

    # Récupérer les stats avec cache
    stats = cache.get(f'stats_ventes_{request.user.id}')
    
    if not stats:
        stats = {
            'ventes_mois': Commande.objects.filter(
                statut='paye',
                date_paiement__month=timezone.now().month
            ).aggregate(total=Sum('montant_total'))['total'] or 0
        }
        cache.set(f'stats_ventes_{request.user.id}', stats, 60*15)  # Cache 15 minutes

    # Mettre à jour les revenus du mois avec les données en cache
    revenus_mois = stats['ventes_mois']

    context = {
        # Produits
        'produits': produits,
        'total_produits': total_produits,
        'produits_rupture': produits_rupture,
        
        # Commandes
        'commandes': commandes,
        'commandes_recentes': commandes_recentes,
        'commandes_en_attente': commandes_en_attente,
        'commandes_en_cours': commandes_en_cours,
        'commandes_terminees': commandes_terminees,
        
        # Finances
        'revenus_mois': revenus_mois,
        'revenus_total': revenus_total,
        
        # Avis
        'avis_recents': avis_recents,
        
        # Notifications
        'notifications_non_lues': notifications_non_lues,
        'nombre_notifications': notifications_non_lues.count(),
        
        # Données graphiques
        'ventes_30j': ventes_30j,
        'dates_30j': dates_30j,
        'categories_vendues': categories_vendues,
        
        'categories_labels': categories_labels,
        'categories_data': categories_data,
    }
    
    return render(request, 'boutique/dashboard.html', context)
 
#dashboard admin   
def index2 (request):
    return render(request, 'theme2/index.html')  # Page d'administration

def components_alerts(request):
    return render(request, 'theme2/components-alerts.html')

# Pages des clients
@login_required
def client(request):
    produits = Produit.objects.all()  # Récupérer tous les produits
    return render(request, 'boutique/client.html', {'produits': produits})




    # Construire les URLs pour chaque commande
    commandes_with_urls = [
        (commande, reverse('client_order', kwargs={'commande_id': commande.id}))
        for commande in commandes
    ]
    
    # Passer les commandes avec leurs URLs au template
    return render(request, 'boutique/dashboard.html', {'commandes_with_urls': commandes_with_urls})


# Page de gestion des produits du vendeur connecté
@login_required
def gestion_produits(request):
    produits = Produit.objects.filter(vendeur=request.user)  # Récupérer tous les produits que l'utilisateur a publié
    categories = Categorie.objects.all()
    context = {
        'produits': produits,
        'categories': categories
    }
    return render(request, 'boutique/gestion_produits.html', context)

# Vérifier le mot de passe d'un utilisateur
def check_user_password(request):
    # Récupérer le nom d'utilisateur et le mot de passe depuis le formulaire
    username = request.POST.get('username')  
    password = request.POST.get('password')

    user = User.objects.filter(username=username).first()
    
    if user:
        # Vérifier si le mot de passe correspond
        if check_password(password, user.password):
            return HttpResponse("Mot de passe correct")
        else:
            return HttpResponse("Mot de passe incorrect")
    else:
        return HttpResponse("Utilisateur non trouvé")
    



def client_order_view(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
   
    return render(request, 'client_order.html', {'commande': commande})

    # Extraire les infos du client depuis la commande
    client_info = {
        'nom': commande.nom_client if hasattr(commande, 'nom_client') else 'Inconnu',
        'email': commande.email_client if hasattr(commande, 'email_client') else 'Non fourni',
        'telephone': commande.telephone_client if hasattr(commande, 'telephone_client') else 'Non fourni'
    }

    return render(request, 'boutique/client_order.html', {'commande': commande, 'client': client_info})

#Voir les détails d'un produit sur le l'interface d'un vendeur
def produit_detail(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)  
    return render(request, 'boutique/produit_detail.html', {'produit': produit})



#Voir les détails d'un produit sur le l'interface d'un client
def produit_detail_clients(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    return render(request, 'boutique/voir_detail.html', {'produit': produit})





def ajouter_panier(request, id):
    produit = Produit.objects.get(id=id)
    panier, created = Panier.objects.get_or_create(user=request.user)
    panier.produits.add(produit)  # Assuming the Panier model has a ManyToMany relation with Produit
    return redirect('panier')  # Redirect to the panier page



def client_order_view(request, commande_id):
    # Code pour traiter la commande
    return render(request, 'boutique/client_order.html', {'commande_id': commande_id})

from .models import UserProfile  

@login_required
def profile_view(request):
    user_profile = request.user.profile
    
    if request.method == 'POST':
        # Mettre à jour la photo de profil si fournie
        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']
        
        # Mettre à jour les autres informations
        user_profile.full_name = request.POST.get('full_name')
        user_profile.phone = request.POST.get('phone')
        user_profile.address = request.POST.get('address')

        # Mettre à jour le mot de passe si fourni
        password = request.POST.get('password')
        if password:
            user_profile.user.set_password(password)

        user_profile.save()
        return JsonResponse({'success': True})

    return render(request, 'hisprofile.html') 



def afficher_panier(request):
    panier, created = Panier.objects.get_or_create(user=request.user)
    items = panier.panierproduit_set.all()  # Récupérer tous les produits dans le panier
    total = sum(item.produit.prix * item.quantite for item in items)  # Calculer le total ici
    return render(request, 'boutique/panier.html', {'panier': panier, 'items': items, 'total': total})

def ajouter_au_panier(request, produit_id):
    """Ajoute un produit au panier."""
    produit = get_object_or_404(Produit, id=produit_id)
    panier, created = Panier.objects.get_or_create(user=request.user)
    
    # Vérifie si le produit est déjà dans le panier
    panier_produit, created = PanierProduit.objects.get_or_create(panier=panier, produit=produit)

    if not created:
        # Si le produit existe déjà, on augmente la quantité
        panier_produit.quantite += 1
    else:
        # Si c'est un nouvel ajout, on définit la quantité à 1
        panier_produit.quantite = 1
    
    panier_produit.save()  # Sauvegarde les modifications
    return redirect('panier')  # Redirige vers la page du panier



def retirer_du_panier(request, produit_id):
    """Retire un produit du panier."""
    panier = get_object_or_404(Panier, user=request.user)
    panier_produit = get_object_or_404(PanierProduit, panier=panier, produit_id=produit_id)
    
    # Supprime le produit du panier
    panier_produit.delete()
    return redirect('panier')  # Redirige vers la page du panier


def recherche_produits(request):
    produits = Produit.objects.all()
    categories = Categorie.objects.all()
    
    query = request.GET.get('q')
    category_filter = request.GET.get('categorie')

    if query:
        produits = produits.filter(nom__icontains=query)
    if category_filter:
        produits = produits.filter(categorie__nom=category_filter)

    panier_count = 0
    if request.user.is_authenticated:
        try:
            panier = Panier.objects.get(user=request.user)
            panier_count = panier.panierproduit_set.count()
        except Panier.DoesNotExist:
            panier_count = 0

    return render(request, 'boutique/client.html', {
        'produits': produits,
        'categories': categories,
        'panier_count': panier_count,
    })
    
    
@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    def post(self, request):
        # Traiter la notification de paiement
        commande_id = request.POST.get('commande_id')
        montant = request.POST.get('montant')
        
        try:
            commande = Commande.objects.get(id=commande_id)
            commande.marquer_comme_payee()
            
            return JsonResponse({'status': 'success'})
        except Commande.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Commande non trouvée'}, status=404)
        

def sales_stats(request):
    # Utilisation du cache pour optimiser
    stats = cache.get('stats_ventes_mois')
    
    if not stats:
        from django.db.models import Sum
        from datetime import datetime
        
        mois_courant = datetime.now().month
        stats = {
            'monthly_sales': Commande.objects.filter(
                statut_paiement='paye',
                date_paiement__month=mois_courant
            ).aggregate(total=Sum('montant_total'))['total'] or 0
        }
        cache.set('stats_ventes_mois', stats, 60*15)  # Cache pendant 15 min
    
    return JsonResponse(stats)

@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        try:
            commande_id = request.POST.get('commande_id')
            commande = Commande.objects.get(id=commande_id)
            commande.marquer_comme_payee()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)