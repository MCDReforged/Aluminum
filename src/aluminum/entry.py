from aluminum.catalogues.online import PluginCatalogue

catalogue: PluginCatalogue

def on_load(server, prev_module):
    global catalogue
    catalogue = PluginCatalogue.load()
    for i in catalogue.plugins.values():
        print(i)