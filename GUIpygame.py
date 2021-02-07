#!/usr/bin/python3
'''
GUIpygame.py 
A basic sprite-based GUI toolkit for pygame.

(Originally written for pygame 1.9.1 and Python 3.1, and also tested with
Python 2.6, under Windows Vista.  Starting with version 185, I'm using
pygame 1.9.2 and Python 3.2, and also testing with Python 2.7, under
Windows 7.)

This GUI toolkit makes it trivially easy to add basic GUI elements, like
buttons, menus, pop-up messages, etc., to any pygame program.  It does not
require changing the structure of your pygame program or its event loop.
The GUI elements are pygame sprites.

Two main classes are defined: Widget and WidgetGroup, plus several subclasses
of these two main classes, and a few additional globals.

Widget is a subclass of pygame's Sprite class, which adds features to define
GUI element sprites ("widgets" or "widget sprites") for things like labels,
menus, text-edit boxes, and forms.  Unlike plain pygame sprites, widgets can
generate pygame events to report results (such as button clicks) to the
application.

WidgetGroup is a subclass of pygame's OrderedUpdates group, specifically for
containing widgets.  A WidgetGroup can contain any number of widgets.

A widget always contains exactly one (possibly empty) WidgetGroup (named
.children), so widgets can be nested arbitrarily deeply within one another,
to create complex compound widgets (forms within forms, etc.).

Originally by Dave Burton
Burton Systems Software
http://www.burtonsys.com/email/


----------------( Copyright 2011-2012, by David A. Burton )----------------

This work is "lightly copyrighted" free software.  You may copy it and use
it without restriction.  If you copy it (with or without modification),
your only requirement is that the copies must retain this notice.

Additionally, you may incorporate portions or snippets of this work in
other works, without restriction, regardless of whether those other works
are copyrighted or uncopyrighted, and regardless of how they are licensed.
However, as a courtesy, I ask that you include the following notice in
any works which incorporate substantial portions of this work:

    Portions of this program were excerpted by permission from
    GUIpygame.py, which is free software written by Dave Burton
    http://www.burtonsys.com/email/

--------------------------------------------------------------------------
'''

# make Python 2.6 / 2.7 more compatible with Python 3
from __future__ import print_function, division  # We require Python 2.6 or later


__all__ = ['MOUSEBUTTONLEFT', 'MOUSEBUTTONRIGHT', 'WIDGETEVENT', 'vera',
           'partial_redraw_mode', 'screen_is_cleared', 'done_drawing',
           'wrap_in_border', 'button_up_color', 'button_dn_color',
           'Widget', 'WidgetGroup', 'Image', 'Label', 'SimpleButton', 'Button',
           'SimpleCheckbox', 'Checkbox', 'Menu', 'TextEditBox', 'InputBox',
           'Form', 'ScrollBar']

        # -- These classes are mainly for internal use: --
        # 'WrapperForm', 'BasicForm', 'CloseButton', 'SliderButton', 'Titlebar',


version_num = "1.0 "



import sys  #@UnusedImport
import os
import pygame
from pygame.locals import *  #@UnusedWildImport
# two constants that should be in pygame.locals, but aren't:
MOUSEBUTTONLEFT = 1
MOUSEBUTTONRIGHT = 3


# import inspect
# cmd_folder = os.path.dirname(os.path.abspath(__file__)) # DO NOT USE __file__ !!!
# __file__ fails if script is called in different ways on Windows
# __file__ fails if someone does os.chdir() before
# sys.argv[0] also fails because it doesn't not always contains the path
#cmd_folder = os.path.dirname(os.path.abspath(__file__))
#print('dbg: cmd_folder = "' + cmd_folder + '"  (from __file__)')
#cmd_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])
#print('dbg: cmd_folder = "' + cmd_folder + '"  (from inspect.getfile(inspect.currentframe()))')
#
# x = inspect.getfile(inspect.currentframe())
# x = os.path.realpath(x)
# print('dbg: x1 = ' + repr(x) )
#
# x = os.path.split(os.path.realpath(__file__))[0]
# print('dbg: x2 = ' + repr(x) )
#
# from nt import _getfinalpathname
# x = _getfinalpathname(x)
# print('dbg: x3 = ' + repr(x) )
#
# x = os.path.normpath(x)
# print('dbg: x4 = ' + repr(x) )



def rel2me(fname):
    '''Take a filename, and make it into an absolute path relative to the folder
    which contains this module (GUIpygame.py).
    '''
    thisdir = os.path.dirname(os.path.realpath(__file__))
    return os.path.realpath(os.path.normpath(os.path.join(thisdir, fname)))


pygame.init()  # if pygame was already initialized, this does nothing


# Global "dirty" flag -- set from anywhere to ensure the display gets updated.
# If you choose to use this, then you should reset it to False at the end of
# your event loop.
changed = True

# get the default mouse cursor (probably a diagonal arrow)
default_mouse_cursor = pygame.mouse.get_cursor()
# (size, hotspot, xormasks, andmasks) = default_mouse_cursor

# When a Widget changes the mouse cursor, saved_mouse_cursor is set to the old
# mouse cursor.  That is, it is set to the mouse cursor when the mouse is not
# over a widget that changes the mouse cursor.  But when no widget has changed
# the mouse cursor, this is None.
saved_mouse_cursor = None
widget_which_set_mouse_cursor = None
widget_being_dragged = None

# To "deglitch" the mouse cursor (and improve performance a bit), we don't
# usually set it until WidgetGroup.notify() is ready to return to the
# application after processing events.  Here's where we keep the new mouse
# cursor to which we intend to set it:
new_mouse_cursor = None
# WidgetGroup.notify() can go recursive, to pass events to child widgets.
# This counts the recursion depth, which we need to keep track of for a
# mouse cursor deglitch kludge.
WidgetGroup_notify_recursion_counter = 0


def deglitched_set_cursor_pt2():
    '''This function sets the actual mouse cursor from the saved (deferred)
    new_mouse_cursor.  This is called from WidgetGroup.notify() when it's
    about to return to the main application.
    '''
    global WidgetGroup_notify_recursion_counter, new_mouse_cursor
    if ( (0 == WidgetGroup_notify_recursion_counter) and
         (new_mouse_cursor is not None) ):
        if pygame.mouse.get_cursor() != new_mouse_cursor:
            pygame.mouse.set_cursor(*new_mouse_cursor)
        new_mouse_cursor = None

def deglitched_set_cursor(*mouse_cursor):
    '''Mouse cursor deglitch code -- avoids multiple spurious setting of the
    mouse cursor.  See also code in WidgetGroup.notify().
    '''
    global new_mouse_cursor
    new_mouse_cursor = mouse_cursor
    deglitched_set_cursor_pt2()

# some global colors
BLACK = (0,0,0)
BLUE = (0,0,200)
WHITE = (255,255,255)
menu_bgcolor = (240,240,240)  # very light grey
menu_hover_color = (224,237,243)  # light bluish-grey
button_up_color = (215,222,240)  # greyer bluish-grey
button_dn_color = (202,207,223)  # bluish-grey

# 11 point Vera is a good font for menus and button labels
try:
    vera = pygame.font.Font(rel2me('Vera.ttf'), 12)
except:
    print('Warning: could not load "Vera.ttf" -- text will be ugly!')
    vera = pygame.font.SysFont('arial,microsoftsansserif,courier', 13)


# Global WIDGETEVENT is the pygame event number we'll use for all events
# generated by widgets.  It is used both for sending results (clicks,
# entered text, etc.) from widgets back to the application, and for
# widget-to-widget communications.  It must be one of the pygame user event
# numbers.  If the program that uses this module doesn't like our default,
# it can change WIDGETEVENT to something else.
WIDGETEVENT = pygame.USEREVENT


#--------------[ Begin code for finding & handling overlaps ]--------------

# The usual case is that the display (or at least all the widgets on it) are
# fully redrawn each time thru the event/draw loop, so set full_redraws=True.
full_redraws = True

def partial_redraw_mode(partial=True):
    ''''If your app only partially redraws each time through the event/draw
    loop, then call partal_redraw_mode() to tell the GUI system that fact,
    and also call screen_is_cleared() whenever you clear the screen, so that
    the GUI system can know what widgets are being displayed on the screen.

    (If your app fully redraws the screen, or at least all the displayed
    widgets, each time through the event/draw loop, then you can ignore all
    this, because the GUI system will keep track of it all automatically.)
    '''
    global full_redraws
    full_redraws = not partial

def screen_is_cleared():
    '''If partial_redraw_mode() has been called, then the application should
    call screen_is_cleared() whenever it clears the screen, before drawing any
    widgets onto it.
    '''
    global drawn_sprites, sorted_draw_list, draw_counter
    drawn_sprites = {}
    sorted_draw_list = []
    draw_counter = 0

# To determine which overlapping widget is on top, we need to know the order
# in which they were drawn.  To determine that, the first thing we must
# know is the order in which the top-level sprites were drawn.  That's what
# these three globals are for, as well as the note_draws() and done_drawing()
# functions.
drawn_sprites = {}
sorted_draw_list = []
draw_counter = 0
is_drawing = False
# is_drawing gets set True when WidgetGroup.draw is called, and we start
# filling in drawn_sprites.  When we're done drawing, is_drawing is set to
# False, and the next time WidgetGroup.draw is called drawn_sprites is reset
# to empty and draw_counter is reset to zero.  Each sprite gets an entry in
# drawn_sprites containing the index number with which it was last drawn.
# (So the if widgetx is the 3rd widget drawn, then drawn_sprites[widgetx]=3.)
# Last, sorted_draw_list gets the list of drawn widgets in sorted order.

def done_drawing():
    '''The application could call this explicitly when done drawing widgets
    (either just before or just after calling pygame.display.update), or it
    can just rely on this being called by WidgetGroup.notify().
    '''
    global is_drawing, sorted_draw_list
    if is_drawing:
        sorted_draw_list = sort_draw_list()
        # print('dbg: top-level widgets are:' + ', '.join([repr(w) for w in sorted_draw_list]))
    is_drawing = False

def note_draws(sprites):
    '''Called by WidgetGroup.draw to note the order in which the top-level
    widgets were drawn onto the display.
    '''
    global drawn_sprites, sorted_draw_list, draw_counter, is_drawing
    if not is_drawing:
        if full_redraws:
            screen_is_cleared()
        is_drawing = True
    for sprite in (sprites):
        draw_counter += 1
        drawn_sprites[sprite] = draw_counter

def _drw_indx(sprite):
    return drawn_sprites[sprite]

def sort_draw_list():
    '''generate a chronologically-sorted list of drawn widgets, by sorting
    the keys of drawn_sprites according to the corresponding counter values.
    '''
    return sorted(drawn_sprites.keys(), key=_drw_indx)

# You might wonder why we don't just accumulate the list of drawn widgets into
# sorted_draw_list as they are drawn, by appending the widgets to the list.
# The answer is that it could end up with duplicates in the list if the
# application for some reason called WidgetGroup.draw more than once for
# a group, or if a widget was listed in more than one group.  Those aren't
# normal cases, but they shouldn't break our algorithm.

def younger_siblings(sprite):
    '''younger siblings are sprites painted after this one, which are either
    in the same .children list for a parent widget, or else which are, like
    this one, top-level sprites.
    '''
    if hasattr(sprite, 'parent') and (sprite.parent is not None):
        # get list of younger fellow children of the same parent widget
        result = sprite.parent.children.sprites_painted_after(sprite)
    elif sprite in drawn_sprites:
        # this is a top-level sprite, so get list of top-level sprites drawn after this one
        ndx = sorted_draw_list.index(sprite)
        result = sorted_draw_list[ndx+1:]
    else:
        result = []
    return result

#---------------[ End code for finding & handling overlaps ]---------------



#-------------[ Begin code with hard-coded GUI element sizes ]-------------

# GUIpygame.png is a file containing the images we need to draw various little graphics
pics = pygame.image.load(rel2me('GUIpygame.png'))

# borderless close button (just an 8x8 "X" on a 14x14 transparent background)
Xpic = pygame.Surface((14,14), SRCALPHA)
Xpic.blit(pics, (0,0), area=(0,0,14,14))
# GUIpygame.png also contains a pair of 14x14 non-transparent close buttons ("up"
# and "down" versions), but I'm not currently using them

CHECKBOXSIZE = 13  # check-boxes are 13x13 pixels
unchecked = pygame.Surface((13,13))
unchecked.blit(pics, (0,0), area=(42,0,13,13))  # unchecked checkbox w/ border
checked = pygame.Surface((13,13))
checked.blit(pics, (0,0), area=(55,0,13,13))  # checked checkbox w/ border

# The knurl-effect triangular draggable lower-right corner is 8x8 w/ transparent background
KNURLSIZE = 8
knurl = pygame.Surface((8,8), SRCALPHA)
knurl.blit(pics, (0,0), area=(68,0,8,8))

# scroll bars require six little icons
scroll_left = pygame.Surface((4,7), SRCALPHA)
scroll_left.blit(pics, (0,0), area=(76,0,4,7))
scroll_up = pygame.Surface((7,4), SRCALPHA)
scroll_up.blit(pics, (0,0), area=(80,0,7,4))
scroll_right = pygame.Surface((4,7), SRCALPHA)
scroll_right.blit(pics, (0,0), area=(87,0,4,7))
scroll_down = pygame.Surface((7,4), SRCALPHA)
scroll_down.blit(pics, (0,0), area=(91,0,7,4))
scroll_horizontal = pygame.Surface((9,7), SRCALPHA)  # 9x7 knurl for drag button
scroll_horizontal.blit(pics, (0,0), area=(98,0,9,7))
scroll_vertical = pygame.Surface((7,9), SRCALPHA)  # 7x9 knurl for drag button
scroll_vertical.blit(pics, (0,0), area=(107,0,7,9))

