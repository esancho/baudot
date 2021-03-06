#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import logging
import tempfile
from threading import Thread

import gtk
import gio
import gobject
from path import path
from pkg_resources import ResourceManager

from core import CharsetConverter
from widget import FileFolderChooser

# globals
VERSION = "0.1"
logging.basicConfig()
LOG = logging.getLogger("baudot_gui")
LOG.setLevel(logging.DEBUG)
CONVERTER = CharsetConverter()
GLADE_PATH = path(ResourceManager().resource_filename("baudot.gui", "glade"))

gobject.threads_init()

class App(object):

    def __init__(self):
        self.win = MainWindow()

    def start(self):
        self.win.show()
        gtk.main()


class MainWindow(object):

    def __init__(self, testing=False):
        self._testing = testing
        builder = gtk.Builder()
        builder.add_from_file(GLADE_PATH / "window.glade")
        self.win = builder.get_object("window")
        self.win_box = builder.get_object("winVBox")
        self.dst_cmb = builder.get_object("dstCmb")
        self.dst_chooser = builder.get_object("dstFileChooser")
        self.add_action = builder.get_object("addAction")
        self.remove_action = builder.get_object("removeAction")
        self.remove_all_action = builder.get_object("removeAllAction")
        self.edit_charset_action = builder.get_object("editCharsetAction")
        self.convert_action = builder.get_object("convertAction")
        self.charset_cmb = builder.get_object("charsetCmb")
        self.file_view = builder.get_object("fileView")
        self.info_area = gtk.VBox()
        self.info_area.set_visible(True)
        self.win_box.pack_start(self.info_area, False)
        self.win_box.reorder_child(self.info_area, 3)
        builder.connect_signals(self)

        self.fm = FileManager()
        self.fm.store.connect("row_deleted", self.on_row_deleted)
        self.fm.store.connect("row_inserted", self.on_row_inserted)

        self.selection = self.file_view.get_selection()
        self.selection.connect('changed', self.on_selection_changed)
        self.file_view.set_model(self.fm.store)

        combo_from_strings(CONVERTER.get_encodings(),
                           self.charset_cmb, "UTF-8")

    def show(self):
        self.win.set_visible(True)
        self.win.show()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_row_inserted(self, model, tree_path, data=None):
        enabled = len(model) > 0
        self.convert_action.set_sensitive(enabled)
        self.remove_all_action.set_sensitive(enabled)

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_row_deleted(self, model, tree_path, data=None):
        enabled = len(model) > 0
        self.convert_action.set_sensitive(enabled)
        self.remove_all_action.set_sensitive(enabled)

    def on_selection_changed(self, selection):
        (model, it) = selection.get_selected()
        if it is None:
            self.remove_action.set_sensitive(False)
            self.edit_charset_action.set_sensitive(False)
        else:
            self.remove_action.set_sensitive(True)
            entry = FileEntry.from_iter(model, it)
            self.edit_charset_action.set_sensitive(entry.filepath.isfile())

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_convertAction_activate(self, data=None):
        dst_charset = self.charset_cmb.get_active_text()
        copy_to = None
        if self.dst_cmb.get_active() == 1:
            copy_to = self.dst_chooser.get_filename()
        cmd = self.fm.convert(dst_charset, copy_to)
        def on_command_started(cmd):
            box = ConvertInfoBox(cmd)
            self.info_area.add(box)
        cmd.connect("command-started", on_command_started)
        cmd.start()
        if self._testing:
            cmd.join()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_addAction_activate(self, data=None):
        chooser = FileFolderChooser()
        if chooser.run() == gtk.RESPONSE_OK:
            files = chooser.get_filenames()
            gobject.idle_add(chooser.destroy)
            for a_file in files:
                cmd = self.fm.add(a_file)
                def on_command_started(cmd):
                    box = AddFileInfoBox(cmd)
                    self.info_area.add(box)
                cmd.connect("command-started", on_command_started)
                cmd.start()
                if self._testing:
                    cmd.join()                
        else:
            chooser.destroy()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_removeAction_activate(self, data=None):
        (model, it) = self.selection.get_selected()
        model.remove(it)

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_editCharsetAction_activate(self, data=None):
        (model, it) = self.selection.get_selected()
        entry = FileEntry.from_iter(model, it)
        dialog = CharsetChooser(entry.filepath, entry.charset)
        if dialog.run() == gtk.RESPONSE_APPLY:
            entry.charset = dialog.get_selected_charset()
            entry.save(model, it)
        dialog.destroy()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_removeAllAction_activate(self, data=None):
        self.fm.clear()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_aboutMenuItem_activate(self, widget, data=None):
        about = gtk.AboutDialog()
        about.set_program_name("Baudot")
        about.set_version(VERSION)
        about.set_copyright("© 2011 - Esteban Sancho")
        about.set_comments("Baudot is an easy to use tool for converting" +
                           " between charsets")
        about.set_website("http://github.com/Tiptop/baudot")
        about.run()
        about.destroy()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_dstCmb_changed(self, widget, data=None):
        self.dst_chooser.set_sensitive(widget.get_active() == 1)

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_quitMenuItem_activate(self, widget, data=None):
        gtk.main_quit()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()
        

