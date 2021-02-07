# ---- GUIpygame DEMO ----
# display debugging messages on console
DEBUG = False

import sys  #@UnusedImport
import os
import pygame
from pygame.locals import *  #@UnusedWildImport

import GUIpygame
from GUIpygame import vera,WidgetGroup,Widget,Label,SimpleButton,Button,TextEditBox,Menu,Form
from GUIpygame import wrap_in_border,InputBox
from GUIpygame import WIDGETEVENT,MOUSEBUTTONLEFT,MOUSEBUTTONRIGHT,button_up_color,button_dn_color

if __name__ == '__main__':

    # Names of pygame event types:
    _evnam = { NOEVENT:'NOEVENT', ACTIVEEVENT:'ACTIVEEVENT', KEYDOWN:'KEYDOWN',  # 0-2
               KEYUP:'KEYUP', MOUSEMOTION:'MOUSEMOTION',                         # 3,4
               MOUSEBUTTONDOWN:'MOUSEBUTTONDOWN', MOUSEBUTTONUP:'MOUSEBUTTONUP', # 5,6
               JOYAXISMOTION:'JOYAXISMOTION', JOYBALLMOTION:'JOYBALLMOTION',     # 7,8
               JOYHATMOTION:'JOYHATMOTION', JOYBUTTONDOWN:'JOYBUTTONDOWN',       # 9,10
               JOYBUTTONUP:'JOYBUTTONUP', QUIT:'QUIT', SYSWMEVENT:'SYSWMEVENT',  # 11-13
               VIDEORESIZE:'VIDEORESIZE', VIDEOEXPOSE:'VIDEOEXPOSE',             # 16,17
               USEREVENT:'USEREVENT', NUMEVENTS:'NUMEVENTS' }                    # 24,32
    # Commented numbers are for SDL 1.2.  They'll be very different in SDL 1.3.
    # see also SDL-1.2.14\include\SDL_events.h

    def event_name(evtype):
        '''Return a Simple DirectMedia Layer (SDL) displayable name for a
        pygame/SDL event type number.

        Designed for SDL 1.2, but it won't break with SDL 1.3.  Names are
        derived from SDL_EventType in SDL_events.h, but without the "SDL_"
        at the beginning of each name.
        '''
        try:
            result = _evnam[evtype]
        except:
            if evtype in range(USEREVENT, NUMEVENTS):
                result = 'USEREVENT+' + repr(evtype-USEREVENT)
            elif evtype >= NUMEVENTS:
                result = 'ILLEGAL_EVENT_' + repr(evtype)
            else:
                result = 'UNKNOWN_EVENT_' + repr(evtype)
                if 12 == QUIT:
                    # this pygame is still based on SDL 1.2
                    if evtype == 14:
                        result = 'EVENT_RESERVEDA'
                    elif evtype == 15:
                        result = 'EVENT_RESERVEDB'
                    elif evtype in range(18, 24):
                        result = 'EVENT_RESERVED' + repr(evtype-16)
                # else this must be the new SDL 1.3
        return result


    hand = (
    "        XXXXXXXXXXX             ",
    "      .X.....X..X.X             ",
    "      X.......X..X.X            ",
    "     X...XX....X..X.X           ",
    " XXXXX..XXXXXXX.X..X.X          ",
    "XXXXXXXXXXXXXXX......X          ",
    "     X..X   X........X          ",
    "     X...XXXX........X          ",
    "     X...............X          ",
    "      X..............X          ",
    "       X.............X XX       ",
    "        X............XX.XX      ",
    "         X..........X..X.XX     ",
    "          XXXXXX...X..X.X.X     ",
    "                XXX..X.X.X      ",
    "                  X.X.X.X       ",
    "                  XX.X.X        ",
    "                  X.X.X         ",
    "                   X.X          ",
    "                    X           ",
    "                                ",
    "                                ",
    "                                ",
    "                                ")
    d_tuple, m_tuple = pygame.cursors.compile(hand, black='.', white='X')  # '.' & 'X' swapped due to pygame bug
    hand_mouse_cursor = ((32,24), (0,5), d_tuple, m_tuple)

    # import os  # module os is needed to access environment variables
    import re  # regular expressions

    try:
        vera_big = pygame.font.Font('Vera.ttf', 36)
        vera_med = pygame.font.Font('Vera.ttf', 18)
    except:
        vera_big = pygame.font.SysFont('arial,microsoftsansserif,courier', 36)
        vera_med = pygame.font.SysFont('arial,microsoftsansserif,courier', 18)

    fullscreen_sz = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    # print( 'dbg: screen size =', fullscreen_sz )
    width, height = 800, 450  # for screens 800x600 or larger