# scrollbar dimensions
SB_BORDER_1 = 1  # scrollbars have a 1 pixel border
SB_WIDTH_17 = 17  # scrollbars are 17 pixels wide
SB_ARROWSIZE_10 = 10  # the arrow buttons at each end of a scrollbar are 10 pixels long
SB_ENDCAPSIZE_11 = SB_ARROWSIZE_10 + SB_BORDER_1  # 1 pixel border + 10 pixel arrow button at each end
SB_CHANNEL_WIDTH_15 = SB_WIDTH_17 - (2 * SB_BORDER_1)  # buttons and slider are 15 pixels wide
# Note: the numbers are included in the names because the purpose of these
# symbols is documentation, not to let you change scrollbar dimensions.

# a titlebar dimension
TB_HEIGHT_21 = 21  # titlebars are 21 pixels high

# Four special mouse cursors used for resizing things.  Usage example:
#   pygame.mouse.set_cursor( *sizer_xy_mouse_cursor )
d_tuple, m_tuple = pygame.cursors.compile(pygame.cursors.sizer_x_strings, black='X', white='.')
sizer_x_mouse_cursor = ((24,16), (8,5), d_tuple, m_tuple)
d_tuple, m_tuple = pygame.cursors.compile(pygame.cursors.sizer_y_strings, black='X', white='.')
sizer_y_mouse_cursor = ((16,24), (5,9), d_tuple, m_tuple)
d_tuple, m_tuple = pygame.cursors.compile(pygame.cursors.sizer_xy_strings, black='X', white='.')
sizer_xy_mouse_cursor = ((24,16), (7,7), d_tuple, m_tuple)
sizer_yx_strings = [ x[12::-1]+x[13:] for x in pygame.cursors.sizer_xy_strings ]
# for x in sizer_yx_strings: print(x+'|')
d_tuple, m_tuple = pygame.cursors.compile(sizer_yx_strings, black='X', white='.')
sizer_yx_mouse_cursor = ((24,16), (7,7), d_tuple, m_tuple)

# for byMouse-resizeable widgets, the outer 4 pixels are draggable
SIZERWIDTH_4 = 4

#--------------[ End code with hard-coded GUI element sizes ]--------------



def _distance_squared(pt1, pt2):
    '''1 + square of the distance between two points.  The "1+" is so that
    the result is always greater than zero, which is convenient.
    '''
    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]
    return 1 + dx*dx + dy*dy;


def list_of_focusable_widgets_at_mouse(spritelist, pos):
    '''This is debug code'''
    result = []
    sprites = spritelist
    for widg in sprites:
        collides = widg.collidepoint(pos)
        if collides:
            if not widg.never_has_focus:
                result.append(widg)
            tmp = list_of_focusable_widgets_at_mouse(widg.children.sprites(), pos)  # recursion
            if tmp:
                result.extend(tmp)
    return result


def border_rects(widget):
    '''Returns an 8-element list, with each element a rect, for the corners
    and sides of a resizeable widget, in clockwise order:
      topleft, top, topright, right, bottomright, bottom, bottomleft, left.
    They delineate the borders which can be dragged.
    The corners are all 4-pixels square; the sides are 4-pixels thick.
    '''
    R = pygame.Rect
    wr = widget.rect
    W = SIZERWIDTH_4
    result = [
              R(wr.left, wr.top, W, W),                      # 0 = top-left
              R(wr.left+W, wr.top, wr.width-(2*W), W),       # 1 = top
              R(wr.right-W, wr.top, W, W),                   # 2 = top-right
              R(wr.right-W, wr.top+W, W, wr.height-(2*W)),   # 3 = right
              R(wr.right-W, wr.bottom-W, W, W),              # 4 = bottom-right
              R(wr.left+W, wr.bottom-W, wr.width-(2*W), W),  # 5 = bottom
              R(wr.left, wr.bottom-W, W, W),                 # 6 = bottom-left
              R(wr.left, wr.top+W, W, wr.height-(2*W))       # 7 = left
             ]
    return result

# the cursors used when resizing, indexed same way as border_rects()' result
resizer_cursors = [sizer_xy_mouse_cursor, sizer_y_mouse_cursor,
                   sizer_yx_mouse_cursor, sizer_x_mouse_cursor,
                   sizer_xy_mouse_cursor, sizer_y_mouse_cursor,
                   sizer_yx_mouse_cursor, sizer_x_mouse_cursor]

# resizer_names = ['topleft', 'top', 'topright', 'right', 'bottomright', 'bottom', 'bottomleft', 'left']


def check_for_resize_border(widget, pos):
    '''Return None if cursor is not over a border, else return an integer 0-7
    which can be used to index resizer_cursors.
    (Be careful to distinguish between None and 0!)
    '''
    result = None
    if widget.resizeable == 'byMouse':
        if widget.resizer_collidepoint(pos):
            # pos is over a border, but which one?
            borders = border_rects(widget)
            for i in range(8):
                if borders[i].collidepoint(pos):
                    result = i
                    break
    return result


def notify_all_widgets(ev):
    '''Do immediate notifcations, by calling all widgets' .notify methods'''
    for widg in sorted_draw_list:
        if hasattr(widg, 'notify'):
            widg.notify(ev)
    # alternately, we could post it to the event queue
    # pygame.event.post(ev)


