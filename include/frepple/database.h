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

#ifndef DATABASE_H
#define DATABASE_H

#ifdef POSTGRESQL_LIBPQ_FE_H
#include <postgresql/libpq-fe.h>
#else
#include <libpq-fe.h>
#endif

#include "frepple.h"

using namespace frepple;

namespace frepple {
namespace utils {

class DatabaseReader;

/* This Python function runs a thread to persist data into a PostgreSQL
 * database. */
PyObject* runDatabaseThread(PyObject*, PyObject*, PyObject*);

/* An abstract class that has 3 implementations:
 * - DatabaseStatement: runs a single statement in autocommit mode.
 * - DatabaseTransaction: runs a series of DatabaseStatement in a
 *   single database transaction.
 * - DatabasePreparedStatement: creates a prepared statement that
 *   can execute the same SQL statement many times
 */
class DatabaseStatementBase {
 public:
  /* Execute the statement on a database connection. */
  virtual PGresult* execute(PGconn*) {
    throw LogicException("DatabaseStatementBase is an abstract base class");
  };

  /* Virtual destructor. */
  virtual ~DatabaseStatementBase() {}
};

/* A simple wrapper around an SQL statement with arguments.
 *
 * TODO: make this class more lightweight to copy and create?
 * TODO: more flexible argument type handling?
 */
class DatabaseStatement : public DatabaseStatementBase {
  friend ostream& operator<<(ostream&, const DatabaseStatement&);

 public:
  /* Constructor. */
  DatabaseStatement(const string& s) : sql(s), args(0) {};

  DatabaseStatement(const string& s, const string& a1) : sql(s), args(1) {
    arg[0] = a1;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2)
      : sql(s), args(2) {
    arg[0] = a1;
    arg[1] = a2;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3)
      : sql(s), args(3) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4)
      : sql(s), args(4) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
  }

  DatabaseStatement(const string& s, const string& a1, string a2,
                    const string& a3, const string& a4, const string& a5)
      : sql(s), args(5) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6)
      : sql(s), args(6) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7)
      : sql(s), args(7) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8)
      : sql(s), args(8) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9)
      : sql(s), args(9) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10)
      : sql(s), args(10) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10, const string& a11)
      : sql(s), args(11) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
    arg[10] = a11;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10, const string& a11,
                    const string& a12)
      : sql(s), args(12) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
    arg[10] = a11;
    arg[11] = a12;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10, const string& a11,
                    const string& a12, const string& a13)
      : sql(s), args(13) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
    arg[10] = a11;
    arg[11] = a12;
    arg[12] = a13;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10, const string& a11,
                    const string& a12, const string& a13, const string& a14)
      : sql(s), args(14) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
    arg[10] = a11;
    arg[11] = a12;
    arg[12] = a13;
    arg[13] = a14;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10, const string& a11,
                    const string& a12, const string& a13, const string& a14,
                    const string& a15)
      : sql(s), args(15) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
    arg[10] = a11;
    arg[11] = a12;
    arg[12] = a13;
    arg[13] = a14;
    arg[14] = a15;
  }

  DatabaseStatement(const string& s, const string& a1, const string& a2,
                    const string& a3, const string& a4, const string& a5,
                    const string& a6, const string& a7, const string& a8,
                    const string& a9, const string& a10, const string& a11,
                    const string& a12, const string& a13, const string& a14,
                    const string& a15, const string& a16)
      : sql(s), args(16) {
    arg[0] = a1;
    arg[1] = a2;
    arg[2] = a3;
    arg[3] = a4;
    arg[4] = a5;
    arg[5] = a6;
    arg[6] = a7;
    arg[7] = a8;
    arg[8] = a9;
    arg[9] = a10;
    arg[10] = a11;
    arg[11] = a12;
    arg[12] = a13;
    arg[13] = a14;
    arg[14] = a15;
    arg[15] = a16;
  }

  /* Execute the statement on a database connection. */
  virtual PGresult* execute(PGconn*);

 private:
  static const short MAXPARAMS = 16;
  string sql;
  short int args;
  string arg[MAXPARAMS];
};

/* Wrapper around a series of SQL statements that will be executed
 * in a single database transaction.
 */
class DatabaseTransaction : public DatabaseStatementBase {
 private:
  /* Queue of statements to be run in an single transaction. */
  deque<DatabaseStatementBase*> statements;

