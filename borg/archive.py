# ...existing code...
from .platform import fat
# ...existing code...

class Archive:
    # ...existing code...

    def stat_item(self, path, st, item):
        # ...existing code...
        if fat.is_fat_filesystem(path):
            try:
                item['fat_attributes'] = fat.get_fat_attributes(path)
            except Exception:
                item['fat_attributes'] = None
        # ...existing code...

    def extract_item(self, item, restore_attrs=True):
        # ...existing code...
        if restore_attrs and 'fat_attributes' in item and item['fat_attributes'] is not None:
            try:
                fat.set_fat_attributes(path, item['fat_attributes'])
            except Exception:
                pass
        # ...existing code...
