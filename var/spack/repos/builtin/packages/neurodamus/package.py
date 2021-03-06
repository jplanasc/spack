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
from spack.pkg.builtin.neurodamus_base import NeurodamusBase
import os
import shutil
from contextlib import contextmanager


class Neurodamus(NeurodamusBase):

    """Package used for building special from NeurodamusBase package"""

    variant('coreneuron', default=True, description="Enable CoreNEURON Support")
    variant('profile', default=False, description="Enable profiling using Tau")
    variant('syntool', default=True, description="Enable Synapsetool reader")
    variant('python', default=False, description="Enable Python Neurodamus")

    depends_on("boost", when="+syntool")
    depends_on("hdf5")
    depends_on("mpi")
    depends_on("neuron")
    depends_on('reportinglib')
    depends_on("zlib")

    depends_on('coreneuron', when='+coreneuron')
    depends_on('coreneuron+profile', when='+profile')
    depends_on('coreneuron@plasticity', when='@plasicity')

    depends_on('neurodamus-base@master', when='@master')
    depends_on('neurodamus-base@hippocampus', when='@hippocampus')
    depends_on('neurodamus-base@plasticity', when='@plasticity')

    depends_on("neuron+profile", when='+profile')
    depends_on('reportinglib+profile', when='+profile')
    depends_on('synapsetool~shared', when='+syntool')
    depends_on('tau', when='+profile')

    depends_on("python@2.7:",      type=('build', 'run'), when='+python')
    depends_on("py-setuptools",    type=('build', 'run'), when='+python')
    depends_on("py-h5py",          type=('build', 'run'), when='+python')
    depends_on("py-numpy",         type=('build', 'run'), when='+python')
    depends_on('py-enum34',        type=('build', 'run'), when='^python@2.4:2.7.999,3.1:3.3.999')
    depends_on("py-lazy-property", type=('build', 'run'), when='+python')

    # coreneuron support is available for plasticity model
    # and requires python support in neuron
    conflicts('@hippocampus', when='+coreneuron')
    conflicts('@master', when='+coreneuron')
    conflicts('^neuron~python', when='+coreneuron')

    phases = ['build', 'install']

    def do_stage(self, mirror_only=False):
        # We Dont do fetching since it's not required, only stage
        self._fetch_time = 0
        self.stage.create()
        build_dir = os.path.join(self.stage.path, 'build')
        os.makedirs(build_dir)
        os.symlink(self.spec['neurodamus-base'].prefix.lib.modlib, os.path.join(build_dir, 'm'))

    # Synapsetool bring dependency with boost libraries
    # As neurodamus is non-cmake package, it's difficult to find
    # find dependencies easily. Here is custom method that find
    # additional libraries required while linking synapse tool
    def syntool_dep_libs(self):
        spec = self.spec
        ld_flags = spec['synapsetool'].libs.ld_flags
        for lib in ['libboost_system-mt', 'libboost_filesystem-mt']:
            libs = find_libraries(lib, root=spec['boost'].prefix,
                                  shared=False, recursive=True)
            ld_flags += ' %s ' % (libs.ld_flags)
        return ld_flags

    def build(self, spec, prefix):
        """ Build mod files from m dir
        """
        profile_flag = '-DENABLE_TAU_PROFILER' if '+profile' in spec else ''
        include_flag = ''
        link_flag = ''
        env['MAKEFLAGS'] = '-j{0}'.format(make_jobs)

        if '+syntool' in spec:
            include_flag += ' -DENABLE_SYNTOOL -I ' + spec['synapsetool'].prefix.include
            link_flag += self.syntool_dep_libs()

        if '+coreneuron' in spec:
            include_flag += ' -DENABLE_CORENEURON -I%s' % (spec['coreneuron'].prefix.include)
            link_flag += ' %s' % (spec['coreneuron'].libs.ld_flags)

        include_flag += ' -I%s -I%s %s' % (spec['reportinglib'].prefix.include,
                                           spec['hdf5'].prefix.include,
                                           profile_flag)
        link_flag += ' %s -L%s -lhdf5 -L%s -lz' % (
                     spec['reportinglib'].libs.ld_flags,
                     spec['hdf5'].prefix.lib,
                     spec['zlib'].prefix.lib)

        nrnivmodl = which('nrnivmodl')
        with profiling_wrapper_on():
            nrnivmodl('-incflags', include_flag,
                      '-loadflags', link_flag, 'm')
        # special exists or fail
        special = os.path.join(os.path.basename(self.neuron_archdir), 'special')
        assert os.path.isfile(special)

    def install(self, spec, prefix):
        """ Move libs to destination.
            Libs are sym-linked. Compiled libs into libs, special into bin
        """
        neurodamus_base = spec['neurodamus-base'].prefix
        arch = os.path.basename(self.neuron_archdir)
        os.makedirs(prefix.lib.modc)
        os.makedirs(prefix.bin)

        os.symlink(neurodamus_base.lib.hoclib, prefix.lib.hoclib)
        os.symlink(neurodamus_base.lib.modlib, prefix.lib.modlib)

        if os.path.isdir(neurodamus_base.python):
            os.symlink(neurodamus_base.python, prefix.python)

        shutil.move(os.path.join(arch, 'special'), prefix.bin)

        # Copy c mods
        for cmod in find(arch, "*.c", recursive=False):
            shutil.move(cmod, prefix.lib.modc)

        # Handle non-binary special
        if os.path.exists(arch + "/.libs/libnrnmech.so"):
            shutil.move(arch + "/.libs/libnrnmech.so", prefix.lib)
            sed = which('sed')
            sed('-i', 's#-dll .*#-dll %s#' % prefix.lib.join('libnrnmech.so'), prefix.bin.special)

    def setup_environment(self, spack_env, run_env):
        run_env.prepend_path('PATH', self.prefix.bin)
        run_env.set('HOC_LIBRARY_PATH', self.prefix.lib.hoclib)
        if os.path.isdir(self.prefix.python):
            for m in spack_env.env_modifications:
                if m.name == 'PYTHONPATH':
                    run_env.prepend_path('PYTHONPATH', m.value)
            run_env.prepend_path('PYTHONPATH', self.prefix.python)
            run_env.set('NEURODAMUS_PYTHON', self.prefix.python)


@contextmanager
def profiling_wrapper_on():
    os.environ["USE_PROFILER_WRAPPER"] = "1"
    yield
    del os.environ["USE_PROFILER_WRAPPER"]
