from os import listdir, get_terminal_size, system, name
from os.path import isfile, join, exists, splitext, sep, getsize, getmtime
import string
import keyboard
from threading import Timer
import platform
import time

OPERATING_SYS = platform.system()

WINDOW_WIDTH = get_terminal_size().columns
MAIN_WINDOW_WIDTH = round(WINDOW_WIDTH*0.85)
LEFT_WINDOW_WIDTH = WINDOW_WIDTH - MAIN_WINDOW_WIDTH

WINDOW_HEIGHT = get_terminal_size().lines - 2

HIGHLIGHT_PREFIX = '\033[95m'
RED = '\033[91m'
GRAY = '\033[90m'
END_COLOR = '\033[0m'

def run_file_with_default_app(file_path):
    start_command = ""
    match OPERATING_SYS:
        case "Linux":
            start_command = "xdg-open"
            file_path = "'" + file_path + "'"
        case "Windows":
            # for some reason surrounding the whole path in quotes doesn't work if the path has spaces
            # This method of only surrounding the offending part does though. Ex: D:\cool stuff\ -> D:\"cool stuff"\
            start_command = "start"
            file_path = file_path.split('\\')
            new_path = []
            for part in file_path:
                if ' ' in part:
                    part = '"' + part + '"'
                new_path.append(part)
            file_path = '\\'.join(new_path)
        case "Darwin":
            '"' + file_path + '"'
            start_command = "open"
    app.send_message("Running command: " + start_command + ' ' + file_path)
    system(start_command + ' ' + file_path)

def limit_string_to_len(string, length):
    return string[:-(3 + len(string) - length)] + ('  ' if string[-1] == ' ' else '… ')

def get_bottom_most_dir(dir):
    active_dir = dir
    while isinstance(active_dir, Dir) and active_dir.contents:
        active_dir = active_dir.contents[-1]
    return active_dir

def format_file_size(size_in_bytes):
    unit = ""
    # 0 - 999 B
    if size_in_bytes < 1000:
        unit = ""
    # 1 - 9,999 KB
    elif size_in_bytes < 1000**2 * 10:
        unit = "K"
        size_in_bytes = round(size_in_bytes/1000)
    # 1 - 999 MB
    elif size_in_bytes < 1000**2 * 999:
        unit = "M"
        size_in_bytes = round(size_in_bytes/1000**2, 1)
    # 1.. GB
    else:
        unit = "G"
        size_in_bytes = round(size_in_bytes/1000**3, 2)
    return "{:,}".format(size_in_bytes) + " " + unit + "B"

def set_width_consts():
    # TODO: change app truncate sizes when window changes
    WINDOW_WIDTH = get_terminal_size().columns
    MAIN_WINDOW_WIDTH = round(WINDOW_WIDTH*0.75)
    LEFT_WINDOW_WIDTH = WINDOW_WIDTH - MAIN_WINDOW_WIDTH
    WINDOW_HEIGHT = get_terminal_size().lines - 2

