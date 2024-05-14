import json

from zoo.libs.hive import constants


def traverseDefinitionLayerDag(layerDef):
    """Depth first search recursive generator function which walks the layer definition DAG nodes.

    :param layerDef:
    :type layerDef: :class:`zoo.libs.hive.base.definition.definitionlayers.LayerDef`
    :return:
    :rtype: :class:`dict` or :class:`zoo.libs.hive.base.definition.definitionnodes.TransformDefinition`
    """

    def _nodeIter(n):
        for child in iter(n.get("children", [])):
            yield child
            for i in _nodeIter(child):
                yield i

    for node in iter(layerDef.get(constants.DAG_DEF_KEY, [])):
        yield node
        for ch in _nodeIter(node):
            yield ch


def parseRawDefinition(definitionData):
    translatedData = {}
    for k, v in definitionData.items():
        if not v:
            continue
        if k == "info":
            translatedData.update(json.loads(v))
            continue
        elif k == constants.SPACE_SWITCH_DEF_KEY:
            translatedData[constants.SPACE_SWITCH_DEF_KEY] = json.loads(v)
            continue
        dag, settings, metaData = (v[constants.DAG_DEF_KEY] or "[]",
                                   v[constants.SETTINGS_DEF_KEY] or ("{}" if k == constants.RIGLAYER_DEF_KEY else "[]"),
                                   v[constants.METADATA_DEF_KEY] or "[]")
        translatedData[k] = {constants.DAG_DEF_KEY: json.loads(dag),
                             constants.SETTINGS_DEF_KEY: json.loads(settings),
                             constants.METADATA_DEF_KEY: json.loads(metaData)}
    return translatedData