 public:
  /* Constructor. */
  DatabaseTransaction() {};

  /* Add a statement to the list. */
  void pushStatement(DatabaseStatementBase* p) { statements.push_back(p); }

  /* Execute the statement on a database connection. */
  virtual PGresult* execute(PGconn* conn);
};

inline ostream& operator<<(ostream& os, const DatabaseStatement& stmt) {
  os << stmt.sql;
  if (stmt.args > 0) {
    for (int i = 0; i < stmt.args; ++i) {
      if (i)
        os << ", " << stmt.arg[i];
      else
        os << " with arguments " << stmt.arg[i];
    }
  }
  return os;
}

/* This class implements a database connection to execute
 * SQL statements on the database.
 *
 * The connection should only be used by one thread at a time.
 */
class DatabaseReader : public NonCopyable {
 public:
  DatabaseReader(const string& c) : connectionstring(c) {}

  ~DatabaseReader();

  DatabaseReader(DatabaseReader&& o) noexcept {
    connectionstring = o.connectionstring;
    conn = o.conn;
    o.conn = nullptr;
  }

  DatabaseReader& operator=(DatabaseReader&& o) noexcept {
    if (this != &o) {
      connectionstring = o.connectionstring;
      if (conn) PQfinish(conn);
      conn = o.conn;
      o.conn = nullptr;
    }
    return *this;
  };

  /* Execute a command query that doesn't return a result. */
  void executeSQL(DatabaseStatement&);

  /* Return the error string of the connection. */
  string getError() { return conn ? PQerrorMessage(conn) : ""; }

  void closeConnection() {
    if (!conn) return;
    PQfinish(conn);
    conn = nullptr;
  }

  /* Return the database connection. TODO keep the connection internal to the
   * class... */
  PGconn* getConnection() {
    assureConnection();
    return conn;
  }

 private:
  void assureConnection();

  /* Connection arguments. */
  string connectionstring;

  /* Pointer to the connection. */
  PGconn* conn = nullptr;
};

class DatabasePreparedStatement : public DatabaseStatementBase {
  friend ostream& operator<<(ostream&, const DatabasePreparedStatement&);

 public:
  DatabasePreparedStatement() {};

  DatabasePreparedStatement(DatabaseReader& db, const string& stmtName,
                            const string& sql, int argcount = 0)
      : name(stmtName), args(argcount) {
    if (args < 0) args = 0;
    if (args > 1000)
      throw DataException("Prepared statements are limited to 1000 arguments");
    if (args) arg.resize(args);
    PGresult* res =
        PQprepare(db.getConnection(), name.c_str(), sql.c_str(), args, nullptr);
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
      auto msg = db.getError();
      PQclear(res);
      throw RuntimeException("Can't compile prepared statement: " + msg);
    }
    PQclear(res);
  }

  int getArgs() const { return args; }

  /* Execute the statement on a database connection. */
  virtual PGresult* execute(PGconn* conn) {
    if (!args)
      return PQexecPrepared(conn, name.c_str(), 0, nullptr, nullptr, nullptr,
                            0);
    else {
      const char* paramValues[args];
      for (int idx = 0; idx < args; ++idx)
        paramValues[idx] = arg[idx].empty() ? nullptr : arg[idx].c_str();
      return PQexecPrepared(conn, name.c_str(), args, paramValues, nullptr,
                            nullptr, 0);
    }
  }

  void setArgument(short int i, const string& s) {
    if (i < 0 || i >= args)
      throw RuntimeException("Setting invalid argument of prepared statement");
    arg[i] = s;
  }

 private:
  string name;
  int args = 0;
  vector<string> arg;
};

inline ostream& operator<<(ostream& os, const DatabasePreparedStatement& stmt) {
  os << stmt.name;
  if (stmt.args > 0) {
    for (int i = 0; i < stmt.args; ++i) {
      if (i)
        os << ", " << stmt.arg[i];
      else
        os << " with arguments " << stmt.arg[i];
    }
  }
  return os;
}

class DatabaseBadConnection : public RuntimeException {
 public:
  DatabaseBadConnection() : RuntimeException("Bad database connection") {}
};