class FileEntry(object):

    def __init__(self, filepath=None, icon=None, filename=None,
                 size=None, description=None, charset=None):
        self.filepath = path(filepath)
        self.icon = icon
        self.filename = filename
        self.size = size
        self.description = description
        self.charset = charset

    def to_list(self):
        return (self.filepath, self.icon, self.filename, self.size,
                    self.description, self.charset)

    def save(self, model, it):
        model.set_value(it, 0, self.filepath)
        model.set_value(it, 1, self.icon)
        model.set_value(it, 2, self.filename)
        model.set_value(it, 3, self.size)
        model.set_value(it, 4, self.description)
        model.set_value(it, 5, self.charset)

    @staticmethod
    def from_row(row):
        filepath, icon, filename, size, description, charset = row
        return FileEntry(filepath, icon, filename, size, description, charset)

    @staticmethod
    def from_iter(model, it):
        row = list()
        for i in range(model.get_n_columns()):
            row.append(model.get_value(it, i))
        return FileEntry.from_row(row)


class FileManager(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)
        # path, icon, filename, size, description, charset
        self.store = gtk.TreeStore(gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        self._stop = False

    def __len__(self):
        return len(self.store)

    def clear(self):
        self.store.clear()

    def convert(self, dst_charset, copy_to=None):
        return ConvertCommand(self.store, dst_charset, copy_to)

    def add(self, filepath):
        return AddFileCommand(self.store, filepath)

class FileCommand(gobject.GObject, Thread):
    
    __gsignals__ = {
        'command-started': (gobject.SIGNAL_RUN_LAST, 
                           gobject.TYPE_NONE, 
                           ()),
        'command-finished': (gobject.SIGNAL_RUN_LAST, 
                           gobject.TYPE_NONE, 
                           ()),
        'command-aborted': (gobject.SIGNAL_RUN_LAST, 
                           gobject.TYPE_NONE, 
                           (gobject.TYPE_STRING, )),
        'progress-updated': (gobject.SIGNAL_RUN_LAST, 
                           gobject.TYPE_NONE, 
                           (gobject.TYPE_INT,)),
    }
    
    def __init__(self, store):
        gobject.GObject.__init__(self)
        Thread.__init__(self)
        self._stopped = False
        self.store = store
        
    def run(self):
        self.emit("command-started")
        self.execute()
        self.emit("command-finished")
    
    def stop(self):
        self._stopped = True
        
    def execute(self):
        raise Exception("Has to be implemented in child class")

    def search(self, filepath):
        filepath = path(filepath)

        def search(rows, filepath):
            if not rows:
                return None
            for row in rows:
                entry = FileEntry.from_row(row)
                if entry.filepath == filepath:
                    return row
                if filepath.startswith(entry.filepath):
                    result = search(row.iterchildren(), filepath)
                    if result:
                        return result
            return None
        
        return search(self.store, filepath)


class AddFileCommand(FileCommand):
    
    def __init__(self, store, filepath):
        super(AddFileCommand, self).__init__(store)
        self.filepath = path(filepath)
        self.total_files = self._count_files(filepath)
        self.added_files = 0
    
    def execute(self):
        if self.search(self.filepath):
            self.emit("command-aborted", self.filepath)
            return
        
        def add_file(filepath, parent):
            if self._stopped:
                return
    
            filename = filepath if parent is None else filepath.basename()
            
            if filepath.isdir():
                entry = FileEntry(filepath, gtk.STOCK_DIRECTORY, 
                                  filename, 0, "Folder")
                it = self.store.append(parent, entry.to_list())
                for d in sorted(filepath.dirs()):
                    add_file(d, it)
                for f in sorted(filepath.files()):
                    add_file(f, it)
                # remove empty or set size
                count = self.store.iter_n_children(it)
                if count > 0 or parent is None:
                    entry.size = "%d items" % count
                    entry.save(self.store, it)
                else:
                    self.store.remove(it)
            else:
                mime = self._get_mime_type(filepath)
                # only allow text files
                if "text" in mime.lower():
                    match = CONVERTER.detect_encoding(filepath)
                    charset = match.charset if match else None
                    if filepath.size < 1000:
                        size = "%d B" % filepath.size
                    elif filepath.size < 1000000:
                        size = "%.2f KB" % (filepath.size / 1000.0)
                    else:
                        size = "%.2f MB" % (filepath.size / 1000000.0)
                    entry = FileEntry(filepath, gtk.STOCK_FILE, filename, size,
                                      mime, charset)
                    self.store.append(parent, entry.to_list())
            self.added_files += 1
            progress = float(self.added_files) * 100 / self.total_files
            self.emit("progress-updated", progress)
            
        add_file(self.filepath, None)
        
    def _count_files(self, filepath):
        filepath = path(filepath)
        count = 1
        if filepath.isdir():
            walker = filepath.walk()
            try:
                while walker.next():
                    count += 1
            except StopIteration:
                pass
        return count

    def _get_mime_type(self, filepath):
        info = gio.File(filepath).query_info("standard::content-type")
        return info.get_content_type()
    

class ConvertCommand(FileCommand):
    
    def __init__(self, store, charset, copy_to):
        super(ConvertCommand, self).__init__(store)
        self.charset = charset
        self.copy_to = path(copy_to) if copy_to else None
        self.total_files = self._count_files()
        self.converted_files = 0
    
    def execute(self):
        def convert(rows, base_path):
            if not rows:
                return
            for row in rows:
                entry = FileEntry.from_row(row)
                src_file = dst_file = entry.filepath
                if src_file.isfile():
                    src_charset = entry.charset
                    if self.copy_to:
                        if not base_path:
                            base_path = src_file.dirname()
                        dst_file = self.copy_to / src_file[len(base_path) + 1:]
                    if dst_file.exists():
                        self._create_backup(dst_file)
                    fd, filename = tempfile.mkstemp(prefix="baudot")
                    os.close(fd)
                    tmp_file = path(filename)
                    LOG.debug("Saving file %s with charset %s" %
                              (tmp_file, self.charset))
                    CONVERTER.convert_encoding(src_file,
                                                  tmp_file,
                                                  src_charset,
                                                  self.charset)
                    tmp_file.copyfile(dst_file)
                    tmp_file.remove()
                    self.converted_files += 1
                    progress = float(self.converted_files) * 100 / self.total_files
                    self.emit("progress-updated", progress)
                else: # isdir
                    children = row.iterchildren()
                    if self.copy_to:
                        if not base_path:
                            base_path = src_file
                        else:
                            dst_file = self.copy_to / src_file[len(base_path) + 1:]
                            if not dst_file.exists():
                                dst_file.makedirs()
                    convert(children, base_path)
        convert(self.store, None)

    def _count_files(self):
        def _count(rows):
            if not rows:
                return 0
            count = 0
            for row in rows:
                entry = FileEntry.from_row(row)
                if entry.filepath.isfile():
                    count += 1
                else:
                    count += _count(row.iterchildren())
            return count
        
        return _count(self.store)

    def _create_backup(self, filepath):
        filepath.copy2(filepath + "~")


class InfoBox(gtk.EventBox):

    def __init__(self):
        super(InfoBox, self).__init__()
        
        color = gtk.gdk.color_parse("#ffffc8")
        self.modify_bg(gtk.STATE_NORMAL, color)


class ErrorInfoBox(InfoBox):
    
    def __init__(self, message):
        super(ErrorInfoBox, self).__init__()
        
        main_box = gtk.VBox()
        main_box.set_border_width(5)

        upper_box = gtk.HBox(spacing=5)
        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_BUTTON)
        upper_box.pack_start(icon, False, False, 5)
        self.label = gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_markup(message)
        upper_box.pack_start(self.label, False)
        main_box.pack_start(upper_box, False)
        
        alignment = gtk.Alignment(xalign=1, yalign=0.5, xscale=0.0, yscale=0.0)
        close_btn = gtk.Button(stock=gtk.STOCK_CLOSE)
        close_btn.connect("clicked", self.on_close_btn_clicked)
        alignment.add(close_btn)
        main_box.pack_start(alignment, expand=False)
        
        self.add(main_box)
        self.show_all()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_close_btn_clicked(self, widget, data=None):
        gobject.idle_add(self.parent.remove, self)


