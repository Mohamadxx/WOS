from django.contrib import admin
from .models import Author, Publication

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'h_index', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}



@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'document_type', 'publication_date')
    search_fields = ('title', 'wos_id', 'doi')