/* A wrapper around the PGresult class to avoid memory leaks. */
class DatabaseResult : public NonCopyable {
 public:
  /* Constructor. */
  DatabaseResult(PGresult* r) : res(r) {}

  /* Constructor which runs a SQL statement. */
  DatabaseResult(DatabaseReader& db, DatabaseStatement& stmt);

  /* Constructor which runs a prepared statement. */
  DatabaseResult(DatabaseReader& db, DatabasePreparedStatement& stmt) {
    res = stmt.execute(db.getConnection());
    if (PQstatus(db.getConnection()) == CONNECTION_BAD) {
      PQclear(res);
      throw DatabaseBadConnection();
    }
    if (PQresultStatus(res) != PGRES_TUPLES_OK &&
        PQresultStatus(res) != PGRES_COMMAND_OK) {
      stringstream o;
      o << "Database error: " << db.getError() << endl
        << "   statement: " << stmt << endl;
      PQclear(res);
      throw RuntimeException(o.str());
    }
  }

  /* Destructor. */
  ~DatabaseResult() { PQclear(res); }

  /* Count the rows. */
  int countRows() const { return PQntuples(res); }

  /* Count the fields. */
  int countFields() const { return PQnfields(res); }

  /* Get a field name. */
  string getFieldName(int i) { return PQfname(res, i); }

  /* Get a field value converted to a date. */
  Date getValueDate(int i, int j) const {
    return Date(PQgetvalue(res, i, j), "%Y-%m-%d %H:%M:%S");
  }

  /* Get a field value converted to a string. */
  string getValueString(int i, int j) const { return PQgetvalue(res, i, j); }

  /* Get a field value converted to a double. */
  double getValueDouble(int i, int j) const {
    return atof(PQgetvalue(res, i, j));
  }

  pair<double, bool> getValueDoubleOrNull(int i, int j) const {
    return PQgetisnull(res, i, j)
               ? make_pair<double, bool>(0.0, true)
               : make_pair<double, bool>(atof(PQgetvalue(res, i, j)), false);
  }

  /* Get a field value converted to an integer. */
  int getValueInt(int i, int j) const { return atoi(PQgetvalue(res, i, j)); }

  /* Get a field value converted to a long. */
  long getValueLong(int i, int j) const { return atol(PQgetvalue(res, i, j)); }

  /* Get a field value converted to a bool. */
  bool getValueBool(int i, int j) const {
    const char* r = PQgetvalue(res, i, j);
    if (!r || !r[0] || r[0] == 'f' || r[0] == 'F' || r[0] == '0')
      return false;
    else
      return true;
  }

 private:
  PGresult* res;
};

/* This class implements a queue that is writing results
 * asynchroneously into a PostgreSQL database.
 */
class DatabaseWriter : public NonCopyable {
 public:
  /* Push a series of statements to the queue. They will be executed
   * in a single transaction.
   * The ownership of the DatabaseTransaction is taken over by the
   * writer, which will delete it after the execution.
   */
  static void pushTransaction(DatabaseTransaction*);

  /* Add a new statement to the queue. */
  static void pushStatement(const string&);
  static void pushStatement(const string&, const string&);
  static void pushStatement(const string&, const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&);
  static void pushStatement(const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&, const string&,
                            const string&, const string&);

  /* Method to launch a singleton database writer.
   * An exception is thrown if the writer is already launched.
   */
  static void launch(const string& c = defaultconnectionstring) {
    if (instance) throw RuntimeException("Database writer already running");
    instance = new DatabaseWriter(c);
  }

  static void setConnectionString(const string& c) {
    defaultconnectionstring = c;
  }

  static string getConnectionString() { return defaultconnectionstring; }

 private:
  /* Constructor. */
  DatabaseWriter(const string& con = defaultconnectionstring);

  /* This method runs in a separate thread to execute all statements. */
  static void workerthread(DatabaseWriter*);

  /* Queue of statements. */
  deque<DatabaseStatementBase*> statements;

  /* Lock to assure the queue is manipulated only from a single thread. */
  mutex lock;

  /* Default database connection string. */
  static string defaultconnectionstring;

  /* Database connection string. */
  string connectionstring;

  /* Singleton instance of this class. */
  static DatabaseWriter* instance;

  thread worker;
};

}  // namespace utils
}  // namespace frepple

#endif
