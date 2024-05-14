import copy
import json
import pprint
from collections import OrderedDict

from zoo.libs.utils import general
from zoo.libs.hive import constants

from zoo.libs.utils import profiling
from zoo.libs.hive.base.definition import definitionlayers
from zoo.libs.hive.base.definition import spaceswitch
from zoo.core.util import zlogging

__all__ = ["ComponentDefinition",
           "migrateToLatestVersion",
           "loadDefinition"]

logger = zlogging.getLogger(__name__)

# Definition keys to skip general update since we handle these explicitly
UPDATE_SKIP_KEYS = (constants.GUIDELAYER_DEF_KEY,
                    constants.RIGLAYER_DEF_KEY,
                    constants.INPUTLAYER_DEF_KEY,
                    constants.OUTPUTLAYER_DEF_KEY,
                    constants.DEFORMLAYER_DEF_KEY,
                    constants.SPACE_SWITCH_DEF_KEY)
# definition keys which need to be serialized to the template
TEMPLATE_KEYS = (constants.NAME_DEF_KEY,
                 constants.SIDE_DEF_KEY,
                 constants.GUIDELAYER_DEF_KEY,
                 constants.CONNECTIONS_DEF_KEY,
                 constants.PARENT_DEF_KEY,
                 constants.DEFINITION_VERSION_DEF_KEY,
                 constants.TYPE_DEF_KEY,
                 constants.GUIDE_MM_LAYOUT_DEF_KEY,
                 constants.DEFORM_MM_LAYOUT_DEF_KEY,
                 constants.RIG_MM_LAYOUT_DEF_KEY,
                 constants.ANIM_MM_LAYOUT_DEF_KEY,
                 constants.SPACE_SWITCH_DEF_KEY,
                 constants.NAMING_PRESET_DEF_KEY
                 )
# definition layer to scene attr mapping names. Used when we serialize
SCENE_LAYER_ATTR_TO_DEF = {
    constants.GUIDELAYER_DEF_KEY: [constants.DEF_CACHE_GUIDE_DAG_ATTR,
                                   constants.DEF_CACHE_GUIDE_SETTINGS_ATTR,
                                   constants.DEF_CACHE_GUIDE_METADATA_ATTR,
                                   constants.DEF_CACHE_GUIDE_DG_ATTR],
    constants.DEFORMLAYER_DEF_KEY: [constants.DEF_CACHE_DEFORM_DAG_ATTR,
                                    constants.DEF_CACHE_DEFORM_SETTINGS_ATTR,
                                    constants.DEF_CACHE_DEFORM_METADATA_ATTR,
                                    ""],
    constants.INPUTLAYER_DEF_KEY: [constants.DEF_CACHE_INPUT_DAG_ATTR,
                                   constants.DEF_CACHE_INPUT_SETTINGS_ATTR,
                                   constants.DEF_CACHE_INPUT_METADATA_ATTR,
                                   ""],
    constants.OUTPUTLAYER_DEF_KEY: [constants.DEF_CACHE_OUTPUT_DAG_ATTR,
                                    constants.DEF_CACHE_OUTPUT_SETTINGS_ATTR,
                                    constants.DEF_CACHE_OUTPUT_METADATA_ATTR,
                                    ""],
    constants.RIGLAYER_DEF_KEY: [constants.DEF_CACHE_RIG_DAG_ATTR,
                                 constants.DEF_CACHE_RIG_SETTINGS_ATTR,
                                 constants.DEF_CACHE_RIG_METADATA_ATTR,
                                 constants.DEF_CACHE_GUIDE_DG_ATTR],
}


