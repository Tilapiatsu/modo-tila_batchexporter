﻿#!/usr/bin/env python

import lx
import os
import sys

# Arguments
triple_sw = '0'
resetPos_sw = '0'
rotAngle = '0'
scaleAmount = '1'
smoothAngle_sw = '0'
smoothAngle = '1'
exportFile = '1'
exportEach = '1'
exportHierarchy = '0'
scanFiles = '0'
upAxis = lx.eval('pref.value units.upAxis ?')
iUpAxis = upAxis


# Get the current FBX Export setting.
fbx_export_setting = lx.eval1('user.value sceneio.fbx.save.exportType ?')

sceneIndex = lx.eval('query sceneservice scene.index ? current')
userSelection = lx.evalN('query layerservice layer.id ? fg')
userSelectionCount = len(userSelection)
currentPath = lx.eval("query sceneservice scene.file ? current")


def init_dialog(dialog_type):
    if dialog_type == "input":
        # Get the directory to export to.
        lx.eval('dialog.setup fileOpenMulti')
        lx.eval('dialog.fileType scene')
        lx.eval('dialog.title "Mesh Path"')
        lx.eval('dialog.msg "Select the meshes you want to process."')
        lx.eval('dialog.result "%s"' % currentPath)

    if dialog_type == "output":
        # Get the directory to export to.
        lx.eval('dialog.setup dir')
        lx.eval('dialog.title "Export Path"')
        lx.eval('dialog.msg "Select path to export to."')
        lx.eval('dialog.result "%s"' % currentPath)

    if dialog_type == 'file_save':
        init_custom_dialog('fileSave', 'SaveFile', ('FBX',), 'FBX file', ('*.FBX',), 'fbx', currentPath[:-4])

    if dialog_type == "cancel":
        init_message('error', 'Canceled', 'Operation aborded')
        sys.exit()


# http://modo.sdk.thefoundry.co.uk/wiki/Dialog_Commands
def init_custom_dialog(type, title, format, uname, ext, save_ext=None, path=None, init_dialog = False):
    ''' Custom file dialog wrapper function

        type  :   Type of dialog, string value, options are 'fileOpen' or 'fileSave'
        title :   Dialog title, string value.
        format:   file format, tuple of string values
        uname :   internal name
        ext   :   tuple of file extension filter strings
        save_ext: output file extension for fileSave dialog
        path  :   optional default loacation to open dialog

    '''
    lx.eval("dialog.setup %s" % type)
    lx.eval("dialog.title {%s}" % (title))
    lx.eval("dialog.fileTypeCustom {%s} {%s} {%s} {%s}" % (format, uname, ext, save_ext))
    if type == 'fileSave' and save_ext != None:
        lx.eval("dialog.fileSaveFormat %s extension" % save_ext)
    if path is not None:
        lx.eval('dialog.result {%s}' % path)

    if init_dialog:
        try:
            lx.eval("dialog.open")
            return lx.eval("dialog.result ?")
        except:
            return None


def init_message(type, title, message):
    lx.eval('dialog.setup {%s}' % type)
    lx.eval('dialog.title {%s}' % title)
    lx.eval('dialog.msg {%s}' % message)
    lx.eval('dialog.open')


def set_bool_arg(arg_arr, index, arg_name, init_value):
    if arg_arr[index] == arg_name:
        if arg_arr[index + 1] != '0' and arg_arr[index + 1] != '1':
            init_message('error', arg_name, 'Illegal ' + arg_name + ' = ' + arg_arr[index + 1] + ' argument value')
            sys.exit()
        else:
            return arg_arr[index + 1]
    else:
        return init_value


def set_float_arg(arg_arr, index, arg_name, init_value):
    if arg_arr[index] == arg_name:
        return arg_arr[index + 1]
    else:
        return init_value


def set_axis_arg(arg_arr, index, arg_name, init_value):
    if arg_arr[index] == arg_name:
        if arg_arr[index + 1] != 'X' and arg_arr[index + 1] != 'Y' and arg_arr[index + 1] != 'Z':
            init_message('error', arg_name, 'Illegal ' + arg_name + ' = ' + arg_arr[index + 1] + ' argument value')
            sys.exit()
        else:
            return arg_arr[index + 1]
    else:
        return init_value


