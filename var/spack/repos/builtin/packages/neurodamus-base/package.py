##############################################################################
# Copyright (c) 2013-2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Created by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://github.com/spack/spack
# Please also see the NOTICE and LICENSE files for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (as
# published by the Free Software Foundation) version 2.1, February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
from spack import *
import os
import shutil


class NeurodamusBase(Package):
    """Library of channels developed by Blue Brain Project, EPFL"""

    homepage = "ssh://bbpcode.epfl.ch/sim/neurodamus/bbp"
    url      = "ssh://bbpcode.epfl.ch/sim/neurodamus/bbp"

    # Once the testing versions are working we go back to using to original branches
    # version('master',      git=url)
    # version('hippocampus', git=url, branch='sandbox/king/hippocampus')
    # version('plasticity',  git=url, branch='sandbox/king/saveupdate_v6support_mask', preferred=True)

    # Testing versions
    version('master', git=url, branch='sandbox/leite/synapsetool', preferred=True)
    version('hippocampus', git=url, branch='sandbox/leite/hippocampus-syntool')
    version('plasticity', git=url, branch='sandbox/leite/saveupdate_v6support_mask-syntool')

    def install(self, spec, prefix):
        shutil.copytree('lib', '%s/lib' % (prefix), symlinks=False)