class Nav:
    current_drive = 0
    selected_folder = None
    navigating_files_view = False
    CYCLE = 5
    VIEW = 4
    CLOSE = 3
    OPEN = 2
    UP = 1
    DOWN = 0

    @staticmethod
    def navigate(nav_option):
        match nav_option:
            # navigating down
            case 0:
                # if the dir has contents then set selected to the first content
                if isinstance(Nav.selected_folder, Dir) and Nav.selected_folder.contents:
                    Nav.selected_folder = Nav.selected_folder.contents[0]

                # if the dir has a parent
                elif Nav.selected_folder.parent:
                    # if it's the last content in a dir
                    if Nav.selected_folder.parent[1] + 1 == len(Nav.selected_folder.parent[0].contents):
                        # if we are in files navigation mode
                        if Nav.navigating_files_view:
                            Nav.selected_folder = Nav.selected_folder.parent[0].contents[0]
                        # if the parent is not a drive
                        elif Nav.selected_folder.parent[0].parent:
                            if Nav.selected_folder.parent[0].parent and len(Nav.selected_folder.parent[0].parent[0].contents) == 1:
                                Nav.selected_folder = Nav.selected_folder.parent[0].parent[0].parent[0].contents[Nav.selected_folder.parent[0].parent[0].parent[1] + 1]
                            else:
                                Nav.selected_folder = Nav.selected_folder.parent[0].parent[
                                    0].contents[(Nav.selected_folder.parent[0].parent[1] + 1) % len(Nav.selected_folder.parent[0].parent[
                                        0].contents)]
                        # if navigating up shoud select a drive
                        else:
                            Nav.current_drive = (Nav.current_drive + 1) % len(drives)
                            Nav.selected_folder = drives[Nav.current_drive]
                    else:
                        # progress through a dir as usual
                        print(len(Nav.selected_folder.parent[0].contents),Nav.selected_folder.parent[1] + 1 )
                        Nav.selected_folder = Nav.selected_folder.parent[0].contents[
                            Nav.selected_folder.parent[1] + 1]
                else:
                    # cycle through drives
                    Nav.current_drive = (Nav.current_drive + 1) % len(drives)
                    Nav.selected_folder = drives[Nav.current_drive]
            # navigating up
            case 1:
                # if the dir has a parent
                if Nav.selected_folder.parent:
                    # if the above dir has contents then set selected to the last content of the dir
                    if isinstance(above_dir := Nav.selected_folder.parent[0].contents[(
                            Nav.selected_folder.parent[1] - 1) % len(Nav.selected_folder.parent[0].contents)], Dir) and above_dir.contents:
                        # if it's the only content in the parent
                        if len(Nav.selected_folder.parent[0].contents) == 1:
                            Nav.selected_folder = Nav.selected_folder.parent[0]
                        else:
                            Nav.selected_folder = get_bottom_most_dir(above_dir)
                    # if it's the first content in a dir
                    elif not Nav.selected_folder.parent[1]:
                        # if we are in files navigation mode
                        if Nav.navigating_files_view:
                            Nav.selected_folder = Nav.selected_folder.parent[0].contents[-1]
                        # if the parent is not a drive
                        elif Nav.selected_folder.parent[0].parent:
                            Nav.selected_folder = Nav.selected_folder.parent[0].parent[
                                0].contents[(Nav.selected_folder.parent[0].parent[1]) % len(Nav.selected_folder.parent[0].parent[
                                    0].contents)]
                        # if navigating up shoud select a drive
                        else:
                            Nav.selected_folder = drives[Nav.current_drive]
                    else:
                        # progress through a dir as usual
                        Nav.selected_folder = Nav.selected_folder.parent[0].contents[
                            Nav.selected_folder.parent[1] - 1]
                else:
                    # if the above drive has contents
                    if (above_dir := drives[ (Nav.current_drive - 1) % len(drives)]).contents:
                        Nav.selected_folder = above_dir.contents[-1]
                        Nav.current_drive = (
                            Nav.current_drive - 1) % len(drives)
                    else:
                        # cycle through drives
                        Nav.current_drive = (Nav.current_drive - 1) % len(drives)
                        Nav.selected_folder = drives[Nav.current_drive]
            # nav right
            case 2:
                if isinstance(Nav.selected_folder, Dir):
                    if not Nav.navigating_files_view:
                        try:
                            openDir(Nav.selected_folder, folders_only=True)
                            App.truncate_bottom += len(Nav.selected_folder.contents)
                        except PermissionError:
                            app.send_message(
                                RED + f'Please re-run with elevated privilages to access {Nav.selected_folder.name}' + END_COLOR)
                else:
                    Nav.selected_folder.open()
            # nav left
            case 3:
                if not Nav.navigating_files_view:
                    if isinstance(Nav.selected_folder, Dir) and Nav.selected_folder.contents:
                        App.truncate_bottom -= len(Nav.selected_folder.contents)
                        closeDir(Nav.selected_folder)
                    elif Nav.selected_folder.parent:
                        Nav.selected_folder = Nav.selected_folder.parent[0]
            # spacebar to view
            case 4:
                if isinstance(Nav.selected_folder, Dir):
                    try:
                        App.open_folder = openDir(
                            Nav.selected_folder, return_copy=True)
                        if Nav.navigating_files_view:
                            Nav.selected_folder = App.open_folder.contents[0]
                    except PermissionError:
                        app.send_message(
                            RED + f'Please re-run with elevated privilages to access {Nav.selected_folder.name}' + END_COLOR)
                else:
                    Nav.selected_folder.open()
            # tab to cycle
            case 5:
                Nav.navigating_files_view = not Nav.navigating_files_view
                if Nav.navigating_files_view:
                    Nav.selected_folder = App.open_folder.contents[0]
                else:
                    Nav.selected_folder = drives[Nav.current_drive]
        app.render()

