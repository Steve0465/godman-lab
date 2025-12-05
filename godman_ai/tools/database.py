"""Database Tool - Query and manipulate databases."""

from typing import Any, Dict, List
import os


class DatabaseTool:
    """Execute database queries and manage data."""
    
    name = "database"
    description = "Query and manipulate SQL databases"
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Perform database operations.
        
        Args:
            action: 'query', 'insert', 'update', 'delete', 'create_table'
            **kwargs: Action-specific parameters
            
        Returns:
            Dict with operation results
        """
        actions = {
            "query": self.query,
            "insert": self.insert,
            "update": self.update,
            "delete": self.delete,
            "create_table": self.create_table
        }
        
        if action in actions:
            return actions[action](**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _get_connection(self, db_type: str = "sqlite", db_path: str = None, **kwargs):
        """Get database connection."""
        if db_type == "sqlite":
            import sqlite3
            db_path = db_path or os.path.expanduser("~/.godman/data.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return sqlite3.connect(db_path)
        elif db_type == "postgres":
            try:
                import psycopg2
            except ImportError:
                raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")
            
            conn_str = os.getenv("POSTGRES_URL") or kwargs.get("connection_string")
            if not conn_str:
                raise ValueError("POSTGRES_URL environment variable or connection_string required")
            return psycopg2.connect(conn_str)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def query(self, sql: str, db_type: str = "sqlite", params: tuple = None, **kwargs) -> Dict[str, Any]:
        """Execute a SELECT query."""
        try:
            conn = self._get_connection(db_type, **kwargs)
            cursor = conn.cursor()
            
            cursor.execute(sql, params or ())
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            results = [dict(zip(columns, row)) for row in rows]
            
            conn.close()
            
            return {
                "success": True,
                "count": len(results),
                "results": results,
                "columns": columns
            }
        except Exception as e:
            return {"error": f"Query failed: {str(e)}", "sql": sql}
    
    def insert(self, table: str, data: Dict[str, Any], db_type: str = "sqlite", **kwargs) -> Dict[str, Any]:
        """Insert a row into a table."""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" if db_type == "sqlite" else "%s"] * len(data))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            conn = self._get_connection(db_type, **kwargs)
            cursor = conn.cursor()
            cursor.execute(sql, tuple(data.values()))
            conn.commit()
            
            row_id = cursor.lastrowid
            conn.close()
            
            return {
                "success": True,
                "table": table,
                "inserted_id": row_id
            }
        except Exception as e:
            return {"error": f"Insert failed: {str(e)}"}
    
    def update(self, table: str, data: Dict[str, Any], where: str, params: tuple = None, db_type: str = "sqlite", **kwargs) -> Dict[str, Any]:
        """Update rows in a table."""
        try:
            set_clause = ", ".join([f"{k} = ?" if db_type == "sqlite" else f"{k} = %s" for k in data.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            
            conn = self._get_connection(db_type, **kwargs)
            cursor = conn.cursor()
            cursor.execute(sql, tuple(data.values()) + (params or ()))
            conn.commit()
            
            rows_affected = cursor.rowcount
            conn.close()
            
            return {
                "success": True,
                "table": table,
                "rows_affected": rows_affected
            }
        except Exception as e:
            return {"error": f"Update failed: {str(e)}"}
    
    def delete(self, table: str, where: str, params: tuple = None, db_type: str = "sqlite", **kwargs) -> Dict[str, Any]:
        """Delete rows from a table."""
        try:
            sql = f"DELETE FROM {table} WHERE {where}"
            
            conn = self._get_connection(db_type, **kwargs)
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            
            rows_affected = cursor.rowcount
            conn.close()
            
            return {
                "success": True,
                "table": table,
                "rows_deleted": rows_affected
            }
        except Exception as e:
            return {"error": f"Delete failed: {str(e)}"}
    
    def create_table(self, table: str, schema: str, db_type: str = "sqlite", **kwargs) -> Dict[str, Any]:
        """Create a new table."""
        try:
            sql = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
            
            conn = self._get_connection(db_type, **kwargs)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "table": table,
                "created": True
            }
        except Exception as e:
            return {"error": f"Create table failed: {str(e)}"}