class AddFileInfoBox(InfoBox):
    
    def __init__(self, cmd):
        super(AddFileInfoBox, self).__init__()
        
        cmd.connect("progress-updated", self.on_progress_updated)
        cmd.connect("command-aborted", self.on_command_aborted)
        cmd.connect("command-finished", self.on_command_finished)
        self.cmd = cmd
        
        main_box = gtk.VBox()
        main_box.set_border_width(5)

        upper_box = gtk.HBox(spacing=5)
        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        upper_box.pack_start(icon, False, False, 5)
        self.label = gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_markup("Adding <b>%s</b>" % cmd.filepath)
        upper_box.pack_start(self.label, False)
        main_box.pack_start(upper_box, False)
        
        lower_box = gtk.HBox(spacing=5)
        alignment = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=1, yscale=0.0)
        self.progress_bar = gtk.ProgressBar()
        alignment.add(self.progress_bar)
        lower_box.pack_start(alignment, expand=True, fill=True)
        cancel_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_btn.connect("clicked", self.on_close_btn_clicked)
        lower_box.pack_start(cancel_btn, False)
        main_box.pack_start(lower_box, False)
        
        self.add(main_box)
        self.show_all()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_command_aborted(self, cmd, filepath):
        box = ErrorInfoBox("%s is already in workspace" % filepath)
        self.parent.add(box)
        
    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_command_finished(self, cmd):
        gobject.idle_add(self.parent.remove, self)
        
    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_progress_updated(self, cmd, progress):
        gobject.idle_add(self.progress_bar.set_value, progress)
    
    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_close_btn_clicked(self, widget, data=None):
        self.cmd.stop()
        gobject.idle_add(self.parent.remove, self)
    

