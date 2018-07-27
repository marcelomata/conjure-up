import asyncio
import os
import json
from conjureup import controllers, juju, utils, snap
from conjureup.app_config import app
from conjureup.ui.views.destroy import DestroyView
from conjureup.models.step import StepModel
from juju.errors import JujuConnectionError
from juju.model import Model


class Destroy:

    def __init__(self):
        self.view = None
        self.deployed_spells = []

    async def _query_model_config(self, controller, model):
        if not app.juju.client:
            app.juju.client = Model(app.loop)
        target = "{}:{}".format(controller, model)
        try:
            # TODO: this could take a while; we should show an interstitial
            await asyncio.wait_for(app.juju.client.connect(target), 30)
        except (JujuConnectionError, asyncio.TimeoutError):
            app.log.debug('Unable to connect to {}; skipping'.format(target))
            return {}
        result = await app.juju.client.get_config()
        if 'extra-info' in result:
            extra_info = result['extra-info'].value
        else:
            extra_info = None
        app.log.debug('extra-info for {}:{}: {}'.format(controller,
                                                        model,
                                                        extra_info))
        if extra_info:
            try:
                result = json.loads(result['extra-info'].value)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass
        app.log.debug("Ignoring unintelligble model config for {}:{}: "
                      "{}".format(controller, model, extra_info))
        return {}

    def finish(self, spellname):
        for spell in self.deployed_spells:
            if spellname == spell['spellname']:
                if 'controller' in spell:
                    app.provider.controller = spell['controller']
                if 'model' in spell:
                    app.provider.model = spell['model']

        utils.set_chosen_spell(spellname,
                               os.path.join(app.conjurefile['cache-dir'],
                                            spellname))
        utils.set_spell_metadata()
        StepModel.load_spell_steps()
        controllers.setup_metadata_controller()
        return controllers.use('destroyconfirm').render()

        self.view = DestroyView(app,
                                spells=self.deployed_spells,
                                cb=self.finish)
        self.view.show()

    def render(self):
        pass


_controller_class = Destroy
