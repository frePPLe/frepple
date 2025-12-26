/***************************************************************************
 *                                                                         *
 * Copyright (C) 2014 by frePPLe bv                                        *
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

#include <deque>
#include <thread>

#include "frepple/database.h"

namespace frepple::utils {

DatabaseWriter* DatabaseWriter::instance = nullptr;

string DatabaseWriter::defaultconnectionstring;

void DatabaseReader::assureConnection() {
  if (conn || connectionstring.empty()) return;
  conn = PQconnectdb(connectionstring.c_str());
  if (PQstatus(conn) != CONNECTION_OK) {
    stringstream o;
    o << "Database error: Connection failed: " << PQerrorMessage(conn) << '\n';
    PQfinish(conn);
    conn = nullptr;
    throw RuntimeException(o.str());
  }
  if (!Plan::instance().getTimeZone().empty())
    DatabaseStatement("set time zone '" + Plan::instance().getTimeZone() + "'")
        .execute(conn);
}

DatabaseReader::~DatabaseReader() {
  if (conn) PQfinish(conn);
}

void DatabaseReader::executeSQL(DatabaseStatement& stmt) {
  assureConnection();
  PGresult* res = stmt.execute(conn);
  if (PQresultStatus(res) != PGRES_COMMAND_OK) {
    stringstream o;
    o << "Database error: " << PQerrorMessage(conn)
      << "\n   statement: " << stmt << '\n';
    PQclear(res);
    throw RuntimeException(o.str());
  }
  PQclear(res);
}

DatabaseResult::DatabaseResult(DatabaseReader& db, DatabaseStatement& stmt) {
  res = stmt.execute(db.getConnection());
  if (PQstatus(db.getConnection()) == CONNECTION_BAD) {
    PQclear(res);
    throw DatabaseBadConnection();
  }
  if (PQresultStatus(res) != PGRES_TUPLES_OK) {
    stringstream o;
    o << "Database error: " << db.getError() << "\n   statement: " << stmt
      << '\n';
    PQclear(res);
    throw RuntimeException(o.str());
  }
}

PyObject* runDatabaseThread(PyObject*, PyObject* args, PyObject*) {
  // Pick up arguments
  const char* con = "";
  if (!PyArg_ParseTuple(args, "|s:runDatabaseThread", &con)) return nullptr;

  // Create a new thread
  DatabaseWriter::launch(con);

  // Return. The database writer is now running in a seperate thread from now
  // onwards.
  return Py_BuildValue("");
}

DatabaseWriter::DatabaseWriter(const string& c) : connectionstring(c) {
  // Create a database writer thread
  worker = thread(workerthread, this);
  worker.detach();
}

void DatabaseWriter::pushTransaction(DatabaseTransaction* trns) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(trns);
}

void DatabaseWriter::pushStatement(const string& sql) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(sql));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(sql, arg1));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(sql, arg1, arg2));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(sql, arg1, arg2, arg3));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5, arg6));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(
      sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(
      sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(
      sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10, const string& arg11) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(
      sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10, arg11));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10, const string& arg11,
                                   const string& arg12) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8,
                            arg9, arg10, arg11, arg12));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10, const string& arg11,
                                   const string& arg12, const string& arg13) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8,
                            arg9, arg10, arg11, arg12, arg13));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10, const string& arg11,
                                   const string& arg12, const string& arg13,
                                   const string& arg14) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8,
                            arg9, arg10, arg11, arg12, arg13, arg14));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10, const string& arg11,
                                   const string& arg12, const string& arg13,
                                   const string& arg14, const string& arg15) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(
      new DatabaseStatement(sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8,
                            arg9, arg10, arg11, arg12, arg13, arg14, arg15));
}

void DatabaseWriter::pushStatement(const string& sql, const string& arg1,
                                   const string& arg2, const string& arg3,
                                   const string& arg4, const string& arg5,
                                   const string& arg6, const string& arg7,
                                   const string& arg8, const string& arg9,
                                   const string& arg10, const string& arg11,
                                   const string& arg12, const string& arg13,
                                   const string& arg14, const string& arg15,
                                   const string& arg16) {
  if (!instance) throw LogicException("Database writer not initialized");
  lock_guard<mutex> l(instance->lock);
  instance->statements.push_back(new DatabaseStatement(
      sql, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10, arg11,
      arg12, arg13, arg14, arg15, arg16));
}

void DatabaseWriter::workerthread(DatabaseWriter* writer) {
  logger << "Initialized database writer\n";

  // Endless loop
  PGconn* conn = nullptr;
  Date idle_since = Date::infinitePast;
  while (true) {
    // Sleep for a second   TODO replace with wait for messages
    this_thread::sleep_for(chrono::seconds(1));

    // Loop while we have commands in the queue
    while (true) {
      // Pick up a statement
      // To be reviewed: we remote the statement, regardless whether execution
      // failed or not. We may loose some changes if eg the connection was
      // dropped.
      writer->lock.lock();
      if (writer->statements.empty()) {
        // Queue is empty
        if (conn && Date::now() - idle_since > Duration(600L)) {
          logger << "Closing idle database connection at " << Date::now()
                 << '\n';
          PQfinish(conn);
          conn = nullptr;
        }
        writer->lock.unlock();
        break;
      }
      DatabaseStatementBase* stmt = writer->statements.front();
      writer->statements.pop_front();
      writer->lock.unlock();

      // Connect to the database if we don't have a connection yet
      if (!conn) {
        conn = PQconnectdb(writer->connectionstring.c_str());
        if (PQstatus(conn) != CONNECTION_OK) {
          logger << "Database thread error: Connection failed: "
                 << PQerrorMessage(conn) << '\n';
          PQfinish(conn);
          return;
        }
        if (!Plan::instance().getTimeZone().empty())
          DatabaseStatement("set time zone '" + Plan::instance().getTimeZone() +
                            "'")
              .execute(conn);
        logger << "Opening connection for database writer at " << Date::now()
               << '\n';
      }

      // Execute the statement
      PGresult* res = stmt->execute(conn);
      if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        logger << "Database thread error: statement failed: "
               << PQerrorMessage(conn) << '\n';
        logger << "  Statement: " << stmt << '\n';
        // TODO Catch dropped connections PGRES_FATAL_ERROR and then call
        // PQreset(conn) to reconnect automatically
      }
      delete stmt;
      PQclear(res);
    }  // While queue not empty

    // Record time of last activity
    idle_since = Date::now();
  };  // Infinite loop till program ends

  // Finalize
  if (conn) PQfinish(conn);
  logger << "Finished database writer thread\n";
}

PGresult* DatabaseStatement::execute(PGconn* conn) {
  // Execute a single statement
  const char* paramValues[MAXPARAMS];
  for (int idx = 0; idx < args; ++idx)
    paramValues[idx] = arg[idx].empty() ? nullptr : arg[idx].c_str();
  if (args)
    return PQexecParams(conn, sql.c_str(), args, nullptr, paramValues, nullptr,
                        nullptr, 0);
  else
    return PQexec(conn, sql.c_str());
}

PGresult* DatabaseTransaction::execute(PGconn* conn) {
  // Start a transaction
  PGresult* res = PQexec(conn, "BEGIN TRANSACTION");
  if (PQresultStatus(res) != PGRES_COMMAND_OK) {
    logger << "Database thread error: transaction start failed: "
           << PQerrorMessage(conn) << '\n';
    return res;
  }
  PQclear(res);

  // Execute all statements in the list
  bool rollback = false;
  while (!statements.empty()) {
    // Pick up a statement
    DatabaseStatementBase* stmt = statements.front();
    statements.pop_front();

    // Execute the statement, unless one of the previous statements failed
    if (!rollback) {
      res = stmt->execute(conn);
      if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        // Statement failed.
        // After rollback we'll return the resultstatus object we have
        // at the moment of the failure. Hence no call to PQClear.
        logger << "Database thread error: statement failed: "
               << PQerrorMessage(conn) << '\n';
        logger << "  Statement: " << stmt << '\n';
        rollback = true;
      } else
        PQclear(res);
    }

    // Delete the statement (whether execution failed or not)
    delete stmt;
  }

  // Commit or rollback the complete transaction
  if (rollback) {
    PGresult* res2 = PQexec(conn, "ROLLBACK");
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
      logger << "Database thread error: transaction rollback failed: "
             << PQerrorMessage(conn) << '\n';
      PQclear(res);
      return res2;
    }
  } else {
    PGresult* res2 = PQexec(conn, "COMMIT");
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
      logger << "Database thread error: transaction commit failed: "
             << PQerrorMessage(conn) << '\n';
      PQclear(res);
      return res2;
    }
  }
  return res;
}

}  // namespace frepple::utils