def init_arg():
    global triple_sw
    global resetPos_sw
    global rotAngle
    global scaleAmount
    global smoothAngle
    global exportEach
    global exportHierarchy
    global scanFiles
    global upAxis

    args = lx.args()
    argCount = len(args)

    for a in xrange(0, argCount - 1):
        if a % 2 == 0:

            triple_sw = set_bool_arg(args, a, 'triple', triple_sw)
            resetPos_sw = set_bool_arg(args, a, 'resetPos', resetPos_sw)
            exportEach = set_bool_arg(args, a, 'exportEach', exportEach)
            exportHierarchy = set_bool_arg(args, a, 'exportHierarchy', exportHierarchy)
            scanFiles = set_bool_arg(args, a, 'scanFiles', scanFiles)

            rotAngle = set_float_arg(args, a, 'rotAngle', rotAngle)
            scaleAmount = set_float_arg(args, a, 'scaleAmount', scaleAmount)
            smoothAngle = set_float_arg(args, a, 'smoothAngle', smoothAngle)

            upAxis = set_axis_arg(args, a, 'smoothAngle', upAxis)


def flow():
    init_arg()

    if scanFiles == '0':  # export selected mesh in the scene
        if userSelectionCount == 0:
            init_message('error', 'No item selected', 'Select at least one item')
            sys.exit()

        if exportEach == '1':
            init_dialog("output")
        else:
            init_dialog("file_save")

        try:  # output folder dialog
            lx.eval('dialog.open')
        except:
            init_dialog('cancel')
        else:
            output_dir = lx.eval1('dialog.result ?')
            batch_export(output_dir)
    else:  # browse file to process

        init_dialog("input")
        try:  # mesh to process dialog
            lx.eval('dialog.open')
        except:
            init_dialog('cancel')
        else:
            files = lx.evalN('dialog.result ?')
            init_dialog("output")
            try:  # output folder dialog
                lx.eval('dialog.open')
            except:
                init_dialog('cancel')
            else:
                output_dir = lx.eval1('dialog.result ?')

                for f in files:
                    print "processing " + os.path.basename(f)
                    name = os.path.basename(f)
                    ext = os.path.splitext(name)[1]
                    name = os.path.splitext(name)[0]

                    lx.eval('loaderOptions.wf_OBJ false false Meters')
                    # lx.eval('loaderOptions.fbx false true true true true true true true false false true true true true 0')
                    lx.eval('!scene.open "%s" normal' % f)

                    # if ext == 'fbx'
                    lx.eval('select.itemType mesh')

                    lx.eval('item.name %s mesh' % name)
                    batch_export(output_dir)
                    lx.eval('!scene.close')

    init_message('info','Done', 'Operation completed !')


def batch_export(output_dir):
    init_arg()

    if upAxis != lx.eval('pref.value units.upAxis ?'):
        lx.eval('pref.value units.upAxis %s' % upAxis)

    if exportHierarchy == '1':
        lx.eval('user.value sceneio.fbx.save.exportType FBXExportSelectionWithHierarchy')
    else:
        lx.eval('user.value sceneio.fbx.save.exportType FBXExportSelection')

    # Grab the IDs of each foreground layer.
    layers = userSelection

    if exportEach == '1':  # Export each layer separately.

        for layer in layers:
            export_loop(output_dir, layer)
            clean_scene()

    else:  # Export all selected layers in one file.
        export_loop(output_dir, layers)
        clean_scene()


def duplicate_rename(layer_name):
    if exportEach == '1':
        lx.eval('item.duplicate false all:true')
        lx.eval('item.name %s mesh' % (layer_name + '_1'))
    else:
        for l in xrange(0, userSelectionCount):
            layer_name = lx.eval1('query layerservice layer.name ? %s' % userSelection[l])
            lx.eval('select.subItem %s set mesh' % userSelection[l])
            lx.eval('item.duplicate false all:true')
            lx.eval('item.name %s mesh' % (layer_name + '_' + str(l)))
        select_duplicate(layer_name)


