import maya.cmds as cmds
from maya.mel import eval as meval

import sys

def show(msg):
    meval("_show(\"%s\");" % (
        "py : " + msg)
    )

def conn(msg):
    meval("_show(\"%s\");" % (
        "py :       " + msg)
    )


def UpdateGUI_TextureSettings_Workflow(attributeName):
    workflowAtt = attributeName

    value = cmds.getAttr(workflowAtt)
    cmds.attrEnumOptionMenuGrp("workflowMenuGrp",
                               attribute=attributeName,
                               edit=True, enable=True)

    return value

def CreateGUI_TextureSettings_Workflow(attributeName):
    workflowAtt = nodeName + ".workflow";


def sbs_GetMaterialFromSubstanceNodeOrCreateIt(nodeName, PBRWorkflow):
    show("sbs_GetMaterialFromSubstanceNodeOrCreateIt( " + nodeName + ", ... )...");
    return meval("sbs_GetMaterialFromSubstanceNodeOrCreateIt(\"%s\", %d);" % (
        nodeName, PBRWorkflow)
    )


def sbsGetShadingGroupFromMaterial(material):
    show("sbsGetShadingGroupFromMaterial( " + material + " )...");
    if cmds.attributeQuery("outColor", exists=True, node=material) == True:
        shadingGroups = cmds.listConnections("%s.outColor" % material)
        if len(shadingGroups):
            return  shadingGroups[0]  # return first

    return ""

def sbs_RearrangeHypershadeGraph():
    show("sbs_RearrangeHypershadeGraph()...");
    meval("sbs_RearrangeHypershadeGraph();")


def getSubstanceOutputNodeConnected(nodeName, channelName):
    show("getSubstanceOutputNodeConnected( " + nodeName + ", " + channelName + " )...");
    return meval("getSubstanceOutputNodeConnected( \"%s\", \"%s\");" % (
        nodeName, channelName)
    )


def createOrGetSubstanceOutputNode(nodeName, channelName):
    show("createOrGetSubstanceOutputNode( " + nodeName + ", " + channelName + " )...");
    meval("createOrGetSubstanceOutputNode( \"%s\", \"%s\");" % (
        nodeName, channelName)
    )

def sbsAreAlreadyConnected(nodeWithAttributeName, otherNode):
    """ returns whether two nodes are connected

    """
    connectedOutputs = cmds.listConnections(nodeWithAttributeName)
    if connectedOutputs is not None:
        return otherNode in connectedOutputs
    else:
        return 0