# change size of pygame window depending on size of device screen
    # if width > (fullscreen_sz[0]-20):
    #     width = fullscreen_sz[0]-20
    # if width < (3*fullscreen_sz[0]//4):
    #     width = 3*fullscreen_sz[0]//4
    # if height > (fullscreen_sz[1]-20):
    #     height = fullscreen_sz[1]-20
    # if height < (3*fullscreen_sz[1]//4):
    #     height = 3*fullscreen_sz[1]//4
    scrsize = (width, height)

    # Tell GUI that we only partially redraws the screen each time
    # through the main event/draw loop
    GUIpygame.partial_redraw_mode()

    # initially center the pygame window by setting %SDL_VIDEO_WINDOW_POS%
    window_pos_left = 1 + ((fullscreen_sz[0] - width) // 2)
    window_pos_top = 1 + ((fullscreen_sz[1] - height) // 2)
    os.environ['SDL_VIDEO_WINDOW_POS'] = '{0},{1}'.format(window_pos_left, window_pos_top)

    screen = pygame.display.set_mode(scrsize, RESIZABLE)

    # I'm surprised this doesn't seem to be necessary for alpha-channel transparency:
    # screen = pygame.display.set_mode(scrsize, RESIZABLE|SRCALPHA)
    # screen.convert_alpha()

    os.environ['SDL_VIDEO_WINDOW_POS'] = ''
    # if you don't clear the environment variable, the window will reposition
    # every time pygame.display.set_mode() gets called due to a VIDEORESIZE event.


    # sounds
    cameraclick = pygame.mixer.Sound(GUIpygame.rel2me("CAMERA.WAV"))
    click = pygame.mixer.Sound(GUIpygame.rel2me("CLICK.WAV"))
    click.play()
    pygame.key.set_repeat(500, 50)  # make keyboard repeat work

    # we'll store mouse position here:
    mx, my = pygame.mouse.get_pos()  # current (initial) position of mouse cursor

    # instructions, centered at the top of the screen
    line0 = Label( "This is a resizeable window", pos=(0,5), color=(0,0,220), font=vera_big)
    line0.rect.centerx = screen.get_size()[0] // 2

    line1 = Label( "Right-click=pop-up menu,  [space]=save screenshot.jpg,  [Esc]=quit", pos=(0,line0.rect.bottom+5), color=(240,0,0) )
    line1.set_text(line1.text, adjustwidth=True)
    line1.rect.centerx = screen.get_size()[0] // 2
    instructions_w = line1.rect.width

    mousepos = Label(repr((mx,my)), pos=(line1.rect.left,line1.rect.bottom+5), color=(0,40,120))

    mouseclick = Label(' '*20, pos=(line1.rect.left,mousepos.rect.bottom+5), color=(0,40,120), padding=2)
    mouseclick.set_boxcolors((150,255,150))

    line3 = Label( "(Here's where we'll show the results)", pos=(line1.rect.left,mouseclick.rect.bottom+5), color=(0,40,120), bgcolor=(255,240,100),font=vera_med )

    sprite_group = pygame.sprite.Group( line0, line1, mousepos, mouseclick, line3 )

    widget_group = WidgetGroup()

    # A singleton button
    button1 = Button( 'Button#1', pos=(30,100) )
    button1.set_border(4)
    button1.draggable = True
    # use nested forms to create a colorful "picture frame" around button#1
    button1 = wrap_in_border(button1, thick=3, color=(10,255,10)) #green
    button1 = wrap_in_border(button1, thick=3, color=(255,0,0)) # red
    button1 = wrap_in_border(button1, thick=4, color=(20,20,255), boxcolors=GUIpygame.BLACK) #blue

    # Another singleton button, positioned 5 pixels to the right of the first
    button3 = Button( 'Button#3', pos=(5+button1.rect.right,100) )
    button3.set_border(4)

    # another singlton button, just beneath the first
    button2 = Button( 'ShowMessagebox', pos=(30,135), three_D=True )
    button2.set_border(4)
    # button2.set_boxcolors( color=((255,200,200),(196,0,0)) )  # our 3D border colors are pink and dark red

    # A four-item menu, the hard way
    menuitem1 = SimpleButton('New')
    menuitem2 = SimpleButton('Open')
    menuitem3 = SimpleButton('Save')
    menuitem3.set_colors(fg=(128,128,128))  # grey (could indicate "disabled")
    menuitem4 = SimpleButton('Exit')
    a4itemMenu = Menu(Id='a4itemMenu')
    a4itemMenu.add_widgets(menuitem1, menuitem2, menuitem3, menuitem4)
    a4itemMenu.rect.topleft = (60, 0)

    # a 9-item menu, the easy way (we'll use this as a right-click pop-up menu)
    menu = Menu.ActionMenu( 'create node|remove node|move node from|move node to|'
                                 +'create arc from|create arc to|edit arc name|'
                                 +'edit FSM name|cancel' )

    tb_menu = GUIpygame.wrap_in_titlebar(menu, 'Pop-up menu', closeable=True, draggable=True, Id='popup_menu')

    # a little black 6x6 pixel square, in the upper left corner
    junk = Widget()
    junk.rect = pygame.Rect(0,0, 6,6)
    junk.image = pygame.Surface((6,6))

    # a picture, with a light green background and border:
    apicture = pygame.image.load(GUIpygame.rel2me('GUIpygame.png'))
    image1 = GUIpygame.Image(apicture, pos=(30,380), bgcolor=(0,255,100), padding=4)

    # This textbox has a transparent background except while you're editing it
    textbox1 = TextEditBox( 'editable transparent', maxlen=30, width=180,
                               pos=(30,165), Id='textbox1' )

    # This textbox has an light-green opaque background
    textbox2 = TextEditBox( 'editable opaque', maxlen=30, width=180,
                               pos=(30,190), bgcolor=(240,255,240),
                               Id='textbox2' )
    textbox2.set_boxcolors((225,225,225))  # give it a light grey border
    textbox2.draggable = True

    ckbox1 = GUIpygame.SimpleCheckbox(Id='ckbox1', pos=(30,210), checked=False)

    # silly demo
    title_counter = 0

    # Now we're going to create a form with a red box around it:
    #                             left,top width,height           R   G   B                R  G B
    form = GUIpygame.BasicForm( rect=((250,150),(340,230)), bgcolor=(255,240,240), boxcolors=(255,0,0), Id='bigform' )
    # Create various widgets to go inside the form.  (Positions are relative to the form.)
    form_l1 = Label('This is a form', pos=(1,5), color=(220,0,0))
    form_l1.relative_rect.centerx = form.rect.width // 2  # center it
    form_b1 = Button('Increment', pos=(50,55), three_D=True)
    form_b1.set_border(6)
    form_b2 = Button('Decrement', pos=(140,55), three_D=True)
    form_b2.set_border(6)
    form_b3 = Button('Double', pos=(230,55), three_D=True)
    form_b3.set_border(6)
    form_t1 = TextEditBox('edit me!', maxlen=30, width=200, pos=(60,90), bgcolor=(230,255,255), Id='textbox_in_form')
    # A Q&A widget, similar to a specialized BasicForm
    form_l2 = Label("Here's a Q&A (specialized form) within the form:", pos=(100,125))
    form_l2.relative_rect.centerx = form.rect.width // 2  # center it


    hbar = GUIpygame.ScrollBar(size=200, pos=(65,30), horizontal=True, min_val=0, max_val=100, Id='hbar')
    hbar.slider_size = 25  # 25% of total range

    qa = InputBox(question='How tall are you (in inches)?', answer='''5'10"''', Id='textbox_howtall')
    qa.relative_rect.midtop = (form.rect.width//2, 140)
    qa = GUIpygame.wrap_in_titlebar(qa, 'a title for the height question & answer', closeable=True, draggable=True, Id='textbox_howtall')
    qa.resizeable = 'byMouse'
    qa.min_height = 22
    qa.min_width = 16
    # Add the widgets to the form
    form.add_widgets(form_l1, form_b1, form_b2, form_b3, form_t1, form_l2, qa, hbar)

    # Now create a form with a blue box around it
    form2 = Form( rect=((600,150),(160,230+21)), bgcolor=(255,230,230), boxcolors=(0,0,255), Id='rightform', title='This is a non-basic form')
    form2_b1 = Button('Draggable button', pos=(20,50+21), border=5, three_D=True)
    form2_b1.draggable = True
    ckbox2 = GUIpygame.Checkbox(Id='ckbox2', pos=(10,190), checked=False, text='Checkbox 2', bgcolor=(250,222,255), padding=10, boxcolors=(0,255,0))
    #ckbox2.draggable = True
    form2.add_widgets(form2_b1,ckbox2)
    form2.resizeable = 'byMouse'

    form = GUIpygame.wrap_in_titlebar(form, 'a title for the form, which is very long so that I can see it get truncated', resizeable = 'byMouse')


    # # We don't actually need to do an update here, but it fixes the rects so debug prints look right
    # form.update()
    # # Debug prints:
    # print('form=' + repr(form))
    # print('  form_b1=' + repr(form_b1))
    # print('  form_b2=' + repr(form_b2))
    # print('  form_b3=' + repr(form_b3))
    # print('  form_t1=' + repr(form_t1))
    # print('  qa=' + repr(qa))

    # scroll bars
    vbar = GUIpygame.ScrollBar(size=100, pos=(100,240))


    # Add all the widgets (except the pop-up menu) to the widget group, so they'll be active
    widget_group.add( button1, image1, button2, button3, junk, textbox1, textbox2, ckbox1, a4itemMenu, form, form2, vbar)

    # print('later than button1 = ' + repr(widget_group.sprites_painted_after(button1)))
    # print('later than a4itemMenu = ' + repr(widget_group.sprites_painted_after(a4itemMenu)))
    # print('later than form = ' + repr(widget_group.sprites_painted_after(form)))

    # test mouse cursors
    # pygame.mouse.set_cursor( *sizer_xy_mouse_cursor )
    # pygame.mouse.set_cursor( *sizer_y_mouse_cursor )
    # pygame.mouse.set_cursor( *sizer_x_mouse_cursor )
    # pygame.mouse.set_cursor( *sizer_yx_mouse_cursor )
    pygame.mouse.set_cursor( *hand_mouse_cursor )

    def draw_everything():
        '''Redraw the screen and everything on it.'''
        global screen, sprite_group, widget_group
        screen.fill( (255,255,230) )  # off-white/ivory background
        for group in (sprite_group, widget_group):
            group.update()
            group.draw(screen)

    #result = GUIpygame.MsgBox('Click OK to close this draggable box', 'message box title', 'OK|Close|Cancel', bg_repaint=draw_everything )
    #line3.set_text( 'modal_popup result = pressed button = ' + repr(result.Id), adjustwidth=True )

    #result = GUIpygame.MsgBox('Click OK to close this box', 'message box title', 'OK|Close|Cancel' )
    #line3.set_text( 'modal_popup result = pressed button = ' + repr(result.Id), adjustwidth=True )


    # ----------- TOP OF MAIN PYGAME EVENT LOOP -----------
    keep_running = True
    while keep_running:
        # get next event:
        event = pygame.event.wait()

        if event.type != MOUSEMOTION and DEBUG:
            print('dbg: ' + repr(event) + ' .dict=' + repr(event.dict))

        # If user clicked the main window's close "X" or pressed the ESC key then quit
        if ( (event.type == QUIT) or
             ((event.type == KEYDOWN) and (event.key == K_ESCAPE)) ):
            keep_running = False
            break

        # Give widgets a look at the event
        event_handled_by_widget = widget_group.notify(event)
        if not event_handled_by_widget:
            # if widget(s) handled the event, we're probably done with it

            # otherwise, handle it in our application
            if ((event.type == MOUSEBUTTONDOWN) and
                 ((event.button == MOUSEBUTTONLEFT) or (event.button == MOUSEBUTTONRIGHT))):
                # left or right mouse button
                mx, my = event.pos  # position of mouse cursor at time of mouse click
                mouseclick.set_text(repr((mx,my)) + '   button=' + repr(event.button), adjustwidth=True)
                if event.button == MOUSEBUTTONLEFT:
                    click.play()  # make a "click" noise
                elif event.button == MOUSEBUTTONRIGHT:
                    # pop-up a menu!
                    tb_menu.rect.topleft = (mx,my)  # position menu on the screen (at mouse position)

                    # we can pop up the menu either modally or non-modally; this is modal:
                    result = GUIpygame.modal_popup(tb_menu, draw_everything)  # modal pop-up
                    line3.set_text( 'modal_popup result = pressed button = ' + repr(result.Id), adjustwidth=True )

                    # widget_group.add(tb_menu)  # non-modal pop-up; result goes in the event queue

            elif event.type == MOUSEMOTION:
                # as user moves the mouse cursor around, display X,Y, and a
                # list of the stack of widgets under the mouse cursor
                mx, my = event.pos  # position of mouse cursor
                topwidg = GUIpygame.list_of_focusable_widgets_at_mouse(GUIpygame.sorted_draw_list, (mx,my))
                tmp = ', '.join([x.Id+'/tc='+repr(x.top_collidepoint(event.pos)) for x in topwidg])  # list comprehension!
                mousepos.set_text(repr((mx,my)) + ' #' + repr(len(topwidg)) + ' ' + tmp, adjustwidth=True)
            elif event.type == KEYDOWN and event.key == K_SPACE:
                # spacebar saves a screenshot
                cameraclick.play()  # make camera-click sound
                pygame.image.save(screen,"screenshot.jpg")  # extension can be bmp, jpg, png, or tga (but not gif)
                # note: screenshot does not include the mouse cursor
            elif event.type == VIDEORESIZE:
                # this program is in a resizeable main window; this event happens when it's resized
                scrsize = event.size  # or event.w, event.h
                screen = pygame.display.set_mode(scrsize,RESIZABLE)
            elif (event.type == WIDGETEVENT) and not event.internal:
                # These are events generated by GUIpygame widget sprites
                if re.match('^textbox', str(event.Id)):
                    # The user typed some text into a textbox widget, and pressed [Enter]
                    line3.set_text( 'widget result event, Id=' + event.Id + ', text="' + event.text + '"', adjustwidth=True )
                elif hasattr(event,'checked'):
                    # The user checked or unchecked a checkbox widget
                    line3.set_text( 'widget checkbox event:  Id=' + repr(event.Id) + ', checked=' + repr(event.checked), adjustwidth=True )
                else:
                    # The user clicked a button widget (note: event actually fires when mouse button is released)
                    line3.set_text( 'widget button event:  pressed button=' + repr(event.Id), adjustwidth=True )
                # close menu (if it is popped up):
                widget_group.remove(menu)
                if 'Exit' == event.Id:
                    # one of the buttons (part of a menu) is named 'Exit' -- guess what it does?
                    keep_running = False
                    break
                elif event.Id == 'close.bigform':
                    # they clicked the close button on the big form
                    widget_group.remove(form)
                elif event.Id == 'close.rightform':
                    # they clicked the close button on the righthand form
                    widget_group.remove(form2)
                elif event.Id == 'close.textbox_howtall':
                    # they clicked the close button on the little form
                    form.remove_nested_widgets(qa)
                    # we must call remove_nested_widgets() instead of remove_widgets()
                    # because form was wrapped by wrap_in_titlebar()
                elif event.Id == 'hbar':
                    # if user moved the horizontal scroll bar, copy the new value to a counter
                    title_counter = hbar.value
                elif event.Id == 'Increment':
                    # "Increment" button increments the counter
                    title_counter += 1
                elif event.Id == 'Decrement':
                    # "Decrement" button decrements the counter
                    title_counter -= 1
                elif event.Id == 'Double':
                    # "Double" button doubles the counter
                    title_counter *= 2
                elif event.Id == 'ShowMessagebox':
                    result = GUIpygame.MsgBox('Click OK to close this draggable box', 'message box title', 'OK|Close|Cancel', bg_repaint=draw_everything )
                    line3.set_text( 'modal_popup result = pressed button = ' + repr(result.Id), adjustwidth=True )
                # display the counter in the titlebar for the big form
                GUIpygame.set_caption(form, 'title_counter=' + repr(title_counter))
                # and copy the counter back to the scrollbar value, so that the
                # "Increment," "Decrement," and "Double" buttons will move the
                # scroll bar slider:
                hbar.value = title_counter


        # reposition some things, in case of VIDEORESIZE
        left_x = (scrsize[0]+1-instructions_w) // 2
        if left_x < (a4itemMenu.rect.right + 5):
            left_x = (a4itemMenu.rect.right + 5)  # don't overlap the menu
        for line in (line1, mousepos, line3):
            line.rect.left = left_x
        mouseclick.rect.left = left_x
        line0.rect.centerx = screen.get_size()[0] // 2

        # Tell GUIpygame that we're about to clear the screen
        GUIpygame.screen_is_cleared()

        # clear the screen and redraw everything
        draw_everything()

        # Update the display window
        pygame.display.update()

    # ----------- BOTTOM OF MAIN PYGAME EVENT LOOP -----------

    pygame.quit()
    # sys.exit(0)  -- unnecesary, if we just drop off the end
