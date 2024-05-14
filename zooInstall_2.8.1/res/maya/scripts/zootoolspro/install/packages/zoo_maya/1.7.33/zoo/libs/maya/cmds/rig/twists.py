"""Code for calculating twist between two objects using quaternions.


Example use:

.. code-block:: python

    from zoo.libs.maya import zapi
    from zoo.libs.maya.cmds.rig import twists
    twists.twistNodeNetwork(zapi.nodeByName("joint1"),
                            zapi.nodeByName("joint1"),
                            drivenObj=zapi.nodeByName("twist1deformer"),
                            drivenAttr="endAngle",
                            axis="x",
                            inverse=True)

Author: Andrew Silke
"""
from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.utils import output

try:
    from zoo.libs.hive import api
except:
    pass


def obj():
    """Helper for UI, returns the selected object"""
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("No objects selected, please select an object")
        return ""
    return selObjs[0]


def twistNodeNetwork(controlA, controlB, axis="x", drivenObj=None, drivenAttr="", inverse=False):
    inverseNode = None
    graphData = api.Configuration().graphRegistry().graph("distributedTwist")
    sceneGraph = api.serialization.NamedDGGraph.create(graphData)
    sceneGraph.connectToInput("driverSrtWorldInvMtx", controlB.attribute("worldInverseMatrix")[0])
    sceneGraph.connectToInput("drivenSrtWorldMtx", controlA.attribute("worldMatrix")[0])

    # Get nodes ---------------------
    twistOffsetNode = sceneGraph.node("twistOffset")
    offsetQuatNode = sceneGraph.node("twistOffsetQuat")
    offsetEulerNode = sceneGraph.node("twistOffsetEuler")

    # Set axis, is connected to x by default -----------------
    if axis != "x":
        offsetQuatNode.outputQuatX.disconnectAll()
        outAttr = "outputQuat{}".format(axis.upper())
        inAttr = "inputQuat{}".format(axis.upper())
        offsetQuatNode.attribute(outAttr).connect(offsetEulerNode.attribute(inAttr))

    # Invert the output ----------------------
    if inverse:
        inverseNode = zapi.createDG("twistInverseMult", "multiplyDivide")
        inverseNode.attribute("input2{}".format(axis.upper())).set(-1.0)

    # Driven attribute -----------------------
    if drivenObj:
        outAttr = "outputRotate{}".format(axis.upper())
        if not inverse:
            offsetEulerNode.attribute(outAttr).connect(drivenObj.attribute(drivenAttr))
        else:  # Invert
            invertInAttr = "input1{}".format(axis.upper())
            invertOutAttr = "output{}".format(axis.upper())
            offsetEulerNode.attribute(outAttr).connect(inverseNode.attribute(invertInAttr))
            inverseNode.attribute(invertOutAttr).connect(drivenObj.attribute(drivenAttr))

    return twistOffsetNode, offsetQuatNode, offsetEulerNode, inverseNode