class Widget(pygame.sprite.Sprite):
    '''A widget is a sprite that can receive pygame events via its notify() method.

    Unlike simpler sprites, some widgets can generate pygame events representing
    things like button or menu clicks, entered text, etc.

    Also, widgets can contain WidgetGroups of other widgets (as .children).

    Like regular pygame sprites, widgets always have widget.rect and
    widget.image attributes.  But widgets also have some additional attributes
    that regular pygame sprites lack:

        1. widget.Id  is an object (usually a string) to identify the widget,
           so that we can tell them apart.  It is shown by __repr__() to help
           make repr(widget) more meaningful, and when a widget generates
           a pygame event, the source widget's id gets passed along as an
           attribute of the event (so that, for example, the application can
           tell which button got clicked).

        2. widget.children  is a WidgetGroup containing a list of all the child
           widgets contained-in / used-by this widget.  Default is empty.

        3. widget.parent  is this widget's parent/container, if this widget
           is contained-in a parent widget, such as a Form.  Default is None.

        4. widget.relative_rect  is a pygame.Rect, similar to widget.rect.
           For "chid" widgets (widgets contained within another widget),
           widget.relative_rect.topleft is the main/master position, relative
           to the parent widget.  For top-level widgets, widget.relative_rect
           is ignored.

        5. widget.bgcolor  is the color of the opaque background, or None if
           the background is transparent.

        6. widget.use_this_mouse_cursor  is either None or else the desired
           mouse cursor to be shown when the mouse is over this widget.

        7. widget.never_has_focus  is True iff, when the mouse cursor is over
           this widget it means that its parent (or perhaps grandparent) is
           considered to still have the mouse focus.  (Except, however, that a
           child of this widget might have focus.)

        8. widget.draggable  can be set to True if you want the user to be able
           to drag the widget around with the mouse.

        9. widget.resizeable  can be set to True if, when the widget is on a
           WrapperForm, the widget should resize along with the wrapper.  Or
           it can be set to 'byMouse' if the widget can also be resized by
           dragging the borders with the mouse.  (You can also set minimum
           resize width and height as widget.min_width and widget.min_height.)

        10. widget.min_width & widget.min_height  specify the minimum width
           and height, respectively, for a resizeable widget.  (These are
           automatically set to something reasonable.)

        11. widget.hasmousefocus  is used by button and menu widgets, and is
           True when the mouse cursor is over the button.  (Other widgets can
           just leave this set to False.)

    A widget's size is widget.rect.size, just like other pygame sprites.
    (The update method copies widget.rect.size to widget.relative_rect.size.)
    However, its position can be determined in either of two ways.

    A top-level widget's position is widget.rect.topleft, just like for
    regular pygame sprites.

    But if the widget is a child of another widget, it is positioned by setting
    widget.relative_rect.topleft (with the position relative to the parent
    widget), instead of by setting widget.rect.topleft.  The parent widget's
    update method will calculate each child widget's widget.rect.topleft
    (absolute) position by adding the parent widget's position to the child
    widget's relative position.  Thus, for child widgets, the master/main
    postion is widget.relative_rect.topleft.
    '''
    def __init__(self, *groups):
        self.children = WidgetGroup()  # needed if this widget has other widgets as children
        self.relative_rect = pygame.Rect(0,0,0,0)  # needed if this widget is a child of another widget
        self.parent = None  # set to the parent if this widget has a parent
        if not hasattr(self, 'bgcolor'):  # the "if not hasattr..." is in case a subclass's __init_ already set it
            self.bgcolor = None  # color of the opaque background, if any
        if not hasattr(self, 'Id'):
            self.Id = 'aWidget'
        if not hasattr(self, 'never_has_focus'):
            self.never_has_focus = True
        if not hasattr(self, 'use_this_mouse_cursor'):
            self.use_this_mouse_cursor = None
        if not hasattr(self, 'draggable'):
            self.draggable = False
        if not hasattr(self, 'resizeable'):
            self.resizeable = False
        if not hasattr(self, 'min_width'):
            self.min_width = 2
        if not hasattr(self, 'min_height'):
            self.min_height = 2
        self.dragging = False
        self.resizing = False
        self.hasmousefocus = False
        pygame.sprite.Sprite.__init__(self, *groups)
        # Note: self.rect contains absolute coordinates (relative to the
        # display surface), so that notify() will work.
        #
        # self.relative_rect contains coordinates relative to the containing
        # (parent) widget, if this widget is a child of another widget.
        #
        # self.relative_rect.size is always just a copy of self.rect.size.
        #
        # self.rect.topleft is calculated as self.relative_rect.topleft +
        # self.parent.relative_rect.topleft, unless there is no parent.

    def notify(self, ev):
        '''Handle a pygame event, at least partially.

        This can be overridden by widgets which need to do more.

        If there are child widgets, this gives each of them a look at the
        event.  Also, it handles dragging for draggable widgets, and mouse
        cursor changes over (possibly overlapping) widgets, and dragging of
        borders and corners for resizeable widgets.

        Widgets that actually do something (as opposed to just containing
        other widgets) will override this with a method that examines the event,
        and returns True if the event has been handled completely by that widget
        (meaning that nothing else needs to examine the event).  Widgets which
        have child widgets also generally need to send the event to the
        children, like this method does, or else (more commonly) they can just
        invoke this superclass method to do so.
        '''
        global changed
        global saved_mouse_cursor, widget_which_set_mouse_cursor, widget_being_dragged
        done_drawing()  # sprite-drawing is done for now; we're getting events

        is_mouse_event = ( (ev.type == MOUSEBUTTONDOWN) or
                           (ev.type == MOUSEBUTTONUP) or
                           (ev.type == MOUSEMOTION) )
        is_left_button_press = ( (ev.type == MOUSEBUTTONDOWN) and
                                 (ev.button == MOUSEBUTTONLEFT) )
        is_left_button_release = ( (ev.type == MOUSEBUTTONUP) and
                                 (ev.button == MOUSEBUTTONLEFT) )

        # This is part of the code to implement resize
        over_resize_area = False  # true iff resizeable and mouse is over a border
        if is_mouse_event and (self.resizeable == 'byMouse') and (not self.dragging):
            if self.resizing:
                if is_left_button_release:
                    # done resizing
                    self.resizing = False
                elif ev.type == MOUSEMOTION:
                    if not ev.buttons[0]:
                        # button isn't down, so button-release was missed
                        self.resizing = False
                    else:
                        # resize it!
                        previous_x = self.previous_mouse_pos[0]
                        previous_y = self.previous_mouse_pos[1]
                        if self.which_border in [2,3,4]:
                            # right side or either right-hand corner
                            w_delta = ev.pos[0] - self.previous_mouse_pos[0]
                            if (self.rect.width + w_delta) < self.min_width:
                                # enforce minimum width
                                w_delta = self.min_width - self.rect.width
                            self.rect.width += w_delta
                            previous_x = self.previous_mouse_pos[0] + w_delta
                        if self.which_border in [0,6,7]:
                            # left side or either left-hand corner
                            w_delta = self.previous_mouse_pos[0] - ev.pos[0]
                            if (self.rect.width + w_delta) < self.min_width:
                                # enforce minimum width
                                w_delta = self.min_width - self.rect.width
                            self.rect.width += w_delta
                            self.rect.left -= w_delta
                            self.relative_rect.left -= w_delta
                            previous_x = self.previous_mouse_pos[0] - w_delta
                        if self.which_border in [4,5,6]:
                            # bottom or either lower corner
                            h_delta = ev.pos[1] - self.previous_mouse_pos[1]
                            if (self.rect.height + h_delta) < self.min_height:
                                # enforce minimum height
                                h_delta = self.min_height - self.rect.height
                            self.rect.height += h_delta
                            previous_y = self.previous_mouse_pos[1] + h_delta
                        if self.which_border in [0,1,2]:
                            # top or either top corner
                            h_delta = self.previous_mouse_pos[1] - ev.pos[1]
                            if (self.rect.height + h_delta) < self.min_height:
                                # enforce minimum height
                                h_delta = self.min_height - self.rect.height
                            self.rect.height += h_delta
                            self.rect.top -= h_delta
                            self.relative_rect.top -= h_delta
                            previous_y = self.previous_mouse_pos[1] - h_delta
                        self.previous_mouse_pos = (previous_x, previous_y)
                        # Do NOT resize image here, because .update tells that
                        # it got resized by noticing that the image is the
                        # wrong size, so it knows to resize child forms if
                        # this is a WrapperForm.
                        # # self._make_image_surface(self.rect.size, transparent=not self.bgcolor)
                        self.update()
                        changed = True
                    over_resize_area = True
            if (not self.resizing) and self.resizer_collidepoint(ev.pos):
                over_resize_area = True
                self.which_border = check_for_resize_border(self, ev.pos)
                assert(self.which_border is not None)
                if is_left_button_press:
                    self.resizing = True
                    self.previous_mouse_pos = ev.pos
                # but if MOUSEMOTION and we're already resizing, don't change self.which_border
            if over_resize_area:
                # change mouse cursor to appropriate resizer, if it isn't already
                # except when something is being dragged
                if widget_being_dragged is None:
                    old_mouse_cursor = pygame.mouse.get_cursor()
                    if saved_mouse_cursor is None:
                        saved_mouse_cursor = old_mouse_cursor
                    deglitched_set_cursor(*resizer_cursors[self.which_border])
                    widget_which_set_mouse_cursor = self

        rc = False
        if not over_resize_area:
            rc = self.children.notify(ev)
            if is_mouse_event:
                # First, check for dragging:
                if (not rc) and self.draggable:
                    if is_left_button_press and self.top_collidepoint(ev.pos):
                        self.dragging = True
                        self.previous_mouse_pos = ev.pos
                        widget_being_dragged = self
                    elif is_left_button_release:
                        if self.dragging:
                            widget_being_dragged = None
                            self.dragging = False
                    elif (ev.type == MOUSEMOTION) and self.dragging:
                        if not ev.buttons[0]:
                            # button isn't down, so button-release was missed
                            widget_being_dragged = None
                            self.dragging = False
                        else:
                            self.move((ev.pos[0]-self.previous_mouse_pos[0],
                                       ev.pos[1]-self.previous_mouse_pos[1]))
                            self.previous_mouse_pos = ev.pos
                            changed = True
                # If this widget has a preferred mouse cursor, then change the
                # mouse cursor to that one if the mouse is over this widget:
                if ( self.use_this_mouse_cursor and
                     (self.dragging or self.mousecursor_collidepoint(ev.pos)) ):
                    if widget_which_set_mouse_cursor is not self:
                        old_mouse_cursor = pygame.mouse.get_cursor()
                        if saved_mouse_cursor is None:
                            saved_mouse_cursor = old_mouse_cursor
                        deglitched_set_cursor(*self.use_this_mouse_cursor)
                        widget_which_set_mouse_cursor = self
                # If mouse cursor moved away, we should restore it (but
                # we generally defer doing so to implement the "ugly mouse
                # cursor deglitch kludge"):
                elif widget_which_set_mouse_cursor is self:
                    # gly mouse cursor deglitch kludge, part 1:
                    deglitched_set_cursor(*saved_mouse_cursor)
                    widget_which_set_mouse_cursor = None
        return rc

    def _box_around(self, color=BLACK,thick=1):
        '''Draw a 1-pixel-wide line around the outside of a widget.

        This doesn't change the size of the sprite's image, it just overwrites
        the outermost pixels.  The box can be either all one color (default
        black), or two colors: the first used for top & left sides, the 2nd
        for bottom and right sides.
        '''
        global changed
        r = self.image.get_rect()
        if len(color) == 2:
            # draw top-right to bottom-right to bottom-left with 2nd color
            pygame.draw.lines(self.image, color[1], False,
                              [(r.w-1,1), (r.w-1,r.h-1), (1,r.h-1)])
            # draw bottom-left to top-left to top-right with 1st color
            pygame.draw.lines(self.image, color[0], False,
                              [(0,r.h-1), (0,0), (r.w-1,0)])
        else:
            # entire box is the same color
            pygame.draw.rect(self.image, color, self.image.get_rect(), thick)
        changed = True

    def notify_of_pending_removal(self, group):
        '''Method called by WidgetGroup.remove to tell the widget that it's
        about to be removed from a group.
        '''
        # First, notify any child widgets
        for child_widget in self.children:
            child_widget.notify_of_pending_removal(group)
        # We might someday need to distinguish between groups, but this seems
        # to be adequate for now.  We could determine whether a widget is
        # really being removed from the screen by checking whether it is in
        # drawn_sprites, or in .children of any widget in drawn_sprites,
        # or in any of their .children, etc.

    def remove(self, *groups):
        '''I don't currently use this, but it can be used to tell a widget
        to remove itself from some group(s).
        '''
        for group in groups:
            self.notify_of_pending_removal(group)
        pygame.sprite.Sprite.remove(self, *groups)

    def collidepoint(self, *pos):
        '''This method sends sprite.rect.collidepoint(pos) to the widget's
        rect.  If the result is 1 or True then this method returns True.
        If 0 or False then this returns False.

        You may pass either a 2-element tuple or separate X and Y coordinates
        as the input pos.

        Subclasses of Widget might override this and use smarter collision
        detection.

        A future version of this might handle subsurfaces, but this doesn't.
        '''
        try:
            pos[1]
        except IndexError:
            pos = pos[0]
        # They may pass either x and y separate parameters, or a length-2 tuple
        # containing x and y.  Either way, now it should be a length-2 tuple.
        result = self.rect.collidepoint(pos)
        if result:
            result = True
        else:
            result = False
            # documentation claims it returns bool, but pygame 1.9.1 actually returns 0 or 1; this fixes it
        return result

    def distance_collidepoint(self, pos):
        '''This method sends sprite.rect.collidepoint(pos) to the widget's rect.
        If the result is True then this method returns 1+ the squared distance
        between pos and the center of the widget (the "1+" is so that it'll
        always test as True).  If False then this returns False.

        The pos parameter must be a tuple; you can't pass separate x & y values.
        '''
        result = self.collidepoint(pos)
        if result:
            result = _distance_squared(self.rect.center, pos)
        return result

    def top_collidepoint(self, pos, include_children=False):
        '''This method is similar to collidepoint() except that it also checks
        to ensure that this point on this widget is not covered up by another
        widget.  If it is, then top_collidepoint() returns False.

        if include_children==True then child widgets are considered to be part
        of this widget, rather than covering it up.

        If self.never_has_focus is True then the only way this function can
        return True is if include_children is True and a child widget has the
        focus.

        Note that you must pass a tuple for pos; unlike collidepoint(), this
        method does not accept separate x and y parameters.
        '''
        result = False
        if self.collidepoint(pos):
            if self.never_has_focus:
                # if never_has_focus then return true only if include_children is true and a child widget has focus
                if include_children:
                    for child in self.children:
                        if child.collidepoint(pos):
                            if child.top_collidepoint(pos, include_children=True):
                                result = True
                                break
            else:
                # if never_has_focus=False, then return true unless covered by a child, sibling, or other top-level widget
                result = True
                # first check the child widgets
                if not include_children:
                    for child in self.children:
                        if child.collidepoint(pos):
                            if child.top_collidepoint(pos, include_children=True):
                                result = False
                                break
                # then check sibling widgets that are drawn after this one,
                # followed by parents' younger siblings, grandparents' younger
                # siblings, etc., up through the top-level drawn widgets:
                thiswidg = self
                while result and (thiswidg is not None):
                    for widg in younger_siblings(thiswidg):
                        if widg.top_collidepoint(pos, include_children=True):
                            # sibling widget is covering this pixel of this widget
                            result = False
                            break
                    if result:
                        thiswidg = thiswidg.parent  # check parent's younger siblings, etc.
        return result

    def mousecursor_collidepoint(self, pos):
        '''This method is similar to top_collidepoint() except that it is
        specialized for checking whether the mouse cursor should be changed.

        If self.use_this_mouse_cursor attribute is None, this will always
        return False.

        Otherwise, if pos is within self.rect, and it isn't covered by another
        widget which has a self.use_this_mouse_cursor, then this returns True.
        '''
        result = False
        if (self.use_this_mouse_cursor is not None) and self.collidepoint(pos):
            # Mouse cursor is within this widget's rect, and this widget has
            # a .use_this_mouse_cursor attribute.  So return true unless
            # covered up by a child, or by a sibling or higher-level widget
            # which has a .use_this_mouse_cursor attribute.
            result = True
            # first check the child widgets
            for child in self.children:
                if child.mousecursor_collidepoint(pos):
                    result = False
                    break
            # then check sibling widgets that are drawn after this one,
            # followed by parents' younger siblings, grandparents' younger
            # siblings, etc., up through the top-level drawn widgets:
            thiswidg = self
            while result and (thiswidg is not None):
                for widg in younger_siblings(thiswidg):
                    if widg.mousecursor_collidepoint(pos):
                        # sibling widget is covering this pixel of this widget
                        result = False
                        break
                if result:
                    thiswidg = thiswidg.parent  # check parent's younger siblings, etc.
        return result

    def resizer_collidepoint(self, pos):
        '''This method is similar to mousecursor_collidepoint() except that it
        is specialized for checking whether the mouse cursor should be changed
        to a resize cursor.

        If self.resizeable is not 'byMouse', this will always return False.

        Otherwise, if pos is within self.rect, and it isn't covered by another
        widget, and it's within the 4-pixel-wide edge region, then this returns
        True.
        '''
        result = False
        if (self.resizeable == 'byMouse') and self.collidepoint(pos):
            # Mouse cursor is within this widget's rect, and this widget is
            # resizeable.
            inner_rect = self.rect.copy()
            inner_rect.width -= (2 * SIZERWIDTH_4)
            inner_rect.height -= (2 * SIZERWIDTH_4)
            inner_rect.left += SIZERWIDTH_4
            inner_rect.top += SIZERWIDTH_4
            if not inner_rect.collidepoint(pos):
                # Mouse cursor is not in the interior, so it most be over the
                # border.  So return True unless covered up by another widget.
                result = True
                # Check sibling widgets that are drawn after this one,
                # followed by parents' younger siblings, grandparents' younger
                # siblings, etc., up through the top-level drawn widgets:
                thiswidg = self
                while result and (thiswidg is not None):
                    for widg in younger_siblings(thiswidg):
                        if widg.collidepoint(pos):
                            # sibling widget is covering this pixel of this widget
                            result = False
                            break
                    if result:
                        thiswidg = thiswidg.parent  # check parent's younger siblings, etc.
        return result

    def _make_image_surface(self, size, transparent=False):
        '''Create the .image attribute for a widget.'''
        w = max(0, size[0])
        h = max(0, size[1])
        size = (w, h)
        if transparent:
            # transparent background
            self.image = pygame.Surface(size, SRCALPHA)
            self.image.convert_alpha()
        else:
            # opaque background
            self.image = pygame.surface.Surface(size)

    def set_boxcolors(self, color=None):
        '''If you want a box drawn around your widget, then call this method
        with the desired line color (or None to delete the box).

        Color can either be a single color, or a tuple containing two colors.
        If it is a tuple containing two colors, then the first color is the
        color of the top and left borders, and the 2nd color is the color of
        the bottom and right borders. (This can be used to create 3D-ish
        effects, for button presses.)
        '''
        self.boxcolors = color

    def _fill_bg(self):
        '''Fill the entire widget's .image attribute with the background color.
        Or, if there's no background color, fill it with "transparent."
        '''
        if self.image.get_size() != self.rect.size:
            # widget size changed, so make a new surface of the correct size:
            self._make_image_surface(self.rect.size, transparent=(self.bgcolor is None))
        if self.bgcolor:
            # normal background
            self.image.fill(self.bgcolor)
        else:
            # transparent background
            self.image.fill((0,0,0,0))
        self._last_rendered_bgcolor = self.bgcolor

    def move(self, amt):
        '''Move widget by specified amount.  amt[0]=delta_x, amt[1]=delta_y.'''
        global changed
        if self.parent:
            # child widgets must adjust their .relative_rect positions
            self.relative_rect.left += amt[0]
            self.relative_rect.top += amt[1]
        self.rect.left += amt[0]
        self.rect.top += amt[1]
        changed = True

    def moveto(self, position):
        self.move( (position[0]-self.rect.left, position[1]-self.rect.top) )

    def update(self):
        '''If this widget has children, then .update() each child and blit its
        image onto the main widget's image.

        Any widget can have a self.boxcolors attribute, and if it is not None
        then when the widget gets the update message a box of the specified
        color(s) will be drawn around it.  (This doesn't change the size of
        the widget's .image attribute, it just overwrites the outermost pixels.)

        Note: when you subclass this, if you want the box to work, then call
        this superclass method AFTER you fill or blit-to the widget's image to
        set the background.
        '''
        global changed
        if self.parent:
            # this widget is a child of another widget
            if self.relative_rect.size != self.rect.size:
                if self.relative_rect == Rect(0,0,0,0):
                    # relative_rect hasn't been set yet, so set it from rect
                    self.relative_rect = self.rect.copy()
                else:
                    # self.rect always has the right width,height, so fix self.relative_rect
                    self.relative_rect.size = self.rect.size
            # absolute position self.rect.topleft is calculated from sum of
            # relative position self.relative_rect.topleft + parent's absolute
            # position self.parent.rect.topleft
            self.rect.topleft = (self.relative_rect.x + self.parent.rect.x,
                                 self.relative_rect.y + self.parent.rect.y)
        # if this widget is parent of other widgets...
        for child_widget in self.children:
            child_widget.parent = self
            child_widget.update()
            self.image.blit( child_widget.image, child_widget.relative_rect )
                            # ((child_widget.rect.left - self.rect.left), (child_widget.rect.top - self.rect.top)) )
        # if boxcolors have been set, then draw the box
        if hasattr(self, 'boxcolors') and self.boxcolors:
            if hasattr(self, 'thick'):
                thick=self.thick
            else:
                thick=1
            self._box_around(self.boxcolors,thick)
            # the boxcolors attribute is optional; missing is equivalent to None
        # if resizeable is 'byMouse', then draw the knurled lower-right corner
        if hasattr(self, 'resizeable') and (self.resizeable == 'byMouse'):
            self.image.blit(knurl, (self.rect.width-KNURLSIZE-2, self.rect.height-KNURLSIZE-2))
        pygame.sprite.Sprite.update(self)  # I don't think this actually does anything
        changed = True

    def add_widgets(self, *child_widgets):
        '''Add a list of child_widgets to a menu or form, in the order specified.
        This method is used for Forms and similar, to add child widgets
        that are used in the form.

        BTW, the reason I didn't call this method add() is that pygame.Sprite
        has a .add method for telling sprites to add themselves to groups.
        '''
        for widg in child_widgets:
            widg.parent = self
        self.children.add(*child_widgets)

    def remove_widgets(self, *child_widgets):
        '''Remove a list of child_widgets from a menu or form.
        '''
        self.children.remove(*child_widgets)

    def remove_nested_widgets(self, *child_widgets):
        '''Remove one or more child_widgets from a menu or form, and/or from
        any of its children.
        '''
        self.children.remove(*child_widgets)
        for widg in self.children:
            widg.remove_nested_widgets(*child_widgets)

    def __repr__(self):
        '''Answer a string representation of a widget.'''
        rs = '<a ' + type(self).__name__ + ' widget, Id=' + repr(self.Id) + ', size=' + repr(self.rect.size)
        if self.parent is not None:
            rs += ', parent.Id=' + repr(self.parent.Id) + ', parent.pos=' + repr(self.parent.rect.topleft)
            rs += '\n       rel_pos=' + repr(self.relative_rect.topleft)
        rs += ', pos=' + repr(self.relative_rect.topleft)
        if len(self.children) > 0:
            rs += ', has ' + repr(len(self.children)) + ' child widgets'
        rs += '>'
        return rs


