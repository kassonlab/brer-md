//
// Created by Eric Irrgang on 11/3/17.
//

#include "export_plugin.h"

#include <pybind11/pybind11.h>

// Make a convenient alias to save some typing...
namespace py = pybind11;


template<class T>
class Restraint : public T
{

};

class MyRestraint
{
    public:
        static const char* docstring;
};

// Raw string will have line breaks and indentation as written between the delimiters.
const char* MyRestraint::docstring =
R"rawdelimiter(Some sort of custom potential.
)rawdelimiter";


// The first argument is the name of the module when importing to Python. This should be the same as the name specified
// as the OUTPUT_NAME for the shared object library in the CMakeLists.txt file. The second argument, 'm', can be anything
// but it might as well be short since we use it to refer to aspects of the module we are defining.
PYBIND11_MODULE(myplugin, m) {
    m.doc() = "sample plugin"; // This will be the text of the module's docstring.

    // The template parameters specify the C++ class to export and the handle type.
    // The function parameters specify the containing module and the Python name for the class.
    py::class_<Restraint<MyRestraint>> potential(m, "Potential");
    potential.def(py::init());
    // Set the Python docstring.
    potential.doc() = MyRestraint::docstring;
}
