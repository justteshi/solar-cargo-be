# Generated by Django 5.2.1 on 2025-06-15 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryreport',
            name='delivery_slip_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='delivery_slip_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='delivery_without_damages_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='delivery_without_damages_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='goods_according_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='goods_according_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='inspection_report_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='inspection_report_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='load_secured_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='load_secured_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='packaging_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='packaging_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='suitable_machines_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryreport',
            name='suitable_machines_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='deliveryreport',
            name='weather_conditions',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
