from .file_api import load_json, custom_components_path

class Manifest():

    def __init__(self, domain):
        self.domain = domain
        self.manifest_path = custom_components_path(f'{domain}/manifest.json')
        self.update()

    def update(self):
        data = load_json(self.manifest_path)
        self.name = data.get('name')
        self.version = data.get('version')
        self.documentation = data.get('documentation')

manifest = Manifest('updater')