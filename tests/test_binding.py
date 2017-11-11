# The myplugin module must be locatable by Python.
# If you configured CMake in the build directory ``/path/to/repo/build`` then,
# assuming you are in ``/path/to/repo``, run the tests with something like
#     PYTHONPATH=./build/src/pythonmodule pytest tests

def test_dependencies():
    import gmx
    assert gmx
    import gmx.core
    # gmx.core.MDModule()
    gmx.core.printName(gmx.core.GmxapiMDModule());

def test_imports():
    import myplugin
    assert myplugin
    import gmx.core
    gmx.core.printName(myplugin.Derived())

def test_add_potential():
    import gmx
    import myplugin
    # gmx.data provides a sample minimal tpr file
    from gmx.data import tpr_filename
    system = gmx.System._from_file(tpr_filename)

    potential = myplugin.Potential()
    system.md.add_potential(potential)