class WidgetGroup(pygame.sprite.OrderedUpdates):
    '''A WidgetGroup is very similar to a regular OrderedUpdates sprite group,
    but it is intended to contain widgets.  (You can also put non-widget
    sprites in a WidgetGroup, but the get_widget_at() method won't find them.)

    Also, WidgetGroup has a notify() method to notify all its widgets of pygame
    events.
    '''
    def notify(self, ev):
        '''Notify all my widgets of the event ev; if any of them handle it, then
        return True, to tell the application that it can ignore this event,
        because it's already been handled.  (However, we still need to give
        every widget a look at MOUSEDOWN events, at least, since they can affect
        widgets other than the one being clicked, by causing one of them to
        lose focus.)
        '''
        global saved_mouse_cursor, widget_which_set_mouse_cursor
        global WidgetGroup_notify_recursion_counter
        WidgetGroup_notify_recursion_counter += 1
        done_drawing()  # sprite-drawing is done for now; we're getting events
        event_handled_by_widget = False
        for widget in self.sprites():
            if hasattr(widget, 'notify'):
                rc = widget.notify(ev)
                event_handled_by_widget = (event_handled_by_widget or rc)
        if (ev.type == WIDGETEVENT) and ev.internal:
            # an internal event, for communication between widgets; no need for
            # the application event loop to look at it
            event_handled_by_widget = True
        WidgetGroup_notify_recursion_counter -= 1
        deglitched_set_cursor_pt2()  # ugly mouse cursor deglitch kludge, part 2
        return event_handled_by_widget

    def remove(self, *sprites):
        '''For most widgets, this just passes control to super().remove, so
        it will remove the sprite(s) from the widget group.  But some widgets
        need to be notified of their pending removal (so they can restore the
        mouse cursor), so this sends that notification to them before removing
        them from the widget group.
        '''
        for sprite in sprites:
            if hasattr(sprite, 'notify_of_pending_removal'):
                sprite.notify_of_pending_removal(self)
            # if there's no .notify_of_pending_removal() method defined,
            # then it must be a non-widget sprite... but that's okay.
        pygame.sprite.OrderedUpdates.remove(self, *sprites)

    def sprites_painted_after(self, this_sprite):
        '''Return the list of sprites which are later in the WidgetGroup's
        .sprites() list than this_sprite.  The significance of that is that
        they will be blit'd to the screen after this_sprite, so if they
        overlap this one they will be on top.
        '''
        widgetlist = self.sprites()
        try:
            ndx = widgetlist.index(this_sprite)
        except ValueError:
            result = []
        else:
            result = widgetlist[ndx+1:]
        return result

    def get_widget_at(self, pos, allsprites=False):
        """Returns the sprite at the specified position, or None.

        This is similar to LayeredUpdates.get_sprites_at(), except that:
        1. Unless allsprites=True this only finds widget sprites, and
        2. This uses my Widget.collidepoint() method which can be subclassed
           to give better answers for non-rectangular or partially transparent
           widgets.
        3. This returns just one sprite, and
        4. If two or more sprites overlap at the position, it returns the
           one that is most closely centered on the position, not the one
           on top.
        """
        widgets = self.sprites()
        colliding = []  # list of tuples, each w/ a widget and its center's distance-squared from pos
        for widget in widgets:
            collided = False
            if hasattr(widget, 'collidepoint'):
                # it's a widget!  Use its built-in collidepoint method.
                collided = widget.collidepoint(pos)
            elif allsprites:
                # it's a regular, non-widget pygame sprite, but allsprites=True
                collided = widget.rect.collidepoint(pos)
            if collided:
                try:
                    dsquared = _distance_squared(widget.rect.center, pos)
                except:
                    print('dbg: _distance_squared() threw an exception!')
                    dsquared = 1  # in case of specialized widgets that lack a rect
                colliding.append((widget, dsquared))
        if not colliding:
            return None  # empty list means there are no widgets at pos
        else:
            # more than one widget is very close; prune the list down to the closest one
            while len(colliding) > 1:
                if colliding[0][1] > colliding[1][1]:
                    del colliding[0]
                else:
                    del colliding[1]
        return colliding[0][0]

    def draw(self, surface):
        note_draws(self.sprites())
        pygame.sprite.OrderedUpdates.draw(self, surface)

    # the .add() method is inherited from pygame.sprite.OrderedUpdates


class Image(Widget):
    '''Image is just a widget that displays an image (picture).
    Image objects ignore all pygame events, and don't generate them.

    Example:
        apicture = pygame.image.load('mugshot.png')
        myphoto = Image(apicture, pos=(50,30))

    Wnen creating an Image instance, you may specify these optional
    keyword parameters:

        pos  the topleft corner of the sprite

        bgcolor  is the background color; defaults to None, meaning transparent

        width  defaults to None, which means to figure it out from the image

        padding  number of extra pixels of "padding" surrounding the image

    Available methods include:

       set_bgcolor((0,0,255))  -- change the background color to deep blue.
           (Same as bgcolor=(0,0,255) parameter.)   For transparent, use None.

       set_width(200)  --  set width to 200 pixels, instead of determining
           it from the image.  (Same as width=200 parameter.)

       set_border(3)  -- add a 3-pixel border around the text, the same color
           as the background.  (Same as padding=3 parameter.)

    ...plus methods inherited from class Widget:

       collidepoint((70,50))  -- is (70,50) within the image?

       etc.

    As with any other sprite, you should send an update() message to your
    Image widget before draw()ing its group to blit the sprites to the screen.
    '''
    def __init__(self, image=None, size=None, pos=(0,0), bgcolor=None,
                 width=None, padding=0, pic_pos=(0,0)):
        '''Create an image sprite, with specified image, top-left position, etc.
        You must specify either image or size.

        If you specify size instead of image, you probably should also specify bgcolor.

        If you specify a non-zero padding, you probably should also specify bgcolor.

        If the image is non-transparent, you can prevent the expensive alpha
        channel by specifying a non-transparent bgcolor even if padding=0.
        '''
        global changed
        assert((image is not None) or (size is not None))
        self.bgcolor = bgcolor
        self._last_rendered_bgcolor = (1,2,3)
        self.padding = padding
        self.pic_pos = pic_pos  # for repositioning its .pic within the widget
        if not hasattr(self, 'Id'):
            # if this was subclassed, the subclass's __init__ might have already set the id; otherwise set it here
            self.Id = 'image'
        Widget.__init__(self)
        size_ = (0,0)
        if image:
            # usual case: set size from image
            self.pic = image
            size_ = image.get_size()
            size_ = (size_[0] + (2*self.padding) + self.pic_pos[0],
                     size_[1] + (2*self.padding) + self.pic_pos[1])
        if size:
            # alternately, if there's no image, size may be specified directly,
            # or it may be overridden via the size= parameter
            size_ = size
        self.rect = pygame.Rect(pos, size_)
        self._overridden_width = width
        if width != None:
            self.rect.width = width
        self.relative_rect = self.rect.copy()
        self._make_image_surface(self.rect.size, transparent=not self.bgcolor)
        changed = True

    def set_bgcolor(self, bgcolor=None):
        '''Set the background color for the widget.
        If bgcolor=None, then background is transparent.
        '''
        global changed
        self.bgcolor = bgcolor
        changed = True

    def set_width(self, width):
        '''Override the width calculated from the image width and the
        border padding.

        If width=None is passed, it means to cease overriding the automatic
        width determination
        '''
        global changed
        if (width is None) and self._overridden_width:
            # self.rect.width = self.image.get_width() + (2 * self.padding) # BUG? -- I don't think I should be adding 2*self.padding here, because self.image.get_width() should already include the padding which was added to self.pic.get_width()
            self.rect.width = self.image.get_width()  # I think this is right
            self._overridden_width = None
        else:
            self.rect.width = self._overridden_width = width
        self.relative_rect.size = self.rect.size
        changed = True

    def set_border(self, padding):
        '''Set the number of extra pixels of padding desired around the image.
        This always directly affects the top, left & botom borders.  But it won't
        affect the right border if set_width() has overridden the width.

        Note that setting the border and/or width with a transparent background
        is untested.
        '''
        global changed
        dif = padding - self.padding
        self.padding = padding
        self.rect.height += (2 * dif)
        if not self._overridden_width:
            self.rect.width += (2 * dif)
        self.relative_rect.size = self.rect.size
        changed = True

    def update(self):
        if ( (self.image.get_size() != self.rect.size) or
             ((self._last_rendered_bgcolor is None) != (self.bgcolor is None)) ):
            # dimensions or background transparency have changed, so make a
            # new image surface of the right size & transparency
            self._make_image_surface(self.rect.size, transparent=not self.bgcolor)
        self._fill_bg()  # fill in the background color
        if hasattr(self,'pic') and self.pic:
            self.image.blit(self.pic, (self.padding+self.pic_pos[0], self.padding+self.pic_pos[1]))
        Widget.update(self)


class Label(Image):
    '''Label is just a widget that displays a text string (label).
    Label objects ignore all pygame events, and don't generate them.

    Example:
        mylabel = Label('Hello, world!', pos=(50,30), color=(255,0,0))

    Wnen creating a Label instance, you may specify these optional
    keyword parameters:

        pos  the topleft corner of the sprite

        color  is the color of the text; defaults to black

        font  defaults to the Vera font, "Vera.ttf", if it is available

        bgcolor  is the background color; defaults to None, meaning transparent
                 (Note: text is always rendered with a transparent background
                 if the sprite also has an image attribute)

        width  defaults to None, which means to figure it out from the text

        padding  number of extra pixels of "padding" needed surrounding the text

        offset_from_left  number of extra pixels to the left of the first character

        ...plus optional image and pic_pos parameters as for Image widgets,
        (used for labels which also include images)

    Available methods include:

       set_text('string-of-text')  -- to change the text string

       set_bgcolor((0,0,255))  -- change the background color to deep blue.
           (Same as bgcolor=(0,0,255) parameter.)   For transparent, use None.

       set_width(200)  --  set width to 200 pixels, instead of determining
           it from the length of the text.  (Same as width=200 parameter.)

       set_border(3)  -- add a 3-pixel border around the text, the same color
           as the background.  (Same as padding=3 parameter.)

    ...plus methods inherited from class Widget:

       collidepoint((70,50))  -- is (70,50) within the label?

       etc.

    As with any other sprite, you should send an update() message to your
    Label widget before draw()ing its group to blit the sprites to the screen.
    '''
    def __init__(self, text='', pos=(0,0), color=BLACK, bgcolor=None, size=None,
                 width=None, font=vera, padding=0, image=None, offset_from_left=0,
                 pic_pos=(0,0), Id=None ):
        '''create a Label widget, with specified text, top-left position, color, etc.'''
        self.color = color
        self.font = font
        self.text = text
        self.offset_from_left = offset_from_left
        if not size:
            size = self.font.size(text)
            size = (size[0]+offset_from_left, size[1])
        if Id:
            self.Id = Id
        elif not hasattr(self, 'Id'):
            # if this was subclassed, the subclass's __init__ might have already set the Id; otherwise set it here
            self.Id = text
        Image.__init__(self, image=image, size=size, pic_pos=pic_pos, pos=pos,
                       bgcolor=bgcolor, width=width, padding=padding)

    def set_text(self, text, adjustwidth=None):
        '''Change the text for this label.  If adjustwidth=True, then the width will be adjusted, too.'''
        global changed
        self.text = text
        if adjustwidth:
            w, h = self.font.size(self.text)  # get the width it requires to render.  #@UnusedVariable
            self.relative_rect.width = self.rect.width = w + (2 * self.padding) + self.offset_from_left
            self._overridden_width = None
        changed = True

    def update(self):
        '''Update self.image from the text, rect, color, bgcolor, etc.'''
        global changed
        Image.update(self)
        if self.text != '':
            if (self.bgcolor is None) or (hasattr(self,'image') and self.image is not None):
                # for transparent background, omit the background color parameter
                txtimg = self.font.render(self.text, True, self.color)
            else:
                txtimg = self.font.render(self.text, True, self.color, self.bgcolor)
            self.image.blit(txtimg, (self.padding+self.offset_from_left,self.padding))
            Widget.update(self)  # repaint the box, in case txtimg overwrote it
        self._last_rendered_bgcolor = self.bgcolor
        changed = True

    def collidepoint(self, pos):
        '''Like Widget.collidepoint(), except that for labels with transparent
        backgrounds only the part which actually contains text "collides" (is
        clickable).
        '''
        result = Widget.collidepoint(self, pos)
        if result and (self.bgcolor is None):
            w,h = self.font.size(self.text)  # get the width it requires to render.  #@UnusedVariable
            if pos[0] > (self.rect.left + w + (2 * self.padding) + self.offset_from_left):
                # they clicked in the transparent tail of the string
                result = None
        return result


