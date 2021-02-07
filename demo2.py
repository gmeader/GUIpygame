import sys
import pygame
from pygame.locals import *
import os  # module os is needed to access environment variables
import re  # regular expressions
import GUIpygame
from GUIpygame import vera,WidgetGroup,Widget,Label,SimpleButton,Button,TextEditBox,Menu,Form
from GUIpygame import wrap_in_border,InputBox
from GUIpygame import WIDGETEVENT,MOUSEBUTTONLEFT,MOUSEBUTTONRIGHT,button_up_color,button_dn_color


if __name__ == '__main__':

    # ---- DEMO ----

    fullscreen_sz = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    # print( 'dbg: screen size =', fullscreen_sz )
    width,height = 792,534  # for screens 800x600 or larger
    if width > (fullscreen_sz[0]-20):
        width = fullscreen_sz[0]-20
    if width < (3*fullscreen_sz[0]//4):
        width = 3*fullscreen_sz[0]//4
    if height > (fullscreen_sz[1]-20):
        height = fullscreen_sz[1]-20
    if height < (3*fullscreen_sz[1]//4):
        height = 3*fullscreen_sz[1]//4
    scrsize = (width,height)


    # initially center the pygame window by setting %SDL_VIDEO_WINDOW_POS%
    window_pos_left = 1 + ((fullscreen_sz[0] - width) // 2)
    window_pos_top = 1 + ((fullscreen_sz[1] - height) // 2)
    os.environ['SDL_VIDEO_WINDOW_POS'] = '{0},{1}'.format(window_pos_left, window_pos_top)

    screen = pygame.display.set_mode(scrsize, RESIZABLE)

    background_color = (255,255,230)  # off-white/ivory background

    # I'm surprised this doesn't seem to be necessary for alpha-channel transparency:
    # screen = pygame.display.set_mode(scrsize, RESIZABLE|SRCALPHA)
    # screen.convert_alpha()

    cameraclick = pygame.mixer.Sound("CAMERA.WAV")
    click = pygame.mixer.Sound("CLICK.WAV")

    os.environ['SDL_VIDEO_WINDOW_POS'] = ''
    # if you don't clear the environment variable, the window will reposition
    # every time pygame.display.set_mode() gets called due to a VIDEORESIZE event.


    instructions = vera.render( "Left-click=create-node, Right-click=del-or-menu, [space]=save screenshot.jpg", True, (0,40,120) )
    instructions_w = instructions.get_size()[0]
    instructions_h = instructions.get_size()[1]
    line2_text = ""
    line2 = vera.render(line2_text, True, (0,40,120))

    line3 = Label( "line3: a pygame.sprite", (120,50), (0,40,120), button_dn_color )
    line3.set_width(line3.rect.width * 5 // 2)

    sprite_group = pygame.sprite.Group( line3 )

    widget_group = WidgetGroup()

    # A singleton button
    button1 = Button( 'Button#1', pos=(30,100) )
    button1.set_border(4)
    # use nested forms to create a colorful "picture frame" around button#1
    button1 = wrap_in_border( button1, thick=3, color=(10,255,10) )
    button1 = wrap_in_border( button1, thick=3, color=(255,0,0) )
    button1 = wrap_in_border( button1, thick=4, color=(20,20,255), boxcolors=(0,0,0) )

    # Another singleton button, positioned 5 pixels to the right of the first
    button3 = Button( 'Button#3', pos=(5+button1.rect.right,100) )
    button3.set_border(4)

    # another singlton button, just beneath the first
    button2 = Button( 'Button#2', pos=(30,135), three_D=True )
    button2.set_border(4)
    # button2.set_boxcolors( color=((255,200,200),(196,0,0)) )  # our 3D border colors are pink and dark red

    # A four-item menu, the hard way
    menuitem1 = SimpleButton('Cut')
    menuitem2 = SimpleButton('Copy')
    menuitem3 = SimpleButton('Paste')
    menuitem3.set_colors(fg=(128,128,128))  # grey (could indicate "disabled")
    menuitem4 = SimpleButton('Delete')
    menu_A = Menu()
    menu_A.add_widgets(menuitem1, menuitem2, menuitem3, menuitem4)
    menu_A.rect.topleft =(60,0)

    # an 11-item menu, the easy way
    menu = Menu.ActionMenu( 'create node|remove node|move node from|move node to|' +
                            'create arc from|create arc to|edit arc name|' +
                            'edit FSM name|file in|file out|cancel' )

    # a little black 4x4 pixel square, in the upper left corner
    junk = Widget()
    junk.rect = pygame.Rect(0,0, 4,4)
    junk.image = pygame.Surface((4,4))

    # This textbox has a transparent background except while you're editing it
    textbox1 = TextEditBox( 'editable transparent', maxlen=30, width=180,
                            pos=(30,165), Id='textbox1' )

    # This textbox has an light-green opaque background
    textbox2 = TextEditBox( 'editable opaque', maxlen=30, width=180,
                            pos=(30,190), bgcolor=(240,255,240),
                               Id='textbox2' )
    textbox2.set_boxcolors((225,225,225))  # give it a light grey border

    # A Q&A widget sprite, similar to a specialized Form
    qa = InputBox( question='How tall are you (in inches)?', answer='''5'10"''', Id='inches_high' )
    qa.relative_rect.topleft = (100,100)

    # Now we're going to create a form, with a red box around it:
    form = Form( rect=((200,250),(340,200)), bgcolor=(255,240,240), boxcolors=(255,0,0) )
    # Create various widget sprites to go inside the form.  (Positions are relative to the form.)
    form_b1 = Button( '1st button', pos=(20,20), three_D=True )
    form_b1.set_border(6)
    form_b2 = Button( '3nd button', pos=(120,20), three_D=True )
    form_b2.set_border(6)
    form_b3 = Button( '3nd button', pos=(220,20), three_D=True )
    form_b3.set_border(6)
    form_t1 = TextEditBox( 'edit me!', maxlen=30, width=200, pos=(60,50), bgcolor=(230,255,255), Id='textbox_in_form' )
    # Add the widgets to the form
    form.add_widgets(form_b1, form_b2, form_b3, form_t1, qa)

    # # We don't actually need to do an update here, but it fixes the rects so debug prints look right
    # form.update()
    # # Debug prints:
    # print('form=' + repr(form))
    # print('  form_b1=' + repr(form_b1))
    # print('  form_b2=' + repr(form_b2))
    # print('  form_b3=' + repr(form_b3))
    # print('  form_t1=' + repr(form_t1))
    # print('  qa=' + repr(qa))

    # Add all the widgets (except the pop-up menu) to the widget group, so they'll be active
    widget_group.add( button1, button2, button3, junk, textbox1, textbox2, menu_A, form )

    # we'll store mouse position here:
    mx = 0
    my = 0

    keep_running = True
    while keep_running:
        # get next event:
        event = pygame.event.wait()

        # if event.type != MOUSEMOTION:
        #     if event.type == WIDGETEVENT:
        #         print('dbg 6: got event, event.type=' + repr(event.type) + '=' + event_name(event.type) + ', data=' + repr(event.data))
        #     else:
        #         print('dbg 6: got event, event.type=' + repr(event.type) + '=' + event_name(event.type))

        # If event is QUIT (or ESC key) then quit
        if ( (event.type == QUIT) or
             ((event.type == KEYDOWN) and (event.key == K_ESCAPE)) ):
            keep_running = False
            break

        # Give widget sprites a look at the event
        event_handled_by_widget = widget_group.notify(event)
        if event_handled_by_widget:
            continue
            # if widget(s) handled the event, we're probably done with it

        # otherwise, handle it in our application
        if ((event.type == MOUSEBUTTONDOWN) and
              ((event.button == MOUSEBUTTONLEFT) or (event.button == MOUSEBUTTONRIGHT))):
            # left or right mouse button
            mx,my = event.pos  # position of mouse cursor at time of mouse click
            line2_text = repr((mx,my)) + '   button=' + repr(event.button)
            line2 = vera.render( line2_text, True, (0,40,120) )
            if event.button == MOUSEBUTTONLEFT:
                click.play()
            elif event.button == MOUSEBUTTONRIGHT:
                # pop-up menu!
                menu.rect.topleft = (mx,my)
                widget_group.add(menu)
                GUIpygame.changed = True
        elif event.type == MOUSEMOTION:
            mx,my = event.pos  # position of mouse cursor
            line2_text = repr((mx,my))
            line2 = vera.render( line2_text, True, (0,30,100) )
            GUIpygame.changed = True
        elif event.type == KEYDOWN and event.key == K_SPACE:
            cameraclick.play()  # make camera-click sound
            pygame.image.save(screen,"screenshot.jpg")  # extension can be bmp, jpg, png, or tga (but not gif)
            # note: screenshot does not include the mouse cursor
        elif event.type == VIDEORESIZE:
            scrsize = event.size  # or event.w, event.h
            screen = pygame.display.set_mode(scrsize,RESIZABLE)
            GUIpygame.changed = True
        elif event.type == WIDGETEVENT:
            if re.match('^textbox', str(event.id)):
                line3.set_text( 'line3:  ' + event.id + '= "' + event.text + '"', adjustwidth=True )
            else:
                line3.set_text( 'line3:  pressed button=' + repr(event.id), adjustwidth=True )
            # print('dbg 4: line3="' + line3.text +'"')
            # close menu (if it is popped up):
            widget_group.remove(menu)
            GUIpygame.changed = True

        if GUIpygame.changed:
            # Clear, Update, and Draw Everything
            screen.fill( background_color )
            left_x = (scrsize[0]+1-instructions_w)//2
            if left_x < (menu_A.rect.right + 5):
                left_x = (menu_A.rect.right + 5)  # don't overlap the menu
            screen.blit( instructions, (left_x,1) )  # at top-center of screen
            screen.blit( line2, (left_x, 6+instructions_h) )  # right below the instructions
            line3.rect.left = left_x

            for group in (sprite_group, widget_group):
                group.update()
                group.draw(screen)

            pygame.display.update()
            GUIpygame.changed = False

    pygame.quit()
    sys.exit(0)

