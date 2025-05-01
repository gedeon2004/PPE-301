from django.db import migrations, models
from django.conf import settings
import uuid

def set_references_and_vendeurs(apps, schema_editor):
    Commande = apps.get_model('boutique', 'Commande')
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)
    
    # Récupérez un utilisateur par défaut ou créez-en un
    default_user = User.objects.first()

    for cmd in Commande.objects.all():
        if not cmd.reference:
            cmd.reference = f"CMD-{uuid.uuid4().hex[:6].upper()}"
        if not cmd.vendeur and default_user:
            cmd.vendeur = default_user
        cmd.save()

class Migration(migrations.Migration):
    dependencies = [
        ('boutique', '0015_remove_commande_reference_remove_commande_vendeur'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='reference',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='commande',
            name='vendeur',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                null=True
            ),
        ),
        migrations.RunPython(set_references_and_vendeurs),
        migrations.AlterField(
            model_name='commande',
            name='reference',
            field=models.CharField(max_length=50, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name='commande',
            name='vendeur',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE
            ),
        ),
    ]