from django.contrib import admin
from .models import File, FileShare


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display  = ('filename', 'owner', 'file_size_display', 'storage_mode', 'upload_date', 'blockchain_tx_hash')
    list_filter   = ('owner', 'upload_date')
    search_fields = ('filename', 'owner__username', 'file_hash')
    readonly_fields = ('file_hash', 'blockchain_tx_hash', 'ipfs_cid', 'encrypted_file_path', 'upload_date')


@admin.register(FileShare)
class FileShareAdmin(admin.ModelAdmin):
    list_display = ('file', 'shared_by', 'shared_with', 'shared_at', 'can_download')
    list_filter  = ('shared_by', 'shared_with')