class ConvertInfoBox(InfoBox):
    
    def __init__(self, cmd):
        super(ConvertInfoBox, self).__init__()
        
        cmd.connect("progress-updated", self.on_progress_updated)
        cmd.connect("command-aborted", self.on_command_aborted)
        cmd.connect("command-finished", self.on_command_finished)
        self.cmd = cmd
        
        main_box = gtk.VBox()
        main_box.set_border_width(5)

        upper_box = gtk.HBox(spacing=5)
        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_CONVERT, gtk.ICON_SIZE_BUTTON)
        upper_box.pack_start(icon, False, False, 5)
        self.label = gtk.Label()
        self.label.set_use_markup(False)
        self.label.set_text("Converting all files in workspace")
        upper_box.pack_start(self.label, False)
        main_box.pack_start(upper_box, False)
        
        lower_box = gtk.HBox(spacing=5)
        alignment = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=1, yscale=0.0)
        self.progress_bar = gtk.ProgressBar()
        alignment.add(self.progress_bar)
        lower_box.pack_start(alignment, expand=True, fill=True)
        cancel_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_btn.connect("clicked", self.on_close_btn_clicked)
        lower_box.pack_start(cancel_btn, False)
        main_box.pack_start(lower_box, False)
        
        self.add(main_box)
        self.show_all()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_command_aborted(self, cmd, filepath):
        box = ErrorInfoBox("An error ocurred")
        self.parent.add(box)
        
    def on_command_finished(self, cmd):
        gobject.idle_add(self.parent.remove, self)
        
    def on_progress_updated(self, cmd, progress):
        gobject.idle_add(self.progress_bar.set_value, progress)
    
    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_close_btn_clicked(self, widget, data=None):
        self.cmd.stop()
        gobject.idle_add(self.parent.remove, self)
    

class CharsetChooser(object):

    def __init__(self, filepath, charset):
        filepath = path(filepath)
        self.data = filepath.bytes()

        builder = gtk.Builder()
        builder.add_from_file(GLADE_PATH / "charset_chooser.glade")
        self.dialog = builder.get_object("chooser")
        self.dialog.set_title(filepath.basename())
        text_view = builder.get_object("textView")
        self.text_buffer = text_view.get_buffer()
        self.charset_cmb = builder.get_object("encodingCmb")
        builder.connect_signals(self)

        combo_from_strings(self._get_charsets(self.data), 
                           self.charset_cmb, 
                           charset)
        self.set_data(charset)

    def run(self):
        response = self.dialog.run()
        return gtk.RESPONSE_APPLY if response == 1 else gtk.RESPONSE_CLOSE

    def get_selected_charset(self):
        model = self.charset_cmb.get_model()
        return model.get_value(self.charset_cmb.get_active_iter(), 0)

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def on_encodingCmb_changed(self, widget, data=None):
        charset = self.get_selected_charset()
        self.set_data(charset)

    def destroy(self):
        self.dialog.destroy()

    def set_data(self, charset):
        try:
            text = unicode(self.data, charset)
            self.text_buffer.set_text(text)
        except ValueError, e:
            gtk_error_msg(self.dialog, str(e))

    def _get_charsets(self, data):
        good = list()
        for charset in CONVERTER.get_encodings():
            try:
                unicode(data, charset)
                good.append(charset)
            except (ValueError, LookupError):
                pass
        return good

def gtk_error_msg(parent, message):
    md = gtk.MessageDialog(parent,
                           gtk.DIALOG_DESTROY_WITH_PARENT,
                           gtk.MESSAGE_ERROR,
                           gtk.BUTTONS_CLOSE,
                           message)
    md.set_title("Error")
    md.run()
    md.destroy()

def combo_from_strings(str_list, combo, default=None):
    '''Helper function to populate a combo with a list of strings
    '''
    store = gtk.ListStore(gobject.TYPE_STRING)
    index = -1
    for i in range(len(str_list)):
        store.append((str_list[i],))
        if index < 0 and str_list[i] == default:
            index = i
    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 0)
    combo.set_model(store)
    combo.set_active(index)

