# Wapiti SVN - A web application vulnerability scanner
# Wapiti Project (http://wapiti.sourceforge.net)
# Copyright (C) 2008 Nicolas Surribas
#
# David del Pozo
# Alberto Pastor
# Informatica Gesfor
# ICT Romulus (http://www.ict-romulus.eu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
from file.auxtext import AuxText

class Attack:
    """
    This class represents an attack, it must be extended
    for any class which implements a new type of attack
    """
    verbose = 0
    color   = 0
    
    reportGen = None
    HTTP      = None
    auxText   = None
    
    CONFIG_DIR_NAME = "config/attacks"
    BASE_DIR = os.path.normpath(os.path.join(os.path.abspath(__file__),'../..'))
    CONFIG_DIR = BASE_DIR+"/"+CONFIG_DIR_NAME
    
    def __init__(self,HTTP,reportGen):
        self.HTTP = HTTP
        self.reportGen = reportGen
        self.auxText = AuxText()

    def setVerbose(self,verbose):
        self.verbose = verbose

    def setColor(self):
        self.color = 1
        
    def loadPayloads(self,fileName):
        return self.auxText.readLines(fileName)
    
    
if __name__ == "__main__":
    print __file__
    print __doc__
    print __name__
    print os.path.normpath(os.path.join(os.path.abspath(__file__),'../..'))