class SimpleButton(Label):
    '''A Simple Button is like a Label, except that it has a notify()
    method to notify it of events, and if you click it, it generates a pygame event.

    It should have either the text= or image= parameter specified; otherwise,
    you'll get a blank button.

    Pass the initializer an event.Id value (Id=), to be used when generating
    events.  If the id is omitted, the button caption (text= parameter) is used.
    '''
    def __init__(self, text='', padding=0, image=None, pos=(0,0), border=2,
                 color=BLACK, bgcolor=None, size=None, pic_pos=(0,0),
                 Id=None, three_D=False, internal=False):
        self.Id = Id
        self.isdown = False
        if internal:
            self.internal = True
        self.never_has_focus = False  # buttons can have mouse focus
        if Id is None:
            if text == '':
                self.Id = 'imagebutton'
            else:
                self.Id = text  # default for Id returned by clicking this button is the button caption
        self.text = text
        if bgcolor is None:
            bgcolor_ = button_up_color
        else:
            bgcolor_ = bgcolor
        if text != '':
            Label.__init__(self, text, padding=padding, pos=pos, color=color,
                           bgcolor=bgcolor_, size=size, width=None)
        if image or (text == ''):
            Image.__init__(self, padding=padding, image=image, pic_pos=pic_pos,
                           pos=pos, bgcolor=bgcolor_, size=size, width=None)
        self.three_D = three_D
        self.saved_boxcolors = None
        if three_D:
            self.set_boxcolors( color=((230,230,230),(83,83,83)) )  # default 3D colors are light & dark grey
        if bgcolor is None:
            self.set_colors(button_up_color, button_dn_color, button_up_color)  # default colors are appropriate for a singleton button
        else:
            self.set_colors(bgcolor, bgcolor, bgcolor)
        if border != 0:
            self.set_border(border)
        if size is not None:
            self.rect.size = size  # prevent border from increasing size

    def _swapped_boxcolors(self):
        '''If boxcolors is set to a single color, this returns it; if set to a
        pair of colors, this returns them in swapped order.  If boxcolors is
        not set, this returns None.  (Handy when doing 3D button-press effects.)
        '''
        result = None
        try:
            result = self.boxcolors
            if self.three_D and (len(result) == 2):
                result = (result[1], result[0])
        except AttributeError:
            pass
        return result

    def set_colors(self, up=None, dn=None, hover=None, fg=None):
        '''Set any or all of the three possible background colors for a button,
        and/or the text (forground) color.

        Singleton buttons generally have only two background colors: up and down.
        But buttons which are part of a menu have a hover-over color which is
        different from the up-color.

        Note that "None" here means don't set the color, rather than transparent.
        '''
        if up:
            self.color_up = up
        if dn:
            self.color_dn = dn
        if hover:
            self.color_hover = hover
        if fg:
            self.color = fg
        self.set_bgcolor(self.color_up)

    def click(self):
        '''Post a button-click user event to the pygame event queue'''
        if hasattr(self, 'internal'):
            # if self.internal=True then this is an internal button,
            # e.g., part of a scroll bar
            internal = self.internal
        else:
            internal = False
        ev = pygame.event.Event( WIDGETEVENT, {'Id':self.Id, 'sender':self, 'internal':internal} )
        pygame.event.post(ev)

    def _3D_up(self):
        '''undo 3D "down" effect'''
        if self.three_D and self.saved_boxcolors and self.boxcolors:
            self.boxcolors = self.saved_boxcolors
            self.saved_boxcolors = None

    def _3D_dn(self):
        '''create 3D "down" effect by swapping the box colors'''
        if self.three_D and self.boxcolors and not self.saved_boxcolors:
            self.saved_boxcolors = self.boxcolors
            self.boxcolors = self._swapped_boxcolors()

    def notify(self, ev):
        '''Receive notification of a pygame event, and do something if it is for this button.
        If the event belongs (exclusively) to this button, return True, else False.
        '''
        rc = False
        if (ev.type == MOUSEBUTTONDOWN) and (ev.button == MOUSEBUTTONLEFT) and self.top_collidepoint(ev.pos):
            self.set_bgcolor(self.color_dn)  # render the down-state button image
            self._3D_dn()
            self.isdown = True
            self.hasmousefocus = True
            # send internal-use-only widget event to tell text-entry widgets that they've lost keyboard focus
            tmpev = pygame.event.Event( WIDGETEVENT, {'Id':'KBDFOCUS', 'sender':self, 'internal':True} )
            notify_all_widgets(tmpev)
            rc = True  # no other widgets need to receive this event
        elif (ev.type == MOUSEBUTTONUP) and (ev.button == MOUSEBUTTONLEFT) and self.top_collidepoint(ev.pos):
            self.set_bgcolor(self.color_hover)  # render the up-state hovering button image
            self._3D_up()
            self.isdown = False
            self.hasmousefocus = True
            self.click()  # enqueue WIDGETEVENT / self.Id pygame event
            rc = True  # no other widgets need to receive this event
        elif ev.type == MOUSEMOTION:
            # need to show focus when mouse pointer moves in, lose it when mouse pointer moves out
            if self.top_collidepoint(ev.pos):
                if not self.hasmousefocus:
                    # user just moved the mouse over this button
                    self.isdown = pygame.mouse.get_pressed()[0]
                    if self.isdown:
                        self.set_bgcolor(self.color_dn)  # render the down-state button image
                        self._3D_dn()
                    else:
                        self.set_bgcolor(self.color_hover)  # render the up-state hovering button image
                        self._3D_up()
                    self.hasmousefocus = True
            else:
                if self.hasmousefocus:
                    # user just moved the mouse away from this button
                    self.isdown = False
                    self.set_bgcolor(self.color_up)  # render the up-state non-hovering button image
                    self._3D_up()
                    self.hasmousefocus = False
            # MOUSEMOTION events can affect more than one widget, so return rc=False
        Widget.notify(self, ev)  # for mouse cursor handling (or draggable buttons)
        return rc


class Button(SimpleButton):
    '''A Button is like a SimpleButton, except that it changes the
    mouse cursor over the button.
    '''
    def __init__(self, text='', image=None, pos=(0,0), border=2, color=BLACK, Id=None, three_D=False):
        SimpleButton.__init__(self, text=text, image=image, pos=pos,
                           border=border, color=color, Id=Id, three_D=three_D)
        self.use_this_mouse_cursor = default_mouse_cursor


class CloseButton(Button):
    '''The little 14x14 close button (with 8x8 "X") for use in a title bar
    '''
    def __init__(self, pos=(3,3), Id='Close'):
        Button.__init__(self, image=Xpic, pos=pos, border=0, Id=Id, three_D=True)
        self.set_colors(up=(240,240,240), dn=(220,220,220), hover=(240,240,240))  # light & medium grey
        self.boxcolor = ((255,255,255),(105,105,105))  # white and dark grey


class SimpleCheckbox(Image):
    '''A SimpleCheckbox is a simple 13x13 pixel check-box, with two possible
    states: unchecked and checked.

    Clicking on it reverses its state.

    Pass the initializer an event.Id value (Id=), to be used when generating
    events.  If the Id is omitted, then 'checkbox' is used (which, obviously,
    is only adequate if there's only one checkbox in your program).
    '''
    def __init__(self, pos=(0,0), Id='checkbox', checked=False, padding=0):
        self.Id = Id
        self.checked = checked
        self.never_has_focus = False  # checkboxes can have mouse focus
        Image.__init__(self, image=unchecked.copy(), pos=pos, padding=padding )

    def click(self):
        '''Post a checkbox-change event to the pygame event queue'''
        ev = pygame.event.Event( WIDGETEVENT, {'Id':self.Id, 'internal':False, 'checked':self.checked} )
        pygame.event.post(ev)

    def notify(self, ev):
        '''Receive notification of a pygame event, and do something if it is
        for this checkbox widget.

        If the event belongs (exclusively) to this button, return True, else False.
        '''
        rc = False
        if (ev.type == MOUSEBUTTONDOWN) and (ev.button == MOUSEBUTTONLEFT) and self.top_collidepoint(ev.pos):
            tmpev = pygame.event.Event( WIDGETEVENT, {'Id':'KBDFOCUS', 'sender':self, 'internal':True} )
            notify_all_widgets(tmpev)
            rc = True  # no other widgets need to receive this event
        elif (ev.type == MOUSEBUTTONUP) and (ev.button == MOUSEBUTTONLEFT) and self.top_collidepoint(ev.pos):
            self.checked = not self.checked
            self.click()
            rc = True  # no other widgets need to receive this event
        Widget.notify(self, ev)  # for mouse cursor handling (or draggable widget, but that would be weird)
        return rc

    def update(self):
        if self.checked:
            self.image.blit(checked, (self.padding,self.padding))
        else:
            self.image.blit(unchecked, (self.padding,self.padding))


class Checkbox(SimpleCheckbox, Label):
    '''A Checkbox is a simple 13x13 pixel check-box, plus optional text
    to label it, with two possible states: unchecked and checked.

    It is a hybrid class, using multiple-inheritance to combine the features
    of a SimpleCheckbox and a Label.

    Clicking on it reverses its state.

    Pass the initializer an event.Id value (Id=), to be used when generating
    events.  If the id is omitted, then 'checkbox' is used (which, obviously,
    is only adequate if there's only one checkbox in your program).

    Checkbox also differs from SimpleCheckbox in that Checkbox
    adds code to change the mouse cursor over the widget.
    '''
    def __init__(self, pos=(0,0), Id='checkbox', checked=False, padding=0,
                 text='', color=BLACK, bgcolor=None, width=None, font=vera,
                 boxcolors=None):
        SimpleCheckbox.__init__(self, pos=pos, Id=Id, checked=checked,
                                padding=padding)
        size = font.size(text)
        size = (size[0]+CHECKBOXSIZE+3+2*padding, size[1]+2*padding)
        if size[1] < (CHECKBOXSIZE + 2*padding):
            size = (size[0], (CHECKBOXSIZE + 2*padding))  # has to be tall enough for a simplecheckbox
        if width:
            size[0] = width
        else:
            width = size[0]
        Label.__init__(self, image=unchecked.copy(), text=text, pos=pos,
                       color=color, font=font, size=size, bgcolor=bgcolor,
                       offset_from_left=CHECKBOXSIZE+3, width=width,
                       padding=padding)
        if boxcolors:
            self.set_boxcolors(boxcolors)
        # mouse cursor should be changed to default arrow over a checkbox:
        self.use_this_mouse_cursor = default_mouse_cursor

    def update(self):
        Label.update(self)  # draw the background & label text
        SimpleCheckbox.update(self)  # then the checkbox

    # top_collidepoint() is inherited from Label, and notify() is inherited
    # from SimpleCheckbox, so you can reverse the state of the checkbox
    # by clicking anywhere on the box or its label.  Neat, eh?


# pop-up menu borders are 3 pixels wide: the two inner pixels are very light,
# the outer border is a 1-pixel dark grey line:
menu_border_inner_color = (245,245,245)
menu_border_outer_color = (151,151,151)

class Menu(Widget):
    '''A vertical menu widget is a widget which contains a WidgetGroup of
    simplebutton widgets, one for each menu item.
    '''
    def __init__(self, pos=(0,0), Id='aMenu'):
        self.border_thickness = 3  # hard-coded for now, but could change
        self.Id = Id
        self.never_has_focus = False  # menus can have mouse focus (and so can their buttons)
        Widget.__init__(self)
        # menu selection buttons are stored in self.children (which was initialized by Widget.__init__())
        self.rect = pygame.Rect(pos, (self.border_thickness*2,self.border_thickness*2))
        self.image = pygame.Surface((self.border_thickness*2,self.border_thickness*2))
        self.set_boxcolors(menu_border_outer_color)  # menus need a box around them
        self.use_this_mouse_cursor = default_mouse_cursor

    def add_widgets(self, *buttons):
        '''Add a list of buttons to a menu, in the order specified.  This is
        the same as the .add_widgets() method for the Widget class, except
        that this one overrides the button colors for our standard menu colors.
        '''
        for button in buttons:
            button.set_colors(menu_bgcolor, button_dn_color, menu_hover_color)
        Widget.add_widgets(self, *buttons)

    def _arrange_buttons(self):
        w = 0
        h = self.border_thickness
        # left = self.border_thickness
        for button in self.children:
            button.relative_rect.topleft = (self.border_thickness, h)
            button.rect.topleft = (self.border_thickness + self.rect.left, h + self.rect.top)
            h += button.rect.height
            w = max(w, button.rect.width)
        h += self.border_thickness
        w2 = w + (2 * self.border_thickness)
        self.relative_rect.size = self.rect.size = (w2, h)
        for button in self.children:
            button.set_width(w)
        if self.image.get_size() != self.rect.size:
            # menu size/shape has changed, so we must refresh the image:
            # the inner-border, outer-border, and buttons:
            self.image = pygame.Surface((w2, self.rect.height))
            self.image.fill(menu_border_inner_color)  # fill with inner border color
            # outer border is taken care of by Widget.update()
            # self._box_around(menu_border_outer_color)  # draw outer border

    def update(self):
        '''blit each button onto the menu's image'''
        self._arrange_buttons()
        Widget.update(self)

    @classmethod
    def ActionMenu(cls, labels, selectors=None, pos=(0,0), Id='aMenu'):
        '''Quick constructor of a Menu instance and its buttons.
        The labels are contained in a string and separated by '|' vertical bars.

        A button will be created for each label.

        The selectors are a list of event.Id values, one for each button.
        If selectors are omitted, then the labels (strings) will be used.
        
        If any label is prefixed with "-" then it will be shown greyed-out.  Although
        the "-" is not shown in the menu, if the selectors are allowed to default to
        be the button labels, then the "-" will be included in the event.Id when such
        a menu item is clicked; when such an event is received, it's a good idea to
        pop-up an explanation of why the menu item is disabled.
        '''
        menu = cls(Id=Id)
        lbls = labels.split('|')  # that's a vertical bar '|' even though it looks like a slash in Eclipse
        n = len(lbls)
        if selectors:
            if n != len(selectors):
                raise 'Wrong number of selectors: ' + repr(len(selectors)) + ' selectors for ' + repr(n) + ' labels.'
        else:
            selectors = lbls
        buttons = []
        for i in range(0, n):
            if lbls[i][0] =='-':  # leading '-' on label means disabled
                button = SimpleButton(lbls[i][1:], Id=selectors[i], border=4)
                button.set_colors(fg=(128,128,128))  # grey indicates "disabled"
            else:
                button = SimpleButton(lbls[i], Id=selectors[i], border=4)
            buttons.append(button)
        menu.add_widgets(*buttons)
        menu.rect.topleft = menu.relative_rect.topleft = pos
        # menu.rect.topleft is for the normal case, menu.relative_rect.topleft is
        # for when we're building a menu for use within another widget.
        return menu
    # Note: using the @classmethod decorator (which fills in the cls parameter)
    # ensures that this method will work properly even on subclasses of MenuClass.
    # See Alex Martelli's excellent answer, here:
    # http://stackoverflow.com/questions/1950414/what-does-classmethod-has-done-who-can-give-me-a-simple-code-example-thanks
    # (or here: http://www.webcitation.org/66OPVbKlf)


