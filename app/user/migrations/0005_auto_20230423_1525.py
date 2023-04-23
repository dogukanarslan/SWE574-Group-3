# Generated by Django 3.1.1 on 2023-04-23 15:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20230404_1357'),
    ]

    operations = [
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200)),
                ('level', models.IntegerField(choices=[(1, 'Platinum'), (2, 'Silver'), (3, 'Gold')])),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='badge',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_badges', to='user.badge'),
        ),
    ]
