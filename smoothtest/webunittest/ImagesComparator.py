# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import subprocess
import logging
from smoothtest.base import SmoothTestBase
from PIL import Image
import tempfile
import shutil
import os


class ImagesComparator(SmoothTestBase):
    def exec_cmd(self, cmd):
        logging.debug('Getting output of: %r' % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        assert not p.returncode, 'Command %r failed output: %s err: %s' % (cmd, out, err)
        return out
    
    def create_diff(self, a_file, b_file, diff, crop_threshold):
        if not (0 <= crop_threshold <= 100):
            raise ValueError('crop_threshold outside range: 0 <= crop_threshold <= 100.')
        tempdir = None
        aimg = Image.open(a_file)
        bimg = Image.open(b_file)
        if aimg.size != bimg.size:
            if crop_threshold == 100:
                raise ValueError('crop_threshold is 100 and images are from different sizes.')
            w,h = min((aimg.size[0], bimg.size[0])), min((aimg.size[1], bimg.size[1]))
            wratio = w/float(aimg.size[0])*100
            hratio = h/float(aimg.size[1])*100
            if wratio < crop_threshold or hratio < crop_threshold:
                raise ValueError('Cropping ratios %r are smaller than '
                                 'crop_threshold=%r.' % ((wratio, hratio), crop_threshold))
            tempdir = tempfile.mkdtemp()
            if aimg.size != (w,h):
                a_file = self.crop_image(tempdir, a_file, w, h)
            if bimg.size != (w,h):
                b_file =self.crop_image(tempdir, b_file, w, h)
        self.exec_cmd('compare %s %s %s'%(a_file,b_file,diff))
#        if tempdir:
#            shutil.rmtree(tempdir)

    def crop_image(self, tempdir, img_file, w, h):
        new_file = os.path.join(tempdir, os.path.basename(img_file))
        cmd = 'convert {img_file} -crop {w}x{h}+0+0  +repage {new_file}'.format(**locals())
        self.exec_cmd(cmd)
        return new_file

    def compare(self, a_file, b_file, treshold=100):
        command = 'findimagedupes -t=%s %s %s' % (treshold, a_file, b_file)
        return bool(self.exec_cmd(command))


def smoke_test_module():
    ic = ImagesComparator()
    a_file = 'tests/img/street.jpg' 
    b_file = 'tests/img/street_diff.jpg'
    diff = 'tests/img/diff.jpg'
    assert ic.compare(a_file, b_file, treshold=100) == False
    assert ic.compare(a_file, b_file, treshold=50) == True
    ic.create_diff(a_file, b_file, diff)
    a = '/home/jduo/000-JujuUnencrypted/EclipseProjects/smoothtest/smoothtest/ref/python_search.png'
    b = '/tmp/tmpfAHDpt/python_search.png'
    ic.create_diff(a, b, '/tmp/diff.png', crop_threshold=90)

if __name__ == "__main__":
    smoke_test_module()