class TextEditBox(Label):
    '''A TextEditBox is like a Label, except that the label is editable
    from the keyboard.

    Pass an event.Id value (Id=) to the initializer, for use when generating
    events.  If id is omitted, 'text' is used.

    maxlen  is maximum number of enterable characters allowed (default 80).

    width  is width of edit box, in pixels.

    A pygame event will be generated when the user presses the [Enter] key,
    and the text string that the user entered will be stored in event.text
    (and also retained in the widget's .text attribute).
    '''
    def __init__(self, text='', maxlen=80, width=100, pos=(0,0), border=2, color=BLACK, bgcolor=None, Id='text'):
        self.Id = Id
        self.never_has_focus = False  # TextEditBoxs can have mouse focus
        self.haskbdfocus = False
        self.cursorpos = 0
        self.maxlen = maxlen
        self.insert_mode = True
        self.selection_start = 0
        self.selection_end = 0
        self.saved_bgcolor = bgcolor
        self.boxcolors = None
        self.saved_boxcolors = None
        Label.__init__(self, text, pos=pos, color=color, bgcolor=bgcolor, width=width)
        if border != 0:
            self.set_border(border)
        self.use_this_mouse_cursor = default_mouse_cursor

    def enter_key(self):
        '''Post a user event to the pygame event queue in response to the Enter key.'''
        ev = pygame.event.Event( WIDGETEVENT, {'Id':self.Id, 'text':self.text, 'internal':False} )
        pygame.event.post(ev)

    def focus(self, has_focus=True):
        '''called when we get or lose kbd focus'''
        if self.haskbdfocus != has_focus:
            # change things (display or hide cursor, etc.)
            self.haskbdfocus = has_focus
            if self.haskbdfocus:
                Label.set_bgcolor( self, (255,255,220) )  # change the color to show focus
                self.saved_boxcolors = self.boxcolors
                self.set_boxcolors(BLACK)  # also, draw a black box around it (or change box color to black, if there was already a box around it)
                # send internal-use-only widget event to tell other widgets that they've lost focus
                tmpev = pygame.event.Event( WIDGETEVENT, {'Id':'KBDFOCUS', 'sender':self, 'internal':True} )
                notify_all_widgets(tmpev)
            else:
                Label.set_bgcolor( self, self.saved_bgcolor )
                self.set_boxcolors(self.saved_boxcolors)
                self.saved_boxcolors = None
            changed = True

    def set_text(self, text, adjustwidth=None):
        '''The only thing this adds to the implementation in class Label
        is that it enforces maxlen.
        '''
        if (self.maxlen != 0) and (len(self.text) > self.maxlen):
            text = text[:self.maxlen]
        Label.set_text(self, text, adjustwidth)

    def update(self):
        '''Update the image for displaying.

        If this widget doesn't have focus, then super().update does all the
        work.  But if it does have focus, then we have to show the focus via
        a box around it, a slightly yellowed background color, and a cursor
        (1 pixel-wide for insert mode, 2 pixels for replace/overstrike mode).
        Also, if the text doesn't fit in the rect, then we have to scroll it
        left/right as needed, according to the edit cursor position, and show
        the relevant part.
        '''
        Label.update(self)
        if self.haskbdfocus:
            # draw the cursor
            thickness = 1
            if not self.insert_mode:
                thickness = 2
            # The hardest part is figuring out where to draw it.
            # First, get the rendered width of the text to the left of the cursor
            x, h = self.font.size(self.text[:self.cursorpos])
            x += (self.padding - 1)
            y = self.padding
            h = self.rect.height - (2 * self.padding + 1)
            # check for overflow
            maxx = self.rect.width - (self.padding + 3)
            if x > maxx:
                # uh oh!  It's too long!
                # re-render the whole thing, then re-blit it with a negative
                # x-origin, to truncate left part
                self._fill_bg()  # fill in the background color
                if self.bgcolor:
                    # normal background
                    txtimg = self.font.render(self.text, True, self.color, self.bgcolor)
                else:
                    # transparent background
                    txtimg = self.font.render(self.text, True, self.color)  # omit the background color parameter
                self.image.blit(txtimg, (self.padding-(x-maxx),self.padding) )
                # draw the cursor (at the end):
                pygame.draw.line(self.image, BLACK, (maxx,y), (maxx,y+h), thickness)
            else:
                # good, it fits.
                pygame.draw.line(self.image, BLACK, (x,y), (x,y+h), thickness)
            Widget.update(self)  # redraw the box around it

    def notify(self, ev):
        '''Receive notification of a pygame event, and do something if it is
        for this widget.
        If the event belongs (exclusively) to this widget, return True, else False.
        '''
        global changed
        rc = False
        if ev.type == MOUSEBUTTONDOWN:
            if self.top_collidepoint(ev.pos):
                rc = True   # this click is for us alone
                if ev.button == MOUSEBUTTONLEFT:
                    # user left-clicked on the widget
                    self.focus(True)
                    # problem: other widgets need to know that they lost focus. hmmmm...
                # else right-clicks are ignored, for now (could pop-up a copy/cut/paste menu)
            else:
                # they clicked away from the widget, with either mouse button
                self.focus(False)
        elif (ev.type == KEYDOWN) and self.haskbdfocus:
            # got a keystroke
            if not pygame.key.get_focused():
                print('Strange! Got keystroke but key.get_focused()=False')
            ch = ev.unicode
            ky = ev.key
            rc = True  # this keystroke is for us alone
            if ch == '\r':
                # he pressed the [Enter] key
                self.enter_key()  # post the text-entered event
                self.focus(False)  # done entering, so give up keyboard focus
            elif ky == K_BACKSPACE:
                if self.cursorpos > 0:
                    self.text = self.text[:self.cursorpos-1] + self.text[self.cursorpos:]
                    self.cursorpos -= 1
            elif ky == K_DELETE:
                if self.cursorpos < len(self.text):
                    self.text = self.text[:self.cursorpos] + self.text[self.cursorpos+1:]
            elif ky == K_HOME:
                self.cursorpos = 0
            elif ky == K_END:
                self.cursorpos = len(self.text)
            elif ky == K_INSERT:
                self.insert_mode = not self.insert_mode
            elif ky == K_RIGHT:
                if self.cursorpos < len(self.text):
                    self.cursorpos += 1
            elif ky == K_LEFT:
                if self.cursorpos > 0:
                    self.cursorpos -= 1
            elif ky == K_TAB:
                # do something useful with the tab key (implements 8-space tabs)
                amt = 8 - (self.cursorpos % 8)
                if amt == 0:
                    amt = 8
                self.cursorpos += amt
                if self.cursorpos > len(self.text):
                    self.cursorpos = len(self.text)
            else:
                if len(ch) > 0:  # ignore shift key, ctrl key, etc.
                    try:
                        # print('Got character ch=' + repr(ch) + ' key=' + repr(ky))
                        if self.insert_mode:
                            if (self.maxlen == 0) or (len(self.text) < self.maxlen):
                                self.text = self.text[:self.cursorpos] + ch + self.text[self.cursorpos:]
                                self.cursorpos += 1
                            # else should beep here
                        else:
                            self.text = self.text[:self.cursorpos] + ch + self.text[self.cursorpos+1:]
                            self.cursorpos += 1
                        if (self.maxlen != 0) and (len(self.text) > self.maxlen):
                            self.text = self.text[:self.maxlen]
                        if self.cursorpos > self.maxlen:
                            self.cursorpos = self.maxlen
                    except:
                        # should beep here
                        pass
            changed = True
        elif (ev.type == WIDGETEVENT) and ev.internal and (ev.Id == 'KBDFOCUS') and (ev.sender is not self):
            # another widget has taken the keyboard focus
            self.focus(False)
        Label.notify(self, ev)  # for mouse cursor handling (or draggable editbox)
        return rc


class BasicForm(Widget):
    '''General-purpose container class in which multiple widgets are displayed
    within a widget "form."  To use it, first create the individual widgets,
    then (instead of drawing them directly on the display) you can add them to
    a BasicForm widget, and draw it on the display.

    The rect parameter specifies the position and size of the form, as a pygame
    Rect, or a tuple of four values (left,top,width,height), or a tuple of two
    pairs ((left,top),(width,height)).  If you don't specify it when you create
    the form, it defaults to (0,0,0,0) and you can fill it in later.  However,
    note that, as with all widgets, there are 2 different Rect attributes which
    are used.  The size should be the same in both (and widget.rect.size
    contains the master copy).  But there are two positions: for top-level
    widgets, widget.rect.topleft is the position and widget.relative_rect is
    ignored.  But for a child widget (a widget contained in a BasicForm or other
    container widget), widget.relative_rect.topleft is the master position,
    which is the position relative to the parent widget, and widget.rect.topleft
    will be periodically reset to be the sum of the parent widget's position and
    the child widget's relative_rect.topleft.

    For a transparent background, you must specify bgcolor=None.  The default
    is a very light blue opaque background.

    If you want a box (one-pixel border) drawn around your form, then specify
    the boxcolors parameter, e.g., boxcolors=(0,0,0) for a black border.  The
    default is no box.

    BasicForm widgets don't generate any pygame events (though the widgets which
    they contain might do so).  Consequently, use of the Id= parameter to name
    your forms is optional.
    '''
    def __init__(self, rect=(0,0,0,0), bgcolor=(240,240,255), boxcolors=None,
                 Id='aForm', draggable=False, thick=1):
        Widget.__init__(self)
        self.titlebar = None
        self.Id = Id
        self.draggable = draggable
        if bgcolor:
            self.never_has_focus = False
            # BasicForms can have mouse focus unless they have transparent background
        self.rect = pygame.Rect(rect)
        self.relative_rect = pygame.Rect(rect)
        self.bgcolor = bgcolor
        self._make_image_surface(self.rect.size, transparent=not self.bgcolor)
        self.boxcolors = boxcolors
        self.thick=thick

    def update(self):
        self._fill_bg()  # fill in the background color
        # send .update() to each child widget, then blit each child widget onto
        # the form's image.  Then, if there's a boxcolor, draw the box.
        Widget.update(self)


class InputBox(BasicForm):
    '''Question and Answer -- a class for widgets which contain two other
    widgets: a Label (displaying the question), and a TextEditBox (where the
    answer can be entered).
    '''
    def __init__(self, maxlen=80, width=100, pos=(0,0), color=BLACK,
                 bgcolor=(240,240,255), question='Question:',
                 answer='Type answer here & press [Enter]',
                 boxcolors=BLACK, Id='InputBox'):
        q = Label(text=question, color=color, pos=(10,10), Id='Q.'+Id)
        if width:
            w = width
        else:
            w = 13 * maxlen
        if w < (q.rect.width + 20):
            w = q.rect.width + 20
        if w < 30:
            w = 30
        elif w > 600:
            w = 600
        h = 60
        a = TextEditBox(text=answer, pos=(10,30), maxlen=maxlen, width=w, bgcolor=(255,240,240), Id=Id)
        BasicForm.__init__(self, rect=(pos,((w+20),h)), bgcolor=bgcolor, boxcolors=boxcolors, Id='wrapperform.'+Id)
        self.add_widgets(q, a)


class Titlebar(BasicForm):
    '''A Titlebar is for use with another widget (normally a Form),
    as its Title Bar.

    It has either one or two child widgets.  The first child widget is
    always the caption (titletext).  The second child widget is the close
    button, unless you pass closable=False.

    You can change the caption text via the set_caption method.

    If there's a close button, its id (which is sent with its click events)
    is the titlebar's id with "close." prefixed.
    '''
    def __init__(self, title='', width=100, Id='titlebar', draggable=True, closeable=True):
        tt_id = 'text.' + Id
        titletext = Label(title, Id=tt_id)
        BasicForm.__init__(self, rect=(0,0,width,TB_HEIGHT_21), bgcolor=(215,215,245),
                           Id=Id, draggable=draggable)
        if draggable:
            self.never_has_focus = False  # title bars get mouse focus if opaque and/or draggable (and, for now, they are always opaque)
        titletext.relative_rect.left = 8
        titletext.relative_rect.centery = self.rect.centery
        self.closeable = closeable
        self.add_widgets(titletext)
        if closeable:
            closebutton = CloseButton(pos=(width-18,4), Id='close.'+Id)
            titletext.set_width(width - 28)
            self.add_widgets(closebutton)
        else:
            titletext.set_width(width - 15)
        self.use_this_mouse_cursor = default_mouse_cursor

    def update(self):
        if self.parent:
            parent = self.parent
            # Adjust the length of the title bar to match its enclosing form.
            # This is the normal case, since title bars are intended to be within forms.
            self.rect.width = parent.rect.width
            if self.closeable:
                self.children.sprites()[1].relative_rect.left = self.rect.width-18  # reposition the close button
                self.children.sprites()[0].set_width(self.rect.width - 28)  # limit length of text to just short of the close button
            else:
                self.children.sprites()[0].set_width(self.rect.width - 15)
            # If title bar got dragged, then drag its parent along:
            if self.relative_rect.topleft != (0,0):
                if hasattr(parent, 'parent'):
                    # our parent form has a parent
                    parent.relative_rect.left += self.relative_rect.left
                    parent.relative_rect.top += self.relative_rect.top
                parent.rect.left += self.relative_rect.left
                parent.rect.top += self.relative_rect.top
                self.relative_rect.left = 0
                self.relative_rect.top = 0
        BasicForm.update(self)

    def set_caption(self, title):
        titletext = self.children.sprites()[0]
        titletext.set_text(title)


