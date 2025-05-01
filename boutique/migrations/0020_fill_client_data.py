from django.db import migrations

def fill_client_data(apps, schema_editor):
    Order = apps.get_model('boutique', 'Order')

    # Vérifie si les attributs existent bien pour chaque champ
    for order in Order.objects.all():
        # On vérifie si les attributs nécessaires existent
        if hasattr(order, 'client_nom') and hasattr(order, 'client_prenom') and hasattr(order, 'client_email'):
            # Si jamais le champ client a été supprimé, cette ligne serait une erreur → on le remplace par un test sécurisé
            if hasattr(order, 'client') and order.client:
                # On récupère dynamiquement le modèle client si nécessaire
                Client = apps.get_model('auth', 'User')  # ou remplace 'auth' et 'User' selon ton modèle
                try:
                    client = Client.objects.get(pk=order.client_id)
                    order.client_nom = client.last_name or "Non spécifié"
                    order.client_prenom = client.first_name or "Non spécifié"
                    order.client_email = client.email or "Non spécifié"
                    order.save()
                except Client.DoesNotExist:
                    pass  # ignore si client introuvable

class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0019_remove_order_client_order_client_email_and_more'),
    ]

    operations = [
        migrations.RunPython(fill_client_data),
    ]