class ComponentDefinition(general.ObjectDict):
    """This class describes the component, this is used by the component setup methods and is the fallback data
    for when the component has yet to be created in maya, the guides instance variable is a list of Guide objects which
    deal with the creation and serialization of each guide. when accessing the internal data of a guide. you should
    always refer to the internal "id" key as this will never change but users can rename so use "name" to get the
    user modified name.

    :param data:
    :type data: dict
    :param originalDefinition:
    :type originalDefinition: :class:`ComponentDefinition`
    :param path:
    :type path: str or None
    """
    definitionVersion = "2.0"

    def __init__(self, data=None, originalDefinition=None, path=None):
        data = data or {}
        data[constants.DEFINITION_VERSION_DEF_KEY] = self.definitionVersion
        data[constants.GUIDELAYER_DEF_KEY] = definitionlayers.GuideLayerDefinition.fromData(
            data.get(constants.GUIDELAYER_DEF_KEY, {}))
        data[constants.RIGLAYER_DEF_KEY] = definitionlayers.RigLayerDefinition.fromData(
            data.get(constants.RIGLAYER_DEF_KEY, {}))
        data[constants.INPUTLAYER_DEF_KEY] = definitionlayers.InputLayerDefinition.fromData(
            data.get(constants.INPUTLAYER_DEF_KEY, {}))
        data[constants.OUTPUTLAYER_DEF_KEY] = definitionlayers.OutputLayerDefinition.fromData(
            data.get(constants.OUTPUTLAYER_DEF_KEY, {}))
        data[constants.DEFORMLAYER_DEF_KEY] = definitionlayers.DeformLayerDefinition.fromData(
            data.get(constants.DEFORMLAYER_DEF_KEY, {}))
        data[constants.PARENT_DEF_KEY] = data.get(constants.PARENT_DEF_KEY, [])
        data[constants.CONNECTIONS_DEF_KEY] = data.get(constants.CONNECTIONS_DEF_KEY, {})
        data[constants.SPACE_SWITCH_DEF_KEY] = [spaceswitch.SpaceSwitchDefinition(i) for i in
                                                data.get(constants.SPACE_SWITCH_DEF_KEY, [])]
        super(ComponentDefinition, self).__init__(data)
        self.path = path or ""

        if originalDefinition is not None:
            self.originalDefinition = ComponentDefinition(originalDefinition)
        else:
            self.originalDefinition = {}

    def serialize(self):
        data = {}
        for k, v in self.items():
            if k in ("originalDefinition", "path"):
                continue
            data[k] = v
        spaces = []

        for i in self.spaceSwitching:
            existingSpace = self.originalDefinition.spaceSwitchByLabel(i["label"])
            if not existingSpace:
                spaces.append(i)
            else:
                difference = i.difference(existingSpace)
                if difference:
                    spaces.append(difference)
        data[constants.SPACE_SWITCH_DEF_KEY] = spaces
        return data

    @property
    def guideLayer(self):
        """
        :return:
        :rtype: :class:`definitionlayers.GuideLayerDefinition`
        """
        return self[constants.GUIDELAYER_DEF_KEY]

    @property
    def rigLayer(self):
        """
        :return:
        :rtype: :class:`definitionlayers.RigLayerDefinition`
        """
        return self[constants.RIGLAYER_DEF_KEY]

    @property
    def deformLayer(self):
        """
        :return:
        :rtype: :class:`definitionlayers.DeformLayerDefinition`
        """
        return self[constants.DEFORMLAYER_DEF_KEY]

    @property
    def outputLayer(self):
        """
        :return:
        :rtype: :class:`definitionlayers.OutputLayerDefinition`
        """
        return self[constants.OUTPUTLAYER_DEF_KEY]

    @property
    def inputLayer(self):
        """
        :return:
        :rtype: :class:`definitionlayers.InputLayerDefinition`
        """
        return self[constants.INPUTLAYER_DEF_KEY]

    def pprint(self):
        """Pretty prints the current definition
        """
        pprint.pprint(dict(self.serialize()))

    def __repr__(self):
        return "<{}> {}".format(self.__class__.__name__, self.name)

    def toJson(self, template=False):
        """Returns the string version of the definition.

        :return: json converted string of the current definition
        :rtype: str
        """
        if template:
            return json.dumps(self.toTemplate())
        return json.dumps(self.serialize())

    def toSceneData(self):
        serializedData = self.serialize()
        outputData = {}
        for layerKey, [dagLayerAttrName, settingsAttrName, metaDataAttrName,
                       dgAttrName] in SCENE_LAYER_ATTR_TO_DEF.items():
            layer = serializedData.get(layerKey, {})
            outputData[dagLayerAttrName] = json.dumps(layer.get(constants.DAG_DEF_KEY, []))
            outputData[settingsAttrName] = json.dumps(
                layer.get(constants.SETTINGS_DEF_KEY, [] if layerKey != constants.RIGLAYER_DEF_KEY else {}))
            outputData[metaDataAttrName] = json.dumps(layer.get(constants.METADATA_DEF_KEY, []))
            if dgAttrName:
                outputData[dgAttrName] = json.dumps(layer.get(constants.DG_GRAPH_DEF_KEY, []))

        spaceSwitchingData = serializedData.get(constants.SPACE_SWITCH_DEF_KEY, {})
        outputData[constants.DEF_CACHE_SPACE_SWITCHING_ATTR] = json.dumps(spaceSwitchingData)
        infoData = {}
        for k in (constants.NAME_DEF_KEY,
                  constants.SIDE_DEF_KEY,
                  constants.CONNECTIONS_DEF_KEY,
                  constants.PARENT_DEF_KEY,
                  constants.DEFINITION_VERSION_DEF_KEY,
                  constants.TYPE_DEF_KEY,
                  constants.GUIDE_MM_LAYOUT_DEF_KEY,
                  constants.DEFORM_MM_LAYOUT_DEF_KEY,
                  constants.RIG_MM_LAYOUT_DEF_KEY,
                  constants.ANIM_MM_LAYOUT_DEF_KEY,
                  constants.NAMING_PRESET_DEF_KEY):
            infoData[k] = serializedData.get(k, "")
        outputData[constants.DEF_CACHE_INFO_ATTR] = json.dumps(infoData)
        return outputData

    def toTemplate(self):
        """Returns a dict only containing the necessary information for template storage which should only
        be the guide information, all rig related keys are skipped since this isn't required and if
        included would reduce too much data complexity into updates.

        :returns: a dict contains the keys ("name", "side", "guideLayer", \
        constants.CONNECTIONS_DEF_KEY, constants.PARENT_DEF_KEY, "type")
        :rtype: dict

        """
        data = self.serialize()
        raw = copy.deepcopy({n: info for n, info in data.items() if n in TEMPLATE_KEYS})
        ignoreMetaAttrs = ("guideVisibility",
                           "guideControlVisibility")
        metaData = []
        for metaAttr in raw[constants.GUIDELAYER_DEF_KEY].get(constants.SETTINGS_DEF_KEY):
            if metaAttr not in ignoreMetaAttrs:
                metaData.append(metaAttr)
        raw[constants.GUIDELAYER_DEF_KEY][constants.METADATA_DEF_KEY] = metaData
        return raw

    def asDefinitionBaseData(self):
        """Specialized method which converts the definition data to a compatible bare minimal definition for
        saving to disk as a base definition.
        """
        raw = copy.deepcopy(self)
        del raw["guideLayer"]["metaData"]
        del raw["guideLayer"]["connections"]
        del raw["guideLayer"]["parent"]
        if "path" in raw:
            del raw["path"]
        return raw

    def __getattr__(self, item):
        """Loop for guide objects and return the first guide object that has the name

        :param item: the name of the guide
        :type item: str
        :rtype: instance(Guide)
        """
        try:
            return self[item]
        except KeyError:
            pass
        guid = self.guideLayer.guide(item)
        if guid is not None:
            return guid

        return super(ComponentDefinition, self).__getattribute__(item)

    @profiling.fnTimer
    def update(self, kwargs):
        """Overridden to convert any attributes to Setting objects

        :param kwargs:
        :type kwargs: :class:`Definition`
         """
        self[constants.GUIDELAYER_DEF_KEY].update(kwargs.get(constants.GUIDELAYER_DEF_KEY, {}))
        self[constants.RIGLAYER_DEF_KEY].update(kwargs.get(constants.RIGLAYER_DEF_KEY, {}))
        self[constants.INPUTLAYER_DEF_KEY].update(kwargs.get(constants.INPUTLAYER_DEF_KEY, {}))
        self[constants.OUTPUTLAYER_DEF_KEY].update(kwargs.get(constants.OUTPUTLAYER_DEF_KEY, {}))
        self[constants.DEFORMLAYER_DEF_KEY].update(kwargs.get(constants.DEFORMLAYER_DEF_KEY, {}))
        self.updateSpaceSwitching(kwargs.get(constants.SPACE_SWITCH_DEF_KEY, []))

        for k, v in kwargs.items():
            if k not in UPDATE_SKIP_KEYS:
                self[k] = v

    def spaceSwitchByLabel(self, label):
        """

        :param label:
        :type label: str
        :return:
        :rtype: :class:`spaceswitch.SpaceSwitchDefinition`
        """
        for i in self.get(constants.SPACE_SWITCH_DEF_KEY, []):
            if i.label == label:
                return i

    def removeSpacesByLabel(self, labels):
        spacesToDelete = []
        for i, space in enumerate(self.get(constants.SPACE_SWITCH_DEF_KEY, [])):
            if space.label in labels:
                spacesToDelete.append(space)
        for index in spacesToDelete:
            self[constants.SPACE_SWITCH_DEF_KEY].remove(index)

    def removeSpaceSwitch(self, label):

        for i, space in enumerate(self.get(constants.SPACE_SWITCH_DEF_KEY, [])):
            if space.label == label:
                logger.debug("Removing SpaceSwitch: {}".format(label))
                del self[constants.SPACE_SWITCH_DEF_KEY][i]
                return True
        return False

    def createSpaceSwitch(self, label, drivenId, constraintType, controlPanelFilter, permissions,
                          drivers):
        existingSpace = self.spaceSwitchByLabel(label)
        if existingSpace:
            existingSpace.controlPanelFilter = controlPanelFilter
            existingSpace.permissions = permissions
            existingSpace["drivers"] = [spaceswitch.SpaceSwitchDriverDefinition(i) for i in drivers]
            return existingSpace
        logger.debug("Creating Space Switching Definition: {}".format(label))
        space = {
            "label": label,
            "controlPanelFilter": controlPanelFilter,
            "driven": drivenId,
            "type": constraintType,
            "permissions": permissions,
            "drivers": drivers
        }
        spaceDef = spaceswitch.SpaceSwitchDefinition(space)
        self[constants.SPACE_SWITCH_DEF_KEY].append(spaceDef)
        return spaceDef

    def updateSpaceSwitching(self, spaces):
        """merges incoming space switches with the current.

        #. Merges any missing spaces.


        """
        if not spaces:
            return
        existingSpaces = OrderedDict((k["label"], k) for k in self.get(constants.SPACE_SWITCH_DEF_KEY))
        for space in spaces:
            label = space["label"]
            panelFilter = space.get("controlPanelFilter", {})
            default = panelFilter.get("default", "")
            drivers = space.get("drivers", [])
            existingSpace = existingSpaces.get(label)
            if not existingSpace:
                existingSpaces[label] = space
                continue

            existingDrivers = {i.label: i for i in existingSpace.drivers}
            # merged based on the incoming drivers not the existing.
            mergedDrivers = []
            for driver in drivers:
                existingDriver = existingDrivers.get(driver["label"])
                if existingDriver:
                    mergedDrivers.append(existingDriver)
                else:
                    mergedDrivers.append(spaceswitch.SpaceSwitchDriverDefinition(**driver))
            existingSpace.drivers = mergedDrivers
            existingSpace.defaultDriver = default

        self[constants.SPACE_SWITCH_DEF_KEY] = [spaceswitch.SpaceSwitchDefinition(i) for i in existingSpaces.values()]


def loadDefinition(definitionData, originalDefinition, path=None):
    """

    :param definitionData:
    :type definitionData: dict
    :param path:
    :type path: str
    :return:
    :rtype: :class:`ComponentDefinition`
    """
    # in this case we need to upgrade the definition for the old to the new
    # for now something hardcode to go between 1.0 and 2.0
    latestData = migrateToLatestVersion(definitionData)
    return ComponentDefinition(data=latestData, originalDefinition=copy.deepcopy(originalDefinition), path=path)


def migrateToLatestVersion(definitionData, originalComponent=None):
    """Function which migrates definition schema from an old version to latest.

    :param definitionData: The definition data as a raw dict
    :type definitionData: dict
    :param originalComponent: The unmodified component definition, usually this is the \
    base definition for the component.
    :type originalComponent: :class:`ComponentDefinition`
    :return: Translated definition data to the latest schema
    :rtype: dict
    """
    if originalComponent:
        # We expect that the rigLayer comes from the base definition not the scene so maintain the
        # original.
        definitionData[constants.RIGLAYER_DEF_KEY] = originalComponent[constants.RIGLAYER_DEF_KEY]
    return definitionData
    # raise NotImplementedError("UnSupported definition version: {}".format(requestedVersion))