class Form(BasicForm):
    '''Like BasicForm, but adds a title bar.  Note that the title bar
    uses the top 21 pixel rows of the form, so don't draw other things there.

    The titlebar is the first child of the resulting form, and for convenience
    it is also stored as self.titlebar.
    '''
    def __init__(self, rect=(0,0,0,0), bgcolor=(240,240,255), boxcolors=None,
                 Id='aForm', title='', draggable=True, closeable=True,thick=1):
        rect = pygame.Rect(rect)
        min_height = (1+TB_HEIGHT_21)
        if rect.height < (1+TB_HEIGHT_21):
            rect.height = (1+TB_HEIGHT_21)
        min_width = 2
        if closeable:
            min_width = 16
        if rect.width < min_width:
            rect.width = min_width
        BasicForm.__init__(self, rect=rect, bgcolor=bgcolor,
                           boxcolors=boxcolors, Id=Id,thick=thick)
        self.min_width = min_width
        self.min_height = min_height
        # temporarily use form Id for the title bar, so close button gets right Id
        tb = Titlebar(title=title, width=rect.width, Id=Id,
                            draggable=draggable, closeable=closeable)
        tb.Id = 'title.' + Id  # then adjust the title bar's Id
        self.titlebar = tb
        self.add_widgets(tb)

    def set_caption(self, title):
        self.titlebar.set_text(title)


class WrapperForm(BasicForm):
    '''Like BasicForm, but used for wrapping other widgets.  The only
    difference is that when it gets resized it resizes its child widget, too.
    '''
    def update(self):
        if self.image.get_size() != self.rect.size:
            # widget size changed, so adjust wrapped children sizes
            w_delta = self.rect.width - self.image.get_width()
            h_delta = self.rect.height - self.image.get_height()
            for widg in self.children.sprites():
                if widg.resizeable:
                    widg.rect.width += w_delta
                    widg.rect.height += h_delta
        BasicForm.update(self)


class SliderButton(SimpleButton):
    '''A SliderButton is a special button, which can be dragged either
    horizontally or vertically (but not both).  Clicking it doesn't actually
    do anything except change the 3D effect to show that it is being dragged,
    but dragging it generates repeated click events.  It is for use by a
    ScrollBar widget, of which it must be a child widget.
       Its initializer has two additional parameters: horizontal (boolean),
    and px_range (integer).  px_range is the number of pixels that the
    button can slide: the length of the "track" on which it slides, minus
    the length of the button itself.  So, for instance, if the button is 15x25,
    and the scrollbar is 250 pixels long (including the two 11-pixel-long
    endcaps), then the "track" on which the button can slide is 250-(2*11) =
    228 pixels long, and px_range is 228-25 = 203.
    '''
    def __init__(self, text='', padding=0, image=None, pos=(1,12), border=0,
                 color=BLACK, bgcolor=None,
                 size=(SB_CHANNEL_WIDTH_15,SB_CHANNEL_WIDTH_15), pic_pos=(4,3),
                 Id='slider', three_D=True, internal=True, horizontal=False,
                 px_range=213):
        SimpleButton.__init__(self, text=text, padding=padding, image=image,
                 pos=pos, border=border, color=color, bgcolor=bgcolor,
                 size=size, pic_pos=pic_pos, Id=Id, three_D=three_D,
                 internal=internal)
        self.is_slider = True
        self.slider_dragging = False
        self.horizontal = horizontal
        self.px_range = px_range
        # Note: px_range gets adjusted by the parent ScrollBar widget's .update
        # method, so you really don't need to set it when initializing a
        # SliderButton instance
        self.accumulate_amt_moved = 0

    def notify(self, ev):
        '''Receive notification of a pygame event, and do something if it is
        for this slider.
        '''
        rc = False
        if ev.type == MOUSEMOTION:
            if self.isdown and not ev.buttons[0]:
                # button isn't down, so button-release was missed
                self.isdown = False
                self.slider_dragging = False
            if self.isdown:
                # dragging!
                self.slider_dragging = True
                if self.horizontal:
                    # this is a horizontal scrollbar slider, being dragged
                    prev_mpos = self.previous_mouse_pos[0]
                    new_mpos = ev.pos[0]
                else:
                    # vertical scrollbar slider, being dragged
                    prev_mpos = self.previous_mouse_pos[1]
                    new_mpos = ev.pos[1]
                amt_moved = new_mpos - prev_mpos
                if amt_moved != 0:
                    if self.horizontal:
                        prev_spos = self.rect.left
                        min_spos = self.parent.rect.left + SB_ENDCAPSIZE_11
                        slider_len = self.rect.width
                    else:
                        prev_spos = self.rect.top
                        min_spos = self.parent.rect.top + SB_ENDCAPSIZE_11
                        slider_len = self.rect.height

                    # debug code
                    if self.horizontal:
                        px_size = self.parent.rect.width
                    else:
                        px_size = self.parent.rect.height
                    px_size -= (2 * SB_ENDCAPSIZE_11)
                    px_size -= slider_len
                    if px_size != self.px_range: print("ERR: px_size=" + repr(px_size) + " but px_range=" + repr(self.px_range) + ". slider_len=" + repr(slider_len))
                    assert(px_size == self.px_range)

                    new_spos = prev_spos + amt_moved
                    max_spos = min_spos + self.px_range
                    if new_spos < min_spos:
                        amt_moved = min_spos - prev_spos
                        new_spos = min_spos
                    elif new_spos > max_spos:
                        amt_moved = max_spos - prev_spos
                        new_spos = max_spos
                    if amt_moved != 0:
                        if self.horizontal:
                            # this is a horizontal scrollbar slider, being dragged
                            self.move((amt_moved, 0))
                            self.previous_mouse_pos = (prev_mpos + amt_moved, self.previous_mouse_pos[1])
                        else:
                            # vertical scrollbar slider, being dragged
                            self.move((0, amt_moved))
                            self.previous_mouse_pos = (self.previous_mouse_pos[0], prev_mpos + amt_moved)
                        if hasattr(self.parent, 'value_to_pixel_ratio'):
                            self.parent.value = (new_spos - min_spos) * self.parent.value_to_pixel_ratio
                        self.parent.update(by_dragging=True)  # need to repaint the scrollbar
                        self.accumulate_amt_moved += amt_moved
                        changed = True
            else:
                # button isn't down, but we still need to show focus when mouse
                # pointer moves in, lose it when mouse pointer moves out.
                if self.top_collidepoint(ev.pos):
                    if not self.hasmousefocus:
                        # user just moved the mouse over this button
                        self.set_bgcolor(self.color_hover)  # render the up-state hovering button image
                        self._3D_up()
                        self.hasmousefocus = True
                else:
                    if self.hasmousefocus:
                        # user just moved the mouse away from this button
                        self.set_bgcolor(self.color_up)  # render the up-state non-hovering button image
                        self._3D_up()
                        self.hasmousefocus = False
            if (self.accumulate_amt_moved != 0) and not pygame.event.peek(MOUSEMOTION):
                self.accumulate_amt_moved = 0
                # print("dbg: slider-click, parent.value=" + repr(self.parent.value))
                self.click()  # slider buttons don't generate clicks except when dragged
            # MOUSEMOTION events can affect more than one widget, so return rc=False

        elif (ev.type == MOUSEBUTTONDOWN) and (ev.button == MOUSEBUTTONLEFT) and self.top_collidepoint(ev.pos):
            self.set_bgcolor(self.color_dn)  # render the down-state button image
            self._3D_dn()
            self.isdown = True
            self.hasmousefocus = True
            self.previous_mouse_pos = ev.pos  # remember position, so we can tell how much it moved
            # send internal-use-only widget event to tell text-entry widgets that they've lost keyboard focus
            tmpev = pygame.event.Event( WIDGETEVENT, {'Id':'KBDFOCUS', 'sender':self, 'internal':True} )
            notify_all_widgets(tmpev)
            rc = True  # no other widgets need to receive this event

        elif (ev.type == MOUSEBUTTONUP) and (ev.button == MOUSEBUTTONLEFT):
            self.set_bgcolor(self.color_hover)  # render the up-state hovering button image
            self._3D_up()
            if self.isdown:
                self.isdown = False
                if self.slider_dragging:
                    if self.accumulate_amt_moved:
                        # this doesn't happen often, but it's possible if user gets wild with the mouse
                        self.accumulate_amt_moved = 0
                        self.click()  # slider buttons don't generate clicks except when dragged
                        # print("dbg: slider-click generated on mousebuttonup")
                    self.slider_dragging = False
            if self.top_collidepoint(ev.pos):
                self.hasmousefocus = True
            self.previous_mouse_pos = None
            rc = True  # no other widgets need to receive this event

        Widget.notify(self, ev)  # for mouse cursor handling
        return rc


