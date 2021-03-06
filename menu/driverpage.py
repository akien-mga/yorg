from itertools import product
from random import shuffle
from panda3d.core import TextureStage, Shader, Texture, PNMImage, TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectEntry import DirectEntry
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGuiGlobals import DISABLED, NORMAL
from yyagl.engine.gui.page import Page, PageGui
from yyagl.engine.gui.imgbtn import ImgBtn
from yyagl.gameobject import GameObject
from yorg.utils import Utils
from .thankspage import ThanksPageGui


frag = '''#version 120
varying vec2 texcoord;
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;

void main() {
    float dist_l = texcoord.x;
    float dist_r = 1 - texcoord.x;
    float dist_u = texcoord.y;
    float dist_b = 1 - texcoord.y;
    float alpha = min(dist_l, min(dist_r, min(dist_u, dist_b))) * 30;
    vec4 pix_a = texture2D(p3d_Texture0, texcoord);
    vec4 pix_b = texture2D(p3d_Texture1, texcoord);
    vec4 tex_col = mix(pix_a, pix_b, pix_b.a);
    gl_FragColor = tex_col * vec4(1, 1, 1, alpha);
}'''


class DriverPageProps(object):

    def __init__(self, player_name, drivers_img, cars_img, cars, drivers):
        self.player_name = player_name
        self.drivers_img = drivers_img
        self.cars_img = cars_img
        self.cars = cars
        self.drivers = drivers


class DriverPageGui(ThanksPageGui):

    def __init__(self, mdt, menu_args, driverpage_props):
        self.props = driverpage_props
        ThanksPageGui.__init__(self, mdt, menu_args)

    def bld_page(self):
        self.skills = [drv[2] for drv in self.props.drivers]
        menu_gui = self.mdt.menu.gui
        menu_args = self.mdt.menu.gui.menu_args
        widgets = [OnscreenText(text=_('Select the driver'), pos=(0, .8),
                                **menu_gui.menu_args.text_args)]
        self.track_path = self.mdt.menu.track
        t_a = self.mdt.menu.gui.menu_args.text_args.copy()
        del t_a['scale']
        name = OnscreenText(_('Write your name:'), pos=(-.1, .6), scale=.06,
                            align=TextNode.A_right, **t_a)
        self.ent = DirectEntry(
            scale=.08, pos=(0, 1, .6), entryFont=menu_args.font, width=12,
            frameColor=menu_args.btn_color,
            initialText=self.props.player_name or _('your name'))
        self.ent.onscreenText['fg'] = menu_args.text_fg
        self.drivers = []
        for row, col in product(range(2), range(4)):
            idx = (col + 1) + row * 4
            widgets += [ImgBtn(
                scale=.24, pos=(-.75 + col * .5, 1, .25 - row * .5),
                frameColor=(0, 0, 0, 0), image=self.props.drivers_img[0] % idx,
                command=self.on_click, extraArgs=[idx],
                **self.mdt.menu.gui.menu_args.imgbtn_args)]
            self.drivers += [widgets[-1]]
            sign = lambda x: '\1green\1+\2' if x > 0 else ''
            psign = lambda x: '+' if x == 0 else sign(x)

            def ppcol(x):
                return '\1green\1%s\2' % x if x > 0 else '\1red\1%s\2' % x
            pcol = lambda x: x if x == 0 else ppcol(x)

            def add_lab(txt, pos_z):
                return OnscreenText(
                    txt + ':', pos=(-.95 + col * .5, pos_z - row * .5),
                    scale=.046, align=TextNode.A_left, **t_a)

            def add_txt(val, pos_z):
                return OnscreenText(
                    '%s%s%%' % (psign(val), pcol(val)),
                    pos=(-.55 + col * .5, pos_z - row * .5), scale=.052,
                    align=TextNode.A_right, **t_a)
            lab_lst = [(_('adherence'), .04), (_('speed'), .16),
                       (_('stability'), .1)]
            widgets += map(lambda lab_def: add_lab(*lab_def), lab_lst)
            txt_lst = [(self.skills[idx - 1][1], .04),
                       (self.skills[idx - 1][0], .16),
                       (self.skills[idx - 1][2], .1)]
            widgets += map(lambda txt_def: add_txt(*txt_def), txt_lst)
        self.img = OnscreenImage(
            self.props.cars_img % self.mdt.car, parent=base.a2dBottomRight,
            pos=(-.38, 1, .38), scale=.32)
        widgets += [self.img, name, self.ent]
        map(self.add_widget, widgets)
        fpath = eng.curr_path + 'yyagl/assets/shaders/filter.vert'
        with open(fpath) as ffilter:
            vert = ffilter.read()
        shader = Shader.make(Shader.SL_GLSL, vert, frag)
        self.img.setShader(shader)
        self.img.setTransparency(True)
        self.t_s = TextureStage('ts')
        self.t_s.setMode(TextureStage.MDecal)
        empty_img = PNMImage(1, 1)
        empty_img.add_alpha()
        empty_img.alpha_fill(0)
        tex = Texture()
        tex.load(empty_img)
        self.img.setTexture(self.t_s, tex)
        ThanksPageGui.bld_page(self)
        self.update_tsk = taskMgr.add(self.update_text, 'update text')
        self.enable_buttons(False)

    def enable_buttons(self, enable):
        for drv in self.drivers:
            drv['state'] = NORMAL if enable else DISABLED
            drv.setShaderInput('enable', 1 if enable else .2)
            # do wdg.enable, wdg.disable

    def update_text(self, task):
        has_name = self.ent.get() != _('your name')
        if has_name and self.ent.get().startswith(_('your name')):
            self.ent.enterText(self.ent.get()[len(_('your name')):])
            self.enable_buttons(True)
        elif self.ent.get() in [_('your name')[:-1], '']:
            self.ent.enterText('')
            self.enable_buttons(False)
        elif self.ent.get() not in [_('your name'), '']:
            self.enable_buttons(True)
        return task.cont  # don't do a task, attach to modifications events

    def on_click(self, i):
        txt_path = self.props.drivers_img[1]
        self.img.setTexture(self.t_s, loader.loadTexture(txt_path % i))
        self.widgets[-1]['state'] = DISABLED
        self.enable_buttons(False)
        taskMgr.remove(self.update_tsk)
        names = Utils().get_thanks(6)
        cars = self.props.cars[:]
        cars.remove(self.mdt.car)
        shuffle(cars)
        drv_idx = range(1, 9)
        drv_idx.remove(i)
        shuffle(drv_idx)
        drivers = [(i, self.ent.get(), self.skills[i - 1], self.mdt.car)]
        drivers += [(drv_idx[j], names[j], self.skills[j - 1], cars[j])
                    for j in range(6)]
        self.mdt.menu.gui.notify('on_driver_selected', self.ent.get(), drivers,
                                 self.mdt.track, self.mdt.car)

    def destroy(self):
        self.img = None
        taskMgr.remove(self.update_tsk)
        PageGui.destroy(self)


class DriverPage(Page):
    gui_cls = DriverPageGui

    def __init__(self, menu_args, track, car, driverpage_props, menu):
        self.track = track
        self.car = car
        self.menu_args = menu_args
        self.menu = menu
        init_lst = [
            [('event', self.event_cls, [self])],
            [('gui', self.gui_cls, [self, self.menu_args, driverpage_props])]]
        GameObject.__init__(self, init_lst)
