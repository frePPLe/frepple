/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/


#ifndef SAMPLE_MODULE_H
#define SAMPLE_MODULE_H
#include "frepple.h"
using namespace frepple;

/** @file sample_module.h
  * @brief Header file for a sample module.
  *
  * @namespace sample_module
  * @brief A sample module.
  *
  * Using a seperate namespace keeps things clean and simple.
  * It keeps the code structured. The auto-generated documentation will also
  * follow the same modular structure as your extension modules.
  */
namespace sample_module
{


/** This is the initialization routine for the extension.
  * Including a function with this prototype is compulsary. If it doesn't
  * exist your module will not be able to be loaded.
  * The function is called automatically when your module is loaded.
  *
  * Parameters can be passed when loading the library.
  *
  * The initialization routine returns a pointer to a constant character
  * buffer with the module name.
  */
MODULE_EXPORT const char* initialize(const Environment::ParameterList& z);


/** @brief Operation type for modeling transportation efficiently.
  *
  * A transport operation has the following characteristics:
  *  - consumes 1 unit from a source buffer
  *  - produces 1 unit into a destination buffer
  *  - takes a fixed duration of time
  */
class OperationTransport : public OperationFixedTime
{
  private:
    /** Buffer at the source location. */
    Buffer* fromBuf;

    /** Buffer at the destination location. */
    Buffer* toBuf;

    static const Keyword tag_frombuffer;
    static const Keyword tag_tobuffer;

  public:
    /** Constructor. */
    explicit OperationTransport() : fromBuf(NULL), toBuf(NULL)
    {
      initType(metadata);
    }

    /** Returns a pointer to the source buffer. */
    Buffer* getFromBuffer() const
    {
      return fromBuf;
    }

    /** Update the source buffer of the transport.<br>
      * If operationplans already exist for the operation the update will
      * fail.
      */
    void setFromBuffer(Buffer *l);

    /** Returns a pointer to the destination buffer. */
    Buffer* getToBuffer() const
    {
      return toBuf;
    }

    /** Update the destination buffer of the transport.<br>
      * If operationplans already exist for the operation the update will
      * fail.
      */
    void setToBuffer(Buffer *l);

    /** Returns a reference to this class' metadata. */
    virtual const MetaClass& getType() const {return *metadata;}

    /** A static metadata object. */
    static const MetaClass *metadata;

    /** This callback will automatically be called when a buffer is deleted. */
    static bool callback(Buffer*, const Signal);

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      OperationFixedTime::registerFields<OperationTransport>(m);
      m->addPointerField<Cls, Buffer>(tag_frombuffer, &Cls::getFromBuffer, &Cls::setFromBuffer);
      m->addPointerField<Cls, Buffer>(tag_tobuffer, &Cls::getToBuffer, &Cls::setToBuffer);
    }
};

} // End namespace

#endif   // endif SAMPLE_MODULE_H