class ScrollView:
    def __init__(self, height, width) -> None:
        self.rows = []
        self.height = height
        self.offset = 0
        self.width = width

    def format(self):
        new_list = []

        # limit the rows to the correct ones that should display
        copy_rows = self.rows[self.offset:self.offset+self.height]

        for line in copy_rows:
            # remove highlighting from text
            make_highlighted = HIGHLIGHT_PREFIX in line
            line = line.replace(HIGHLIGHT_PREFIX, '').replace(END_COLOR, '')

            # force line to be the correct width unless it is the highlighted line
            line += ' ' * (self.width - len(line) - 1)
            if not make_highlighted:
                # don't truncate if the line is highlighted
                line = line[:self.width]

            # put highlighting back if necessary
            if make_highlighted:
                line = HIGHLIGHT_PREFIX + line + END_COLOR

            new_list.append(line)

        # force the correct height with empty space
        for _ in range(self.height - len(self.rows)):
            new_list.append(' ' * (self.width - 1))

        # set rows to the formatted list
        self.rows = new_list


    def join(self, other):
        new_list = []
        for index, row in enumerate(self.rows):
            make_highlighted = HIGHLIGHT_PREFIX in row
            row = row.replace(HIGHLIGHT_PREFIX, '').replace(END_COLOR, '')
            is_row_longer_than_normal = len(row) >= self.width
            if not make_highlighted:
                row = limit_string_to_len(row, self.width)
            if is_row_longer_than_normal and make_highlighted:
                new_list.append((HIGHLIGHT_PREFIX if make_highlighted else '') + row + (
                    END_COLOR if make_highlighted else '') + ' ' + other.rows[index][len(row) - self.width:])
            else:
                new_list.append((HIGHLIGHT_PREFIX if make_highlighted else '') + row + (
                    END_COLOR if make_highlighted else '') + '｜' + other.rows[index])

        return new_list


class Content:
    def __init__(self, name, path, depth=0, parent=None) -> None:
        self.name = name
        self.depth = depth
        self.path = path
        self.parent = parent
        self.last_modified = time.strftime(
            '%Y-%m-%d %H:%M', time.localtime(getmtime(self.path)))

    def __repr__(self) -> str:
        ret = '  ' * self.depth + f'{self.name}'
        if self is Nav.selected_folder:
            ret = HIGHLIGHT_PREFIX + ret + END_COLOR
        return ret

class Dir(Content):
    def __init__(self, name, path, contents=[], depth=0, parent=None) -> None:
        super().__init__(name, path, depth, parent)
        self.contents = contents

    def __repr__(self) -> str:
        return super().__repr__() + ('↴' if self.contents else '')

class File(Content):
    def __init__(self, name, path, extension, depth=0, parent=None) -> None:
        super().__init__(name, path, depth, parent)
        self.extension = extension
        self.size = format_file_size(getsize(self.path))

    def __repr__(self) -> str:
        ret = '  ' * self.depth + f'{self.name}' + self.extension
        if self is Nav.selected_folder:
            ret = HIGHLIGHT_PREFIX + ret + END_COLOR
        return ret

    def open(self):
        app.message_bar = self.path
        run_file_with_default_app(self.path)