def get_name(layer):
    if exportEach == '1':
        return lx.eval1('query layerservice layer.name ? %s' % layer)
    else:
        return os.path.splitext(lx.eval1('query sceneservice scene.name ? current'))[0]


def set_name(layer_name):
    if exportEach == '1':
        lx.eval('item.name %s mesh' % layer_name)
    else:

        lx.eval('select.itemType mesh')
        duplicate = lx.evalN('query layerservice layer.id ? fg')
        for l in duplicate:
            lx.eval('select.subItem %s set mesh' % l)
            current_name = lx.eval1('query layerservice layer.name ? current')
            current_name = current_name[:-2]
            lx.eval('item.name %s mesh' % current_name)
        lx.eval('select.itemType mesh')


def select_duplicate(layer_name):
    if exportEach == '1':
        lx.eval('select.item {%s} set' % (layer_name + '_1'))
    else:
        get_user_selection()
        for l in xrange(0, userSelectionCount):
            new_layer_name = lx.eval('query layerservice layer.name ? %s' % userSelection[l])
            if l == 0:
                lx.eval('select.item {%s} set' % (new_layer_name + '_' + str(l)))
            else:
                lx.eval('select.item {%s} add' % (new_layer_name + '_' + str(l)))
    if exportHierarchy == '1':
        lx.eval('select.itemHierarchy')


def get_user_selection():
    for l in xrange(0, userSelectionCount):
        if l == 0:
            lx.eval('select.subItem {%s} set mesh' % userSelection[l])
        else:
            lx.eval('select.subItem {%s} add mesh' % userSelection[l])


def export_selection(output_path, layer_name):
    processing_log(layer_name)

    lx.eval('scene.new')
    newScene = lx.eval('query sceneservice scene.index ? current')
    lx.eval('select.itemType mesh')
    lx.eval('!!item.delete')
    lx.eval('scene.set %s' % sceneIndex)
    select_duplicate(layer_name)
    lx.eval('!layer.import %s {} true true false position:0' % newScene)
    lx.eval('scene.set %s' % newScene)
    set_name(layer_name)

    # Export to FBX.
    lx.eval('!scene.saveAs "%s" fbx false' % output_path)

    lx.eval('scene.close')

    lx.eval('scene.set %s' % sceneIndex)
    select_duplicate(layer_name)

    lx.eval('!!item.delete')


def export_loop(output_dir, layer):
    # Get the layer name.
    layer_name = get_name(layer)

    if exportEach == '1':
        # write the export path from the name.
        output_path = os.path.join(output_dir, layer_name + '.fbx')
        # Select only the mesh item.
        lx.eval('select.subItem %s set mesh' % layer)
    else:
        output_path = output_dir
        get_user_selection()

    if exportHierarchy == '1':
        lx.eval('select.itemHierarchy')

    duplicate_rename(layer_name)

    # Set Vertex normal
    if smoothAngle_sw == '1':
        lx.eval('vertMap.normals vert_normals false {%s}' % smoothAngle)

    if triple_sw == '1':
        lx.eval('poly.triple')

    if resetPos_sw == '1':
        lx.eval('transform.reset translation')

    if scaleAmount != '1':
        lx.eval('transform.freeze scale')
        lx.eval('transform.channel scl.X %s' % scaleAmount)
        lx.eval('transform.channel scl.Y %s' % scaleAmount)
        lx.eval('transform.channel scl.Z %s' % scaleAmount)
        lx.eval('transform.freeze scale')

    if rotAngle != '0':
        lx.eval('transform.channel rot.X "%s"' % rotAngle)
        lx.eval('transform.freeze rotation')
        lx.eval('edgesmooth.update')

    # Export to FBX.
    export_selection(output_path, layer_name)


def clean_scene():
    # get_user_selection()

    # Put the user's original FBX Export setting back.
    lx.eval('user.value sceneio.fbx.save.exportType %s' % fbx_export_setting)

    if upAxis != iUpAxis:
        lx.eval('pref.value units.upAxis %s' % iUpAxis)


def print_log(message):
    lx.out("BATCH_EXPORT : " + message)


def processing_log(message):
    print_log("Processing_File : " + message)


flow()