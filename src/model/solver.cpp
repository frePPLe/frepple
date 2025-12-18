/***************************************************************************
 *                                                                         *
 * Copyright (C) 2009 by frePPLe bv                                        *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include "frepple/model.h"

namespace frepple {

template <class Solver>
Tree utils::HasName<Solver>::st;
const MetaCategory* Solver::metadata;

int Solver::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Solver>(
      "solver", "solvers", MetaCategory::ControllerDefault);
  registerFields<Solver>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<Solver>::getPythonType();
  x.setName("solver");
  x.setDoc("frePPLe solver");
  x.supportgetattro();
  x.supportsetattro();
  x.addMethod("solve", solve, METH_NOARGS, "run the solver");
  metadata->setPythonClass(x);
  return x.typeReady();
}

PyObject* Solver::solve(PyObject* self, PyObject* args) {
  Py_BEGIN_ALLOW_THREADS;
  try {
    static_cast<Solver*>(self)->solve();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

}  // namespace frepple
