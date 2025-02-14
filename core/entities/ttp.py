from __future__ import unicode_literals

from mongoengine import *

from core.entities import Entity


class TTP(Entity):
    KILL_CHAIN_STEPS = {
        "1": "Reconnaissance",
        "2": "Weaponisation",
        "3": "Delivery",
        "4": "Exploitation",
        "5": "Installation",
        "6": "C2",
        "7": "Objectives",
    }

    killchain = StringField(
        verbose_name="Kill Chain Stage",
        choices=list(KILL_CHAIN_STEPS.items()),
        required=True,
    )

    DISPLAY_FIELDS = Entity.DISPLAY_FIELDS + [("killchain", "Kill Chain")]

    meta = {
        "ordering": ["killchain"],
    }

    def info(self):
        i = Entity.info(self)
        i["killchain"] = self.KILL_CHAIN_STEPS[self.killchain]
        i["type"] = "ttp"
        return i

    def generate_tags(self):
        return [self.killchain.lower(), self.name.lower()]