def sbsConnectOutputNode(channelName, nodeName, outputNodeName,
                          material, shadingGroup,
                          sbs_AutomaticBakeCheck):
    """ Connects substance output nodes to maya shader or material. When auto
    baking is activated, it will also create and connect the file node.

    """
    show("sbsConnectOutputNode( " + channelName + ", " + nodeName + ", " + outputNodeName + ", ... )...");
    # here "normal camera" slot was not found in material because we are use stingray PBR shader
    # thus we force auto baking as PBR require file map
    #XXXdlet: we could also check the node's workflow
    if (cmds.attributeQuery("normalCamera", exists=True, node=material) == False and
        channelName in ["baseColor", "normal", "roughness", "glossiness", "metallic", "ambientOcclusion", "emissive"] and
        sbs_AutomaticBakeCheck == 0):
        outputNodeName = sbsBakeOutput(outputNodeName, channelName)

    if (channelName in ["normal", "bump"] and
        cmds.attributeQuery("normalCamera", exists=True, node=material)):

        connectedNodes = cmds.listConnections(material + ".normalCamera")
        shaderConnected = cmds.listConnections(outputNodeName + ".outAlpha", type="bump2d")
        if connectedNodes == None:
            shader = ""
            if shaderConnected is not None:
                shader = shaderConnected[0]
            else:
                shader = cmds.shadingNode("bump2d", asUtility=True)

            attr = outputNodeName + ".outAlpha"
            alreadyConnected = sbsAreAlreadyConnected(attr, shader)
            if not alreadyConnected:
                conn("50: cmds.connectAttr( " + attr + ", " + shader + ".bumpValue, force=True )")
                cmds.connectAttr(attr, shader + ".bumpValue", force=True)

            attr = shader + ".outNormal"
            alreadyConnected = sbsAreAlreadyConnected(attr, material)
            if not alreadyConnected:
                conn("51: cmds.connectAttr( " + attr + ", " + material + ".normalCamera, force=True )")
                cmds.connectAttr(attr, material + ".normalCamera", force=True)

            cmds.select(shader, replace=True)
            if channelName == "normal":
                cmds.setAttr(shader + ".bumpInterp", 1)
            cmds.rename(shader, nodeName + "_bump2d")
        else:
            found = 0
            for connectedNode in connectedNodes:
                if shaderConnected is not None:
                    for node in shaderConnected:
                        if connectedNode == node:  # Is this bump2dnode conencted to the material ?
                            # They are already connected, so don t warn user.
                            found = 1
                            break

            if found == 0:
                shader = cmds.shadingNode("bump2d", asUtility=True)
                attr = outputNodeName + ".outAlpha"
                conn("52: cmds.connectAttr( " + attr + ", " + shader + ".bumpValue, force=True )")
                cmds.connectAttr(attr, shader + ".bumpValue", force=True)
                cmds.select(shader, replace=True)
                cmds.rename(shader, shader + "_bump2d")

                # Something is already connected in the (material + ".normalCamera") attribute
                ok = "OK"
                cmds.confirmDialog(message="Substance " + channelName + "Output node is created, but connection to attribute : \""+material+".normalCamera\" could not be made : previous connections exist", button=ok, defaultButton=ok)

    elif channelName in ["Height", "Displacement"] and shadingGroup != "":
        connectedShaders = cmds.listConnections(shadingGroup + ".displacementShader")
        if not connectedShaders:
            shader = ""
            shaderConnected = cmds.listConnections(outputNodeName + ".outColorR", type="displacementShader")
            if shaderConnected:
                shader = shaderConnected[0]
            else:
                shader = cmds.shadingNode("displacementShader", asShader=True)

            cmds.select(shader, replace=True)
            shader = cmds.rename(shader, nodeName + "_" + channelName + "Map")

            attr = outputNodeName + ".outColorR"
            if not sbsAreAlreadyConnected(attr, shader):
                conn("53: cmds.connectAttr( " + attr + ", " + shader + ".displacement, force=True )")
                cmds.connectAttr(attr, shader + ".displacement", force=True)

            attr = shader + ".displacement"
            if not sbsAreAlreadyConnected(attr, shadingGroup):
                conn("54: cmds.connectAttr( " + attr + ", " + shadingGroup + ".displacementShader, force=True )")
                cmds.connectAttr(attr, shadingGroup + ".displacementShader", force=True)
        else:
            # Something is already connected to the shading group .displacement shader
            shaderConnected = cmds.listConnections(outputNodeName + ".outColorR", type="displacementShader")

            #Is this displacement shader already connected ?
            found = 0
            connectedShader = ""
            for connectedShader in connectedShaders:
                shader = ""
                if shaderConnected:
                    for shader in shaderConnected:
                        if connectedShader == shader:
                            #They are already connected, so don't warn user.
                            found = 1
                            break

            if not found:
                shader = cmds.shadingNode("displacementShader", asShader=True)
                cmds.select(shader, replace=True)
                shader = cmds.rename(shader, nodeName + "_" + channelName + "Map")

                attr = outputNodeName + ".outColorR"
                conn("55: cmds.connectAttr( " + attr + ", " + shader + ".displacement, force=True )")
                cmds.connectAttr(attr, shader + ".displacement", force=True)

                # Something is already connected in the (shadingGroup + ".displacementShader") attribute
                ok = "OK"
                cmds.confirmDialog(message="Substance " + channelName + "Output node is created, but connection to attribute : \"" + shadingGroup + ".displacementShader\" could not be made : previous connections exist",
                                   button=ok, defaultButton=ok)
    else:

        show("In sbsConnectOutputNode -> %s.workflow = %d" % (nodeName, cmds.getAttr("%s.workflow" % nodeName)));

        channelMapping = {
            "opacity": ("transparency", 1),# if cmds.getAttr("%s.workflow" % nodeName) == 0 else ("TEX_mask_map", 0), # TODO: MAYA-142, blocked for now
            "diffuse": ("color", 0),
            "emissive": ("incandescence", 0) if cmds.getAttr("%s.workflow" % nodeName) == 0 else ("TEX_emissive_map", 0),
            "glossiness": ("DONOTCONNECT", 0) if cmds.getAttr("%s.workflow" % nodeName) == 0 else ("DONOTCONNECTEITHER", 0),
            "gloss": ("DONOTCONNECT", 0),
            "specular": ("specularColor", 0),
            "baseColor": ("TEX_color_map", 0),
            "normal": ("TEX_normal_map", 0),
            "roughness": ("TEX_roughness_map", 0),
            "metallic": ("TEX_metallic_map", 0),
            "ambientOcclusion": ("TEX_ao_map", 0),
        }

        connectPin, reverseoutput = channelMapping.get(channelName, ("COULDNOTCONNECT", 0))
        attr = outputNodeName + ".outColor"

        show("In sbsConnectOutputNode -> channelMapping for %s : %s, %d" % (channelName, connectPin, reverseoutput));

        if cmds.attributeQuery(connectPin, exists=True, node=material):
            if reverseoutput == 1:
                reverse = ""
                reverseConnected = cmds.listConnections(outputNodeName + ".outColor", type="reverse")
                if reverseConnected:
                    reverse = reverseConnected[0]
                else:
                    reverse = cmds.shadingNode("reverse", asUtility=True)

                if not sbsAreAlreadyConnected(attr, reverse):
                    conn("56: cmds.connectAttr( " + attr + ", " + reverse + ".input, force=True )")
                    cmds.connectAttr(attr, reverse + ".input", force=True)

                attr = reverse + ".output"

            if not sbsAreAlreadyConnected(attr, material):
                conn("57: cmds.connectAttr( " + attr + ", " + material + "." + connectPin + ",  force=True )")
                cmds.connectAttr(attr, material + "." + connectPin, force=True)
        elif connectPin == "COULDNOTCONNECT":
            ok = "OK"
            cmds.confirmDialog(message="Substance " + channelName + " Output Node could not be automatically connected to the shader node. Please manually connect the output to the appropriate shader input",
                               button=ok, defaultButton=ok)