class App:
    truncate_bottom = 0
    truncate_top = 0
    default_message = 'Left = Close dir/ go to parent dir, Right = open dir/ open file, Tab = cycle, Up/Down = navigate, Space = view dir'
    folder_view = ScrollView(WINDOW_HEIGHT, LEFT_WINDOW_WIDTH)
    files_view = ScrollView(WINDOW_HEIGHT, MAIN_WINDOW_WIDTH)
    open_folder = None
    dist_from_top = 0

    def __init__(self) -> None:
        self.message_bar = App.default_message
        App.open_folder = openDir(drives[0], return_copy=True)

    def send_message(self, message):
        self.message_bar = message
        Timer(5, self.reset_message).start()

    def reset_message(self):
        self.message_bar = App.default_message

    def render(self):
        # make sure everything is scaled to the terminal size
        set_width_consts()
        App.folder_view.width = LEFT_WINDOW_WIDTH
        App.files_view.width = MAIN_WINDOW_WIDTH
        App.folder_view.height = App.files_view.height = WINDOW_HEIGHT

        # clear terminal
        system('cls' if name == 'nt' else 'clear')

        # get lines for folder view
        App.folder_view.rows = flatten_list([render(d) for d in drives])

        # get lines for files view
        App.files_view.rows = render_files_view(App.open_folder)

        # offset view
        if Nav.navigating_files_view:
            dist_from_top = get_distance_from_top(App.files_view.rows)
            if WINDOW_HEIGHT <= dist_from_top - App.files_view.offset:
                App.files_view.offset = dist_from_top - WINDOW_HEIGHT + 1
            elif dist_from_top < App.files_view.offset:
                App.files_view.offset = dist_from_top - 1
        else:
            dist_from_top = get_distance_from_top(App.folder_view.rows)
            if WINDOW_HEIGHT <= dist_from_top - App.folder_view.offset:
                App.folder_view.offset = dist_from_top - WINDOW_HEIGHT + 1
            elif dist_from_top < App.folder_view.offset:
                App.folder_view.offset = dist_from_top

        # format folder and files views
        App.files_view.format()
        App.folder_view.format()

        # join folder and files views
        lines_to_render = App.folder_view.join(App.files_view)

        # print all the lines
        print('\n'.join(lines_to_render))

        # format the message bar and print it
        message_bar = ' ' * ((WINDOW_WIDTH - len(self.message_bar))//2) + self.message_bar
        print(message_bar)

def openDir(dir, return_copy=False, folders_only = False):
    if return_copy:
        dir = Dir(dir.name, dir.path, [], dir.depth, dir.parent)
    for index, content_name in enumerate(listdir(dir.path)):
        full_path = join(dir.path, content_name)
        if isfile(full_path):
            #if not folders_only:
            name, extension = splitext(content_name)
            dir.contents.append(File(name, full_path, extension, dir.depth + 1, parent=(dir, index)))
        else:
            dir.contents.append(
                Dir(content_name, full_path, contents=[], depth=dir.depth + 1, parent=(dir, index)))
    return dir

def get_distance_from_top(render_arr):
    counter = 0
    for line in render_arr:
        if HIGHLIGHT_PREFIX in line and END_COLOR in line:
            return counter
        counter += 1

def closeDir(dir):
    dir.contents = []

def flatten_list(arr):
    new_list = []

    for item in arr:
        if isinstance(item, list):
            new_list.extend(flatten_list(item))
        else:
            new_list.append(item)
    return new_list

def render(dir, ignore_top=False):
    rendered_txt = []

    #display the parent directory
    if not ignore_top:
        rendered_txt.append(repr(dir))
    for content in dir.contents:
        # print the child contents
        rendered_txt.append(repr(content))
        if isinstance(content, Dir) and len(content.contents):
            # if it's a directory with contents, print its contents too
            rendered_txt.append(
                render(content, ignore_top=True))
    return rendered_txt

def format_labels_to_screen_width(labels):
    ret = ''
    add_highlight = False
    for label in labels:
        if HIGHLIGHT_PREFIX in label:
            add_highlight = True
        label = label.replace(HIGHLIGHT_PREFIX, '').replace(END_COLOR, '')
        labels_len = MAIN_WINDOW_WIDTH//len(labels)
        label += ' ' * (labels_len - len(label))
        if len(label) > labels_len:
            label = limit_string_to_len(label, labels_len + 1)
        ret += label
    if add_highlight:
        return HIGHLIGHT_PREFIX + ret + END_COLOR
    return ret

def render_files_view(dir):
    rendered_txt = []

    # add labels
    rendered_txt.append(format_labels_to_screen_width(["Name", "Date Modified", "Type", "Size"]))

    for content in dir.contents:
        # print the child contents
        rendered_txt.append(format_labels_to_screen_width([repr(content).lstrip(' '),
                                           content.last_modified,
                                           content.extension if isinstance(content, File) else '',
                                           content.size if isinstance(content, File) else '']))
    return rendered_txt

possible_drives = string.ascii_uppercase
drives = [
    Dir(f'{drive}:', f'{drive}:' + sep, contents=[]) for drive in possible_drives if exists(f'{drive}:')]
Nav.selected_folder = drives[0]
keyboard.on_press_key("down", lambda _ : Nav.navigate(Nav.DOWN))
keyboard.on_press_key("up", lambda _: Nav.navigate(Nav.UP))
keyboard.on_press_key("left", lambda _: Nav.navigate(Nav.CLOSE))
keyboard.on_press_key("right", lambda _: Nav.navigate(Nav.OPEN))
keyboard.on_press_key("space", lambda _: Nav.navigate(Nav.VIEW))
keyboard.on_press_key("tab", lambda _: Nav.navigate(Nav.CYCLE))

app = App()
app.render()

keyboard.wait()