class ScrollBar(BasicForm):
    '''A horizontal or vertical scroll bar widget.

    If slider_size is None, then the slider button is fixed-size 15x15.
    Otherwise, slider_size should be between 1 and 99, specified as the
    desired percentage of the range of values.

    The .value attribute is the floating-point number that gets changed
    when the scroll bar is adjusted.  Conversely, your program can move the
    scroll bar simply by changing the .value attribute.

    Specify min_val & max_val to set the range of values (default is 0.0-100.0).

    Specify small_inc to indicate how much .value changes when one of the
    little arrows is clicked at the end of the scroll bar.

    Specify large_inc to indicate how much .value changes when the space is
    clicked between the slider and the little arrow.

    The default is a vertical scroll bar; if you want a horizontal scroll bar
    then pass horizontal=True.

    Specify the length of the scroll bar by the size= parameter.

    The ScrollBar widget tells the application when the user changes .value,
    by generating a pygame event.
    '''
    def __init__(self, value=0.0, min_val=0.0, max_val=100.0, horizontal=False,
                 small_inc=5.0, large_inc=25.0, size=250, pos=(0,0), Id='scrollbar'):
        if size < 42:
            size = 42  # minimum length of a scroll bar
        if horizontal:
            rect = pygame.Rect(pos, (size,17))
        else:
            rect = pygame.Rect(pos, (17,size))  # all scrollbars are 17 pixels wide
        bgcolor = (237,237,237)  # light grey
        boxcolors = (215,215,215)  # slightly darker grey
        BasicForm.__init__(self, rect=rect, bgcolor=bgcolor,
                           boxcolors=boxcolors, Id=Id)
        self.prev_value = self.value = float(value)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.slider_size = None  # None means fixed-size slider button
        self.small_inc = float(small_inc)
        self.large_inc = float(large_inc)
        self.horizontal = horizontal
        self.use_this_mouse_cursor = default_mouse_cursor
        self.value_to_pixel_ratio = 1.0  # this gets fixed by .update()
        # a scrollbar consists of 5 buttons: a slider (b3), end arrows (b1 & b5), and the gaps between (b2 & b4)
        if horizontal:
            b1 = SimpleButton(image=scroll_left, pos=(SB_BORDER_1,SB_BORDER_1), size=(SB_ARROWSIZE_10,SB_CHANNEL_WIDTH_15),
                              pic_pos=(3,4), Id='dec.'+self.Id,
                              border=0, internal=True)
            b2 = SimpleButton(bgcolor=bgcolor, pos=(SB_ENDCAPSIZE_11,SB_BORDER_1), size=(1,SB_CHANNEL_WIDTH_15),
                              Id='big_dec.'+self.Id,
                              border=0, internal=True)
            b3 = SliderButton(image=scroll_horizontal, pos=(12,SB_BORDER_1), size=(SB_CHANNEL_WIDTH_15,SB_CHANNEL_WIDTH_15),
                              pic_pos=(3,4), Id='slider.'+self.Id, three_D=True,
                              border=0, internal=True, horizontal=True)
            b4 = SimpleButton(bgcolor=bgcolor, pos=(29,SB_BORDER_1), size=(1,SB_CHANNEL_WIDTH_15),
                              Id='big_inc.'+self.Id,
                              border=0, internal=True)
            b5 = SimpleButton(image=scroll_right, pos=(rect.width-SB_ENDCAPSIZE_11,SB_BORDER_1), size=(SB_ARROWSIZE_10,SB_CHANNEL_WIDTH_15),
                              pic_pos=(3,4), Id='inc.'+self.Id,
                              border=0, internal=True)
        else:
            b1 = SimpleButton(image=scroll_up, pos=(SB_BORDER_1,SB_BORDER_1), size=(SB_CHANNEL_WIDTH_15,SB_ARROWSIZE_10),
                              pic_pos=(4,3), Id='dec.'+self.Id,
                              border=0, internal=True)
            b2 = SimpleButton(bgcolor=bgcolor, pos=(SB_BORDER_1,SB_ENDCAPSIZE_11), size=(SB_CHANNEL_WIDTH_15,1),
                              Id='big_dec.'+self.Id,
                              border=0, internal=True)
            b3 = SliderButton(image=scroll_vertical, pos=(SB_BORDER_1,12), size=(SB_CHANNEL_WIDTH_15,SB_CHANNEL_WIDTH_15),
                              pic_pos=(4,3), Id='slider.'+self.Id, three_D=True,
                              border=0, internal=True, horizontal=False)
            b4 = SimpleButton(bgcolor=bgcolor, pos=(SB_BORDER_1,29), size=(SB_CHANNEL_WIDTH_15,1),
                              Id='big_inc.'+self.Id,
                              border=0, internal=True)
            b5 = SimpleButton(image=scroll_down, pos=(SB_BORDER_1,rect.height-SB_ENDCAPSIZE_11), size=(SB_CHANNEL_WIDTH_15,SB_ARROWSIZE_10),
                              pic_pos=(4,3), Id='inc.'+self.Id,
                              border=0, internal=True)
        b3.set_boxcolors( color=((210,210,220),(110,110,120)) )  # 3D border colors for slider
        self.b3 = b3  # slider
        self.add_widgets(b1,b2,b3,b4,b5)
        self.update()

    def notify(self, ev):
        rc = False
        if (ev.type == WIDGETEVENT) and ev.internal:
            btns = self.children.sprites()
            if (ev.Id != 'KBDFOCUS') and (ev.sender in btns):
                # it was our button!
                if ev.sender == btns[0]:
                    self.value = max( self.value-self.small_inc, self.min_val )
                elif ev.sender == btns[1]:
                    self.value = max( self.value-self.large_inc, self.min_val )
                elif ev.sender == btns[2]:
                    # slider slid
                    self.value = max( min(self.value, self.max_val), self.min_val )
                elif ev.sender == btns[3]:
                    self.value = min( self.value+self.large_inc, self.max_val )
                elif ev.sender == btns[4]:
                    self.value = min( self.value+self.small_inc, self.max_val )
                rc = True
        if rc and (self.value != self.prev_value):
            # tell the application that the user moved the scroll bar
            ev2 = pygame.event.Event( WIDGETEVENT, {'Id':self.Id, 'value':self.value, 'sender':self, 'internal':False} )
            self.prev_value = self.value
            pygame.event.post(ev2)
        elif not rc:
            rc = BasicForm.notify(self, ev)
        return rc

    def update(self, by_dragging=False):
        self._fill_bg()
        # ensure that min_val < max_val, and min_val <= value <= max_val
        self.value = float(self.value)
        if self.max_val <= self.min_val:
            self.max_val = self.min_val + 1.0
        if self.value < self.min_val:
            self.value = self.min_val
        if self.value > self.max_val:
            self.value = self.max_val
        # over how big a range can the slider/drag button slide?
        if self.horizontal:
            px_size = self.rect.width
        else:
            px_size = self.rect.height
        # 11 pixels at each end are used for arrows & border, leaving 22 fewer
        pixel_range = px_size - (2 * SB_ENDCAPSIZE_11)
        # if the range is big enough to draw a scroll bar, then draw it
        if pixel_range >= 20:
            if self.slider_size is None:
                # default slider button length is 15 pixels
                blen = 15
            else:
                # calculate button length as a percentage of total slider range
                blen = (100.0 * self.slider_size) / (self.max_val - self.min_val)
                if blen > 100.0:
                    blen = 100.0
                elif blen < 1.0:
                    blen = 1.0
                blen = int(round((blen * pixel_range) / 100.0))
                if blen < 15:
                    # minimum slider button length is 15 pixels
                    blen = 15
            # Slider/drag button is blen pixels long.  That leaves a range
            # of motion = (pixel_range - blen) pixels.
            mv_range_px = pixel_range - blen
            # if self.b3.px_range != mv_range_px: print("dbg: horizontal=" + repr(self.horizontal) + ", px_range changed from " + repr(self.b3.px_range) + " to " + repr(mv_range_px))
            self.b3.px_range = mv_range_px  # tell the slider what its range of motion is
            # conversion factor from pixels to range of values is...
            self.value_to_pixel_ratio = (self.max_val - self.min_val) / mv_range_px
            # calculate the slider/drag button position (offset from low end):
            ofs_px = int(round( mv_range_px *
                                 ((self.value - self.min_val) /
                                  (self.max_val - self.min_val)) ))

            if by_dragging:  # debug code
                if self.horizontal:
                    ofs_px1 = self.b3.rect.left - self.rect.left - SB_ENDCAPSIZE_11
                else:
                    ofs_px1 = self.b3.rect.top - self.rect.top - SB_ENDCAPSIZE_11
                if ofs_px1 != ofs_px:
                    print("ERR: ofs_px1=" + repr(ofs_px1) + ", ofs_px=" + repr(ofs_px) + ", by_dragging=" + repr(by_dragging))
                    assert(False)

            # at last, we know enough to draw the buttons
            (b1,b2,b3,b4,b5) = self.children.sprites()  #@UnusedVariable
            if self.horizontal:
                b2.rect.width = ofs_px
                b3.relative_rect.left = ofs_px + SB_ENDCAPSIZE_11
                b3.rect.width = blen
                b3.pic_pos = ((blen-9)//2, b3.pic_pos[1])
                b4.relative_rect.left = b3.rect.width + b3.relative_rect.left
                b4.rect.width = px_size - SB_ENDCAPSIZE_11 - b4.relative_rect.left
                b5.relative_rect.left = px_size - SB_ENDCAPSIZE_11  # in case of resize
            else:
                b2.rect.height = ofs_px
                b3.relative_rect.top = ofs_px + SB_ENDCAPSIZE_11
                b3.rect.height = blen
                b3.pic_pos = (b3.pic_pos[0], (blen-9)//2)
                b4.relative_rect.top = b3.rect.height + b3.relative_rect.top
                b4.rect.height = px_size - SB_ENDCAPSIZE_11 - b4.relative_rect.top
                b5.relative_rect.top = px_size - SB_ENDCAPSIZE_11  # in case of resize
            BasicForm.update(self)


def wrap_in_titlebar(widget, title='', Id=None, draggable=True, closeable=True, resizeable=None):
    '''Use a BasicForm to wrap another widget, to add a Title Bar.
    The resulting form has two children:
    [0] = the title bar, which, in turn, has one or two children:
       [0] = the caption text
       [1] = the close button (optional)
    [1] = the widget
    '''
    widget.update()  # make sure widget's rect and relative_rect are consistent
    # create a new rect that is 21 pixels taller than widget's rect
    r = Rect( (0,0), (widget.rect.width, widget.rect.height+TB_HEIGHT_21) )
    # preparing to create BasicForm widget, the size of the new rect
    boxcolors = None
    if hasattr(widget, 'boxcolors'):
        boxcolors = widget.boxcolors
        widget.boxcolors = None
    if not Id:
        tb_id = widget.Id
        f_id = 'wrapperform.' + widget.Id
    else:
        tb_id = Id
        f_id = Id
    # Both the titlebar and the wrapper form typically get the wrapped widget's
    # Id, perhaps w/ a 'title.' or 'wrapperform.' prefix.  However, to get a
    # shorter close button Id, I initially pass the widget ID without "title."
    # at the beginning, then change it.
    tb = Titlebar(title=title, width=widget.rect.width, Id=tb_id,
                        draggable=draggable, closeable=closeable)
    if not Id:
        tb_id = 'title.' + widget.Id
        tb.Id = tb_id
    if resizeable is None:
        resizeable = widget.resizeable
    f = WrapperForm(rect=r, boxcolors=boxcolors, Id=f_id)
    f.never_has_focus = True
    f.resizeable = resizeable
    # center the form on the center of the widget:
    f.rect.topleft = widget.rect.topleft
    f.relative_rect.topleft = widget.relative_rect.topleft
    widget.relative_rect.topleft = (0,TB_HEIGHT_21)
    if resizeable:
        widget.resizeable = True  # widget resizes with parent form
        f.min_width = widget.min_width
        if closeable:
            if f.min_width < 16:
                f.min_width = 16
        f.min_height = widget.min_height + TB_HEIGHT_21
        if f.min_height < (1+TB_HEIGHT_21):
            f.min_height = (1+TB_HEIGHT_21)
    # put the titlebar and the original widget into the form:
    f.add_widgets(tb, widget)
    f.titlebar = tb
    f.update()
    return f


def set_caption(wrapped_widget, title=''):
    '''Change the caption (title) in the titlebar for a "wrapped" widget --
    that is, a widget that has a titlebar added to it via wrap_in_titlebar()
    '''
    # tb = wrapped_widget.children.sprites()[0]
    wrapped_widget.titlebar.set_caption(title)


def wrap_in_border(widget, thick=1, color=BLACK, boxcolors=None, Id='border'):
    '''Example of how to use a WrapperForm to wrap another widget, to add a
    border around it.
    '''
    widget.update()  # make sure widget's rect and relative_rect are consistent
    # create a new rect that is a little bigger than widget's rect
    r = Rect( (0,0), (widget.rect.width+(2*thick), widget.rect.height+(2*thick)) )
    # create wrapper Form, the size of the new rect
    f = WrapperForm(rect=r, bgcolor=color, boxcolors=boxcolors, Id=Id,
                    draggable=widget.draggable)
    # center the form on the center of the widget:
    f.rect.center = widget.rect.center
    # f.relative_rect.center = widget.relative_rect.center  # unnecessary, since we do f.update below
    # center the widget in the form:
    widget.relative_rect.topleft = (thick, thick)
    # Drag it by dragging its wrapper (this isn't quite right -- we should be
    # able to drag by clicking either the interior widget or the border, but
    # currently we can only drag by the border)
    widget.draggable = False
    # put the widget into the form:
    f.add_widgets(widget)
    f.update()
    return f


class DialogBox(Form):
    '''A class for use by the MsgBox function.  Dialog boxes are forms which
    contain a titlebar, a label (for the message to be displayed), and buttons
    (represented by a string containing button lables separated by '|'s).

    A dialog box generates events indirectly, because its buttons generate
    events.  The button ids (passed in the generated events) are equal to the
    button labels with a dot and the dialog box id appended.  E.g., a dialogbox
    named Id=useralert with a button labeled 'OK' would generate an event with
    Id="OK.useralert" when the [OK] button is clicked.
    '''
    def __init__(self, width=100, pos=None, color=BLACK,
                 bgcolor=(240,240,255), msg='', buttons='OK',
                 boxcolors=BLACK, Id='DialogBox', title='DialogBox'):

        if None == pos:
            pos = (0,0)
        if width:
            w = width
        else:
            w = 600
        m = Label(text=msg, color=color, pos=(10,10), Id='M.'+Id)

        if w < (m.rect.width + 20):
            w = m.rect.width + 20
        if w < 30:
            w = 30
        elif w > 600:
            w = 600
        h = w // 2
        lbls = buttons.split('|')
        Form.__init__(self, rect=(pos,((w+20),h)), bgcolor=bgcolor,
                      boxcolors=boxcolors, Id=Id, title=title,thick=2)

        m.relative_rect.top = self.titlebar.rect.height + 10
        self.add_widgets(m)
        left = 10
        top = self.titlebar.rect.height + ((h-20) // 2)

        for lbl in lbls:
            button = Button(text=lbl, pos=(left,top), three_D=True, Id=lbl+'.'+Id)
            self.add_widgets(button)
            left += (w // len(lbls))


def modal_popup(widget, bg_repaint=None):
    '''Usually, widgets are displayed and active along with everything else
    in the application, but it is also possible to display a widget "modally,"
    that is, with everything else suspended.  To do so, just pass the widget
    to this function.  It won't return until the widget generates a result
    event.

    A result event is any event of type WIDGETEVENT which has an attribute
    .internal=False.

    Note: don't use this with a widget which can't generate events (like
    a Label), lest it never return!  (Humming Kingston Trio tune...)

    If you use this with a draggable or resizeable widget, you can optionally
    pass a function as bg_repaint, to repaint the background when the widget
    moves.  If you don't, then modal_popup will just save a copy of the
    display surface, and use that to repaint the background.  I thought that
    using a bg_repaint function would work better when the main window was
    resized, but it doesn't seem to make any difference.
    '''
    #widget = wrap_in_border(widget, thick=3, color=BLACK, boxcolors=None)
    bkground_repaints_needed = widget.resizeable or widget.draggable
    if (not bkground_repaints_needed) and hasattr(widget,'titlebar') and (widget.titlebar is not None):
        bkground_repaints_needed = widget.titlebar.resizeable or widget.titlebar.draggable
    group = WidgetGroup(widget)  # a temporary group, for duration of this popup

    screen = pygame.display.get_surface()
    if not bg_repaint:
        # save a copy of the display surface, for repainting the background
        sv_bg = screen.copy()
    keep_running = True
    while keep_running:
        # Update and Draw the screen with the widget on top
        if bkground_repaints_needed:
            if bg_repaint:
                # repaint by calling the bg_repaint function
                bg_repaint()
            else:
                # or repaint by copying the saved background display surface
                screen.blit(sv_bg, (0,0))
        group.update()
        group.draw(screen)
        pygame.display.update()
        # get next event.  (But QUIT is special, so we leave it in the queue.)
        if pygame.event.peek(QUIT):
            event = pygame.event.Event(QUIT)
            keep_running = False
            # If event is QUIT then they closed the whole application, so we
            # could just pygame.quit() and sys.exit(0).  But that wouldn't give
            # the application a chance to see the QUIT event and do cleanup
            # before exiting.
        else:
            event = pygame.event.wait()
            # Give widget a look at the event
            group.notify(event)
            # We loop until we get a result event from the widget
            if event.type == WIDGETEVENT:
                if hasattr(event,'internal') and not event.internal:
                    # we got a result!
                    group.remove(widget)
                    keep_running = False  # we're done

    # repaint the screen w/o the widget
    if bg_repaint:
        bg_repaint()
    else:
        screen.blit(sv_bg, (0,0))
    pygame.display.update()
    return event


def MsgBox(msg='', title='MsgBox', buttons='OK', Id='MsgBox', width=100,
           pos=None, draggable=True, bg_repaint=None):
    '''Pop up a modal message box.

    The buttons parameter is a string containing '|' characters to separate the
    button names.  E.g., buttons='Yes|No|Cancel' will result in three buttons.

    If pos is unspecified, then the message box will be centered.

    The optional bg_repaint function can be used to repaint the background
    when the user drags around the message box, but it isn't necessary,
    because the alternate approach of just saving and restoring the display
    surface seems to work fine.
    '''
    box = DialogBox(width=width, pos=pos, msg=msg, Id=Id, title=title, buttons=buttons)

    box.titlebar.draggable = box.draggable = draggable
    if None == pos:
        # if pos is unspecified, then center the MsgBox on the screen
        screen = pygame.display.get_surface()
        (s_width, s_height) = screen.get_size()
        (mb_width, mb_height) = box.rect.size
        x = max(1, (s_width-mb_width) // 2)
        y = max(1, (s_height-mb_height) // 2)
        pos = (x, y)
        box.rect.left = pos[0]
        box.rect.top = pos[1]
    evt = modal_popup(box, bg_repaint=bg_repaint)
    return evt