def sbsBakeOutput(outputNodeName, channelName):
    show("sbsBakeOutput( " + outputNodeName + " )...");
    imageBaking = ""
    imageBakingConnected = cmds.listConnections(outputNodeName + ".outImage", type="file")
    if imageBakingConnected :
        imageBaking = imageBakingConnected[0]
    else:
        imageBaking = cmds.shadingNode("file", asTexture=True, icm=True)

    attr = outputNodeName + ".outImage"
    if not sbsAreAlreadyConnected(attr, imageBaking):
        conn("58: cmds.connectAttr( " + attr + ", " + imageBaking + ".fileTextureName, force=True )")
        cmds.connectAttr(attr, imageBaking + ".fileTextureName", force=True)
        place2DTextureNode = cmds.listConnections(outputNodeName+".uv")
        conn("59: cmds.connectAttr( " + place2DTextureNode[0] + ".outUV " + imageBaking + ".uv )")
        cmds.connectAttr(place2DTextureNode[0]+".outUV", imageBaking+".uv")
        conn("60: cmds.connectAttr( " + place2DTextureNode[0] + ".outUvFilterSize " + imageBaking + ".uvFilterSize )")
        cmds.connectAttr(place2DTextureNode[0]+".outUvFilterSize", imageBaking+".uvFilterSize")

        # Override the Maya default color space and luminance values for these outputs:
        if channelName == "metallic":
            cmds.setAttr(imageBaking + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(imageBaking + '.alphaIsLuminance', 1)

        elif channelName == "height":
            cmds.setAttr(imageBaking + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(imageBaking + '.alphaIsLuminance', 1)
            cmds.setAttr(imageBaking + '.alphaOffset', -0.5)

        elif channelName == "roughness":
            cmds.setAttr(imageBaking + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(imageBaking + '.alphaIsLuminance', 1)

        elif channelName == "glossiness":
            cmds.setAttr(imageBaking + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(imageBaking + '.alphaIsLuminance', 1)

        elif channelName == "normal":
            cmds.setAttr(imageBaking + '.colorSpace', 'Raw', type='string')


    return imageBaking


def sbsChannelTreeViewButtonClickCommand(nodeName, itemClicked, buttonState):
    show("sbsChannelTreeViewButtonClickCommand( " + nodeName + ", " + itemClicked + ", ...)...");

    g_OutputConnectedImage = ""

    formatAtt = "%s.bakeFormat" % nodeName
    AutomaticBakeCheck = "%s.autoBake" % nodeName
    sbs_AutomaticBakeCheck = cmds.getAttr(AutomaticBakeCheck)
    PBRWorkflow = cmds.getAttr("%s.workflow" % nodeName)

    channelName = itemClicked

    createOrGetSubstanceOutputNode(nodeName, channelName) # This function checks if the node already exists or not
    outputNodeName = getSubstanceOutputNodeConnected(nodeName, channelName)

    if sbs_AutomaticBakeCheck == 1:
        outputNodeName = sbsBakeOutput(outputNodeName, channelName)

    if PBRWorkflow != 2:   # Try to connect outputs in Traditionnal and PBR mode
                           # Let user handle outputs himself in Custom mode
        # Create material and shading group
        material = sbs_GetMaterialFromSubstanceNodeOrCreateIt(nodeName, PBRWorkflow)
        if material == "":
            return

        shadingGroup = sbsGetShadingGroupFromMaterial(material);

        # We are testing it but it should be present as we have built it
        if outputNodeName != "":
            sbsConnectOutputNode(channelName, nodeName, outputNodeName,
                                 material, shadingGroup,
                                 sbs_AutomaticBakeCheck)

    cmds.select(nodeName, replace=True)

    sbs_RearrangeHypershadeGraph()


def sbsCreateShadingNet(nodeName):
    """ Activates and create substance outputs. Links to phong Shader

    """
    show("sbsCreateShadingNet( " + nodeName + " )...");
    graph = cmds.getAttr("%s.graph" % nodeName)
    package = cmds.getAttr("%s.package" % nodeName)
    prefix = "outputdyn_"
    postfixChannelName = "_Name"

    workflow = cmds.getAttr("%s.workflow" % nodeName)
    if workflow == 0:  # CLASSIC
        # Normal
        attrName = prefix + "normal" + postfixChannelName;
        if cmds.attributeQuery(attrName, exists=True, node=nodeName) == True:
            sbsChannelTreeViewButtonClickCommand(nodeName, "normal", 1)
        else:
            # If no normal is present, connect the bump (if any)
            attrName = prefix + "bump" + postfixChannelName;
            if cmds.attributeQuery(attrName, exists=True, node=nodeName) == True:
                sbsChannelTreeViewButtonClickCommand(nodeName, "bump", 1)

        # Always connect the diffuse at the end, as if the substanceTex.outColor is
        # connected to a material, it will replace it with a substance output. If it
        # does so, the others shaders may want to create a new shader
        channels = ["opacity", "specular", "diffuse"]
    elif workflow == 1:  # StingrayPBR
        channels = ["baseColor", "normal", "metallic", "roughness", "ambientOcclusion", "emissive"]  # TODO: MAYA-142 (opacity)
    else:  # Custom
        channels = []  # do not connect any channel


    show("In sbsCreateShadingNet -> ############## TreeView handling starts ###############");
    unconnectedChannels = 0
    connectedChannels = 0
    for channel in channels:
        attrName = prefix + channel + postfixChannelName;
        if cmds.attributeQuery(attrName, exists=True, node=nodeName) == True:
            sbsChannelTreeViewButtonClickCommand(nodeName, channel, 1)
            connectedChannels += 1
        else:
            unconnectedChannels += 1

    # Not all assets have the exact amount of expected outputs! Remove the message below:
    if connectedChannels == 0:
        ok = "OK"
        cmds.confirmDialog(message="No Substance Output Node could not be "
                                   "automatically connected to the shader node. Please "
                                   "manually connect the output to the appropriate shader "
                                   "input or exit custom workflow",
                           button=ok,
                           defaultButton=ok)

    # rename of newly created nodes
    sbs_RearrangeHypershadeGraph()
    cmds.select(nodeName, replace=True)
    sbs_RearrangeHypershadeGraph()
    show("In sbsCreateShadingNet -> ############## TreeView handling done ################");


def sbsCreateShader(nodeName):
    """ Creates and initializes stingray PB Shader

    """
    show("sbsCreateShader( " + nodeName + " )...");
    material = cmds.shadingNode("StingrayPBS", asShader=True)
    shadingGroup = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="StingrayPBS1SG")
    cmds.shaderfx(sfxnode=material, initShaderAttributes=True)

    # connect material2shadingG //
    conn("61: cmds.connectAttr( " + material + ".outColor, " + shadingGroup + ".surfaceShader, force=True )")
    cmds.connectAttr("%s.outColor" % material, "%s.surfaceShader" % shadingGroup, force=True)

    # activate use texture maps
    show("TURN ON MAP ATTRIBUTES...");
    for tex_map in ["color", "normal", "metallic", "roughness", "ao", "emissive"]:
        if cmds.attributeQuery("%s.use_%s_map" % (material, tex_map), exists=True, node=material) == False:
            show("SET ATTRIBUTE: %s.use_%s_map ..." % (material, tex_map));
            cmds.setAttr("%s.use_%s_map" % (material, tex_map), 1)
        else:
            show("ERROR: %s.use_%s_map DOES NOT EXIST!!!" % (material, tex_map));

    cmds.select(material, replace=True)
    cmds.rename(material, nodeName + "_Material")
    material = nodeName + "_Material"
    cmds.hyperShade(shaderNetwork=material)


