from django.db import models
from django.contrib.auth.models import User  # Importation du modèle User
from django.utils import timezone
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import uuid


# Create your models here.

# Modèle pour les catégories de produits
class Categorie(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

# Modèle pour les produits
class Produit(models.Model):
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produits')
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantite_en_stock = models.IntegerField(default=0)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name="produits")
    image = models.ImageField(upload_to="produits/", blank=True, null=True, default='produits/default.jpg')
    date_creation = models.DateTimeField(auto_now_add=True)
    est_supprime = models.BooleanField(default=False)
    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return self.nom
    

def generate_reference():
    return f"CMD-{uuid.uuid4().hex[:6].upper()}"
   
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_commande = models.DateTimeField(auto_now_add=True)
    

    # Informations client
    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  
    client_nom = models.CharField(max_length=100, null=True, blank=True)
    client_prenom = models.CharField(max_length=100, null=True, blank=True)
    client_telephone = models.CharField(max_length=20, null=True, blank=True)
    client_adresse = models.TextField(null=True, blank=True)
    client_email = models.EmailField(null=True, blank=True)
    
    # Informations produit
    produit = models.ForeignKey('Produit', on_delete=models.CASCADE)
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_received')
    quantite = models.IntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Commande #{self.id} - {self.produit.nom}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif: {self.message[:20]}"

    

class Avis(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    # ... autres champs
    date_creation = models.DateTimeField(auto_now_add=True)
  
    
# Modèle pour les ventes
class Vente(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.SET_NULL, null=True, blank=True)
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    mode_paiement = models.CharField(max_length=50, default="Stripe")
    date_vente = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Vente de {self.montant} FCFA par {self.vendeur.username} le {self.date_vente.strftime('%d/%m/%Y')}"

# Modèle pour les articles vendus dans une vente
class ArticleVendu(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="articles")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.IntegerField()
    sous_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} (Vente {self.vente.id})"
    

class Commande(models.Model):
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En Attente'),
            ('termine', 'Terminé')
        ],  
        default='en_attente'
    )
    
    STATUT_PAIEMENT = [
        ('en_attente', 'En attente'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]
    
    statut_paiement = models.CharField(
        max_length=20,
        choices=STATUT_PAIEMENT,
        default='en_attente'
    )
    date_paiement = models.DateTimeField(null=True, blank=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2) 
    vendeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    reference = models.CharField(max_length=50, unique=True, blank=True, editable=False) 
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)  # Correction: 'upload_to' au lieu de 'uupload_to'

    def __str__(self):
        return f"Commande {self.reference}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"CMD-{uuid.uuid4().hex[:6].upper()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # Correction: 'error_correction' au lieu de 'error_correction'
                box_size=10,
                border=4,
            )
            qr.add_data(self.reference)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            filename = f"qr_code_{self.reference}.png"
            
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        super().save(*args, **kwargs)
        
    def marquer_comme_payee(self):
        self.statut_paiement = 'paye'
        self.date_paiement = timezone.now()
        self.save()
        self.mettre_a_jour_statistiques()
    
    def mettre_a_jour_statistiques(self):
        # Mettre à jour les statistiques de vente
        from django.db.models import Sum
        from datetime import date
        
        # Exemple: Mise à jour du cache des statistiques
        cache.delete('stats_ventes_mois')
    

class Panier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Relier un panier à un utilisateur
    produits = models.ManyToManyField(Produit, through='PanierProduit')  # Relier plusieurs produits au panier

    def __str__(self):
        return f"Panier de {self.user.username}"

class PanierProduit(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)  # Quantité de chaque produit dans le panier
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} dans le panier de {self.panier.user.username}"
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='default.jpg')
    date_joined = models.DateTimeField(default=timezone.now)
    
class Client(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name