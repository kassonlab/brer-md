# The myplugin module must be locatable by Python.
# If you configured CMake in the build directory ``/path/to/repo/build`` then,
# assuming you are in ``/path/to/repo``, run the tests with something like
#     PYTHONPATH=./cmake-build-debug/src/pythonmodule mpiexec -n 2 python -m mpi4py -m pytest tests/

# This test is not currently run automatically in any way. Build the module, point your PYTHONPATH at it,
# and run pytest in the tests directory.

import pytest

def test_dependencies():
    import gmx
    assert gmx
    import gmx.core
    # holder = gmx.core.get_holder()
    # gmx.core.get_name();

def test_imports():
    import myplugin
    assert myplugin
    import gmx.core

@pytest.mark.usefixtures("cleandir")
def test_add_potential():
    import gmx
    import myplugin
    import pytest
    # gmx.data provides a sample minimal tpr file
    from gmx.data import tpr_filename
    system = gmx.System._from_file(tpr_filename)
    potential = myplugin.MyRestraint()
    generic_object = object()
    with pytest.raises(Exception) as exc_info:
        potential.bind(generic_object)
    assert str(exc_info).endswith("bind method requires a python capsule as input")

    system.add_mdmodule(potential)
    with gmx.context.DefaultContext(system.workflow) as session:
        session.run()

@pytest.mark.usefixtures("cleandir")
def test_plugin_potential():
    import gmx
    import os
    import myplugin

    cwd = os.path.dirname(__file__)
    water = os.path.join(cwd, 'data', 'water.gro')
    import shutil
    shutil.copy(water, './')

    try:
        # use GromacsWrapper if available
        import gromacs
        import gromacs.formats
        from gromacs.tools import Solvate as solvate
        solvate(o='water.gro', box=[5,5,5])
        mdpparams = [('integrator', 'md'),
                     ('nsteps', 1000),
                     ('nstxout', 100),
                     ('nstvout', 100),
                     ('nstfout', 100),
                     ('tcoupl', 'v-rescale'),
                     ('tc-grps', 'System'),
                     ('tau-t', 1),
                     ('ref-t', 298)]
        mdp = gromacs.formats.MDP()
        for param, value in mdpparams:
            mdp[param] = value
        mdp.write('water.mdp')
        with open('input.top', 'w') as fh:
            fh.write("""#include "gromos43a1.ff/forcefield.itp"
#include "gromos43a1.ff/spc.itp"

[ system ]
; Name
spc

[ molecules ]
; Compound  #mols
SOL         4055
""")
        gromacs.grompp(f='water.mdp', c='water.gro', po='water.mdp', pp='water.top', o='water.tpr', p='input.top')
        tpr_filename = os.path.abspath('water.tpr')
    except:
        from gmx.data import tpr_filename
    print("Testing plugin potential with input file {}".format(os.path.abspath(tpr_filename)))

    # Low level API
    system = gmx.System._from_file(tpr_filename)
    potential = myplugin.HarmonicRestraint()
    potential.set_params(1, 4, 2.0, 10000.0)

    system.add_mdmodule(potential)
    with gmx.context.DefaultContext(system.workflow) as session:
        session.run()

    # gmx 0.0.4
    assert gmx.__version__ == '0.0.4'
    md = gmx.workflow.from_tpr(tpr_filename)

    context = gmx.context.ParallelArrayContext(md)
    with context as session:
        if context.rank == 0:
            print(context.work)
        session.run()

    # Create a WorkElement for the potential
    #potential = gmx.core.TestModule()
    potential_element = gmx.workflow.WorkElement(namespace="myplugin",
                                                 operation="create_restraint",
                                                 params=[1, 4, 2.0, 10000.0])
    # Note that we could flexibly capture accessor methods as workflow elements, too. Maybe we can
    # hide the extra Python bindings by letting myplugin.HarmonicRestraint automatically convert
    # to a WorkElement when add_dependency is called on it.
    potential_element.name = "harmonic_restraint"
    before = md.workspec.elements[md.name]
    md.add_dependency(potential_element)
    assert potential_element.name in md.workspec.elements
    assert potential_element.workspec is md.workspec
    after = md.workspec.elements[md.name]
    assert not before is after

    # Context will need to do these in __enter__
    # potential = myplugin.HarmonicRestraint()
    # potential.set_params(1, 4, 2.0, 10000.0)

    context = gmx.context.ParallelArrayContext(md)
    with context as session:
        if context.rank == 0:
            print(context.work)
        session.run